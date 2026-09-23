"""Adversarial checks for archive semantics, rolling cutoffs and output boundaries."""
import json
import unittest
import numpy as np
import pandas as pd
from src.input_data import ROOT, load_config
from src.timeline import build_schedule
from src.weather_quality import quality_checks
from src.weather_evaluation import add_provider_performance, rolling_stats
from src.weather_ensemble import add_ensembles, circular_average, performance_weights
from src.validation import validate_point_in_time_integrity, validate_feature_columns, estimated_run_availability


def fixture():
    config = load_config()
    config.update(training_target_start="2025-01-01T00:00:00", train_end="2025-01-04T23:59:59",
                  competition_start="2025-01-05T00:00:00", competition_end="2025-01-06T23:59:59", rolling_min_samples=1)
    frame = build_schedule(config, {"selected_offset_hours": 0})
    frame["turbine_id"] = "turbine_1"
    frame["weather_configuration"] = "synthetic-test"
    frame["weather_archive_method"] = "open_meteo_previous_runs"
    frame["weather_archive_confidence"] = "fixed_lead_time_archive"
    frame["methodology_status"] = "lead_time_archive"
    values = {"wind_speed_10m": 5, "wind_speed_100m": 8, "wind_direction_10m": 359,
              "wind_direction_100m": 1, "temperature_2m": 10, "surface_pressure": 900,
              "relative_humidity_2m": 50, "wind_gusts_10m": 12}
    for i, model in enumerate(config["weather_models"]):
        for variable, value in values.items():
            frame[f"{model}_{variable}"] = float(value + i)
        frame[f"{model}_api_error"] = False
        frame[f"{model}_missing_target_hour"] = False
    frame = quality_checks(frame, config)
    frame["eval_actual_wind_speed"] = 7.0
    frame["eval_actual_temperature"] = 9.0
    frame["normalized_active_power"] = 0.5
    frame["scada_hour_complete"] = True
    frame["observation_available_time"] = frame.target_time + pd.Timedelta(hours=2)
    return config, frame


class LeakageTests(unittest.TestCase):
    def test_target_after_issue_time(self):
        config, frame = fixture()
        validate_point_in_time_integrity(frame, config)
        frame.loc[0, "target_time"] = frame.loc[0, "forecast_issue_time"]
        with self.assertRaisesRegex(ValueError, "Target must"):
            validate_point_in_time_integrity(frame, config)

    def test_no_future_weather_actual_in_features(self):
        for column in ["eval_actual_wind_speed", "eval_actual_temperature", "normalized_active_power", "scada_hour_complete", "observation_available_time"]:
            with self.subTest(column=column), self.assertRaises(ValueError):
                validate_feature_columns(["lead_hours", column])

    def test_provider_run_not_after_issue_time(self):
        config, frame = fixture()
        frame.loc[0, "gfs_run_time"] = frame.loc[0, "forecast_issue_time"] + pd.Timedelta(hours=1)
        with self.assertRaisesRegex(ValueError, "Provider run after"):
            validate_point_in_time_integrity(frame, config)

    def test_dissemination_delay_is_enforced(self):
        config, frame = fixture()
        issue = frame.loc[0, "forecast_issue_time"]
        run = issue - pd.Timedelta(hours=6)
        frame.loc[0, "gfs_run_time"] = run
        frame.loc[0, "gfs_estimated_availability_time"] = estimated_run_availability(run, "gfs", config)
        with self.assertRaisesRegex(ValueError, "not disseminated"):
            validate_point_in_time_integrity(frame, config)

    def test_rolling_metrics_use_only_past_errors(self):
        config, frame = fixture()
        cutoff = pd.Timestamp("2025-01-03T00:00:00Z")
        original = add_provider_performance(frame, config)
        mutation = frame.copy()
        future = mutation.observation_available_time >= cutoff
        mutation.loc[future, "eval_actual_wind_speed"] = 999999.0
        mutation.loc[future, "eval_actual_temperature"] = -999999.0
        changed = add_provider_performance(mutation, config)
        columns = [c for c in original if any(f"_{m}_" in c for m in ["mae", "rmse", "bias", "n"]) or "history_latest" in c]
        before = original.forecast_issue_time <= cutoff
        pd.testing.assert_frame_equal(original.loc[before, columns], changed.loc[before, columns])
        self.assertTrue(original.loc[before, "ecmwf_wind_mae_7d"].notna().any())
        validate_point_in_time_integrity(original, config)

    def test_observation_available_exactly_at_issue_is_excluded(self):
        times = pd.Series(pd.to_datetime(["2025-01-01T00:00Z", "2025-01-02T00:00Z"]))
        stats = rolling_stats(times, np.array([2., 1000.]), pd.to_datetime(["2025-01-02T00:00Z"]), 7, 1)
        self.assertEqual(stats["n"][0], 1)
        self.assertEqual(stats["mae"][0], 2)

    def test_no_future_backfill(self):
        times = pd.Series(pd.to_datetime(["2025-01-03T00:00Z"]))
        stats = rolling_stats(times, np.array([4.]), pd.to_datetime(["2025-01-01T00:00Z", "2025-01-04T00:00Z"]), 7, 1)
        self.assertTrue(np.isnan(stats["mae"][0]))
        self.assertEqual(stats["mae"][1], 4)
        config, frame = fixture()
        for model in config["weather_models"]:
            frame.loc[0, f"{model}_wind_speed_100m"] = np.nan
            frame.loc[0, f"{model}_wind_speed_100m_valid"] = False
        result = add_ensembles(add_provider_performance(frame, config), config)
        self.assertTrue(pd.isna(result.loc[0, "ensemble_wind_speed_100m"]))
        self.assertTrue(pd.isna(result.loc[0, "wind_speed_100m_mean"]))

    def test_train_test_boundary(self):
        config, frame = fixture()
        validate_point_in_time_integrity(frame, config)
        competition_index = frame.index[frame.dataset_split == "competition_test"][0]
        frame.loc[competition_index, "dataset_split"] = "train"
        with self.assertRaisesRegex(ValueError, "boundary"):
            validate_point_in_time_integrity(frame, config)

    def test_unique_primary_key(self):
        config, frame = fixture()
        frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "Duplicate primary"):
            validate_point_in_time_integrity(frame, config)

    def test_fixed_lead_archive_is_accepted_without_exact_publication(self):
        config, frame = fixture()
        result = validate_point_in_time_integrity(frame, config)
        self.assertFalse(result["exact_publication_timestamps_verified"])
        frame.loc[frame.archive_day == 2, "archive_nominal_lead_hours"] = 24
        with self.assertRaisesRegex(ValueError, "nominal"):
            validate_point_in_time_integrity(frame, config)

    def test_competition_actuals_never_change_features_or_weights(self):
        config, frame = fixture()
        first = add_ensembles(add_provider_performance(frame, config), config)
        frame.loc[frame.dataset_split == "competition_test", ["eval_actual_wind_speed", "eval_actual_temperature", "normalized_active_power"]] = 1000000.
        second = add_ensembles(add_provider_performance(frame, config), config)
        columns = [c for c in first if c not in ["eval_actual_wind_speed", "eval_actual_temperature", "normalized_active_power"]]
        pd.testing.assert_frame_equal(first[columns], second[columns])

    def test_circular_mean_handles_wrap_and_opposing_directions(self):
        direction, dispersion = circular_average([[359, 1], [90, 270]], [[1, 1], [1, 1]])
        self.assertLess(min(abs(direction[0]), abs(direction[0] - 360)), 1e-7)
        self.assertTrue(np.isnan(direction[1]))
        self.assertAlmostEqual(dispersion[1], 1.0)

    def test_weights_missing_history_and_missing_models(self):
        weights, fallback = performance_weights([[True, True, False], [True, False, False], [False, False, False]],
                                                [[1, np.nan, 0.1], [1, 2, 3], [1, 2, 3]], 0.05)
        np.testing.assert_allclose(weights, [[.5, .5, 0], [1, 0, 0], [0, 0, 0]])
        self.assertTrue(fallback[0])

    def test_provider_outage_keeps_rows_and_uses_other_models(self):
        config, frame = fixture()
        for v in config["weather_variables"]:
            frame[f"ecmwf_{v}"] = np.nan
        frame["ecmwf_api_error"] = True
        quality = quality_checks(frame, config)
        self.assertEqual(len(quality), len(frame))
        self.assertTrue((quality.weather_models_usable_count == 2).all())
        result = add_ensembles(add_provider_performance(quality, config), config)
        self.assertTrue((result.ecmwf_weight == 0).all())
        self.assertTrue(result.ensemble_wind_speed_100m.notna().all())

    def test_configurable_run_hour(self):
        config, _ = fixture()
        config["forecast_run_hour"] = 12
        schedule = build_schedule(config, {"selected_offset_hours": 0})
        self.assertTrue((schedule.forecast_issue_time.dt.hour == 12).all())
        self.assertEqual(set(schedule.lead_hours), set(range(1, 49)))


class ExportIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "data/final/feature_columns.json"
        if not path.exists():
            raise unittest.SkipTest("Run dataset_builder first for export integration checks")
        cls.schema = json.loads(path.read_text(encoding="utf-8"))

    def test_final_parquet_exports(self):
        train = pd.read_parquet(ROOT / "data/final/training_dataset.parquet")
        competition = pd.read_parquet(ROOT / "data/final/competition_features.parquet")
        offline = pd.read_parquet(ROOT / "data/final/offline_test_with_targets.parquet")
        self.assertGreater(len(train), 0)
        self.assertEqual(len(competition), 2688)
        self.assertEqual(len(offline), len(competition))
        self.assertTrue(train.normalized_active_power.notna().all())
        for column in ["normalized_active_power", "eval_actual_wind_speed", "eval_actual_temperature", "observation_available_time", "scada_samples", "scada_hour_complete"]:
            self.assertNotIn(column, competition.columns)
        self.assertTrue(set(self.schema["features"]).issubset(train.columns))
        self.assertTrue(set(self.schema["features"]).issubset(competition.columns))
        config = load_config()
        validate_point_in_time_integrity(train, config, self.schema["features"])
        validate_point_in_time_integrity(competition, config, self.schema["features"])
        self.assertTrue((competition.weather_models_usable_count > 0).all())


if __name__ == "__main__":
    unittest.main()
