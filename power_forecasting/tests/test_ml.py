"""ML safety tests: splits, transformations, history isolation and delivered artifacts."""
import json
import unittest

import numpy as np
import pandas as pd

from src.input_data import load_config
from src.ml_data import ROOT, TARGET, KEYS, read_inputs, make_folds, add_ml_transforms, frozen_history_view, sha256
from src.ml_models import encode_fit, encode_transform, inner_split, metric_values, fit_learner, predict_learner
from src.ml_experiments import choose_simple, historical_baseline, persistence_baseline


class MLSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train, cls.comp, cls.manifest = read_inputs()
        cls.config = json.loads((ROOT / "ml_config.json").read_text(encoding="utf-8"))
        cls.folds = make_folds(cls.train, cls.config)

    def test_target_range_on_input(self):
        self.assertTrue(self.train[TARGET].between(0, 1).all())
        self.assertNotIn(TARGET, self.comp)

    def test_four_chronological_folds_no_duplicate_target_overlap(self):
        self.assertEqual(len(self.folds), 4)
        for fold in self.folds:
            fit, valid = self.train.loc[fold["train"]], self.train.loc[fold["valid"]]
            self.assertLess(fit.target_time.max(), valid.target_time.min())
            self.assertFalse(set(fit.target_time) & set(valid.target_time))

    def test_training_labels_available_before_first_validation_issue(self):
        for fold in self.folds:
            available = self.train.loc[fold["train"], "target_time"] + pd.Timedelta(hours=2)
            self.assertTrue((available < fold["first_issue"]).all())

    def test_inner_stopping_window_is_chronological_and_purged(self):
        fit, tail = inner_split(self.train.loc[self.folds[0]["train"]], self.config)
        self.assertLess(fit.target_time.max(), tail.target_time.min())
        self.assertTrue(((fit.target_time + pd.Timedelta(hours=2)) < tail.forecast_issue_time.min()).all())

    def test_training_only_categories_and_unknown_category(self):
        train = pd.DataFrame({"turbine_id": ["a", "a"], "wind": [1., np.nan]})
        x, schema = encode_fit(train, ["turbine_id", "wind"], "LightGBM", ["turbine_id"])
        query = pd.DataFrame({"turbine_id": ["b"], "wind": [100.]})
        encoded, unseen = encode_transform(query, schema)
        self.assertEqual(schema["categories"]["turbine_id"], ["a"])
        self.assertEqual(unseen["turbine_id"], 1)
        self.assertEqual(encoded.turbine_id__cat_0.iloc[0], 0)
        self.assertTrue(np.isnan(x.wind.iloc[1]))

    def test_missing_feature_fails_and_order_stable(self):
        frame = pd.DataFrame({"a": [1.], "b": [2.]})
        _, schema = encode_fit(frame, ["b", "a"], "XGBoost", [])
        out, _ = encode_transform(frame, schema)
        self.assertEqual(list(out), ["b", "a"])
        with self.assertRaises(ValueError):
            encode_transform(frame.drop(columns="a"), schema)

    def test_invalid_weather_masked_without_backfill(self):
        frame = pd.DataFrame({"wind": [99., 3., np.nan], "wind_valid": [False, True, False]})
        x, _ = encode_fit(frame, ["wind"], "LightGBM", [])
        self.assertTrue(np.isnan(x.wind.iloc[0]))
        self.assertEqual(x.wind.iloc[1], 3.)
        self.assertTrue(np.isnan(x.wind.iloc[2]))

    def test_feature_groups_compact_and_weather_source_isolated(self):
        groups = json.loads((ROOT / "models/feature_groups.json").read_text(encoding="utf-8"))
        self.assertLessEqual(len(groups["CORE"]), 25)
        self.assertLessEqual(len(groups["Full"]), 35)
        for provider in ["ECMWF", "GFS", "ICON"]:
            for col in groups[provider]:
                self.assertFalse(any(col.startswith(other.lower() + "_") for other in ["ECMWF", "GFS", "ICON"] if other != provider))
        for cols in groups.values():
            self.assertEqual(len(cols), len(set(cols)))
            self.assertFalse(any(c == TARGET or c.startswith("eval_") or c in ["target_time", "forecast_issue_time", "dataset_split"] for c in cols))

    def test_validation_future_weather_actuals_cannot_change_features(self):
        fold = self.folds[0]
        source = pd.read_parquet(ROOT / "data/final/training_weather_dataset.parquet")
        source = source[(source.target_time >= fold["history_target_cutoff"] - pd.Timedelta(days=100)) &
                        (source.target_time < fold["history_target_cutoff"] + pd.Timedelta(days=7))].reset_index(drop=True)
        query = self.train.loc[fold["valid"]].groupby(["turbine_id", "horizon_bucket"]).head(2)
        before = frozen_history_view(query, source, fold["history_target_cutoff"], load_config())
        mutated = source.copy()
        after_cutoff = mutated.target_time >= fold["history_target_cutoff"]
        for col in ["eval_actual_wind_speed", "eval_actual_temperature", TARGET]:
            mutated.loc[after_cutoff, col] = 99999.
        after = frozen_history_view(query, mutated, fold["history_target_cutoff"], load_config())
        pd.testing.assert_frame_equal(before, after)

    def test_duplicate_horizon_does_not_reweight_baseline(self):
        fold = self.folds[0]
        fit = self.train.loc[fold["train"]]
        query = self.train.loc[fold["valid"]].head(20)
        a = historical_baseline(fit, query, "HistoricalMean")
        b = historical_baseline(pd.concat([fit, fit[fit.horizon_bucket == "D1"]]), query, "HistoricalMean")
        np.testing.assert_allclose(a, b)

    def test_metric_formulas_and_sign(self):
        values = metric_values([0, 1], [.2, .8])
        self.assertAlmostEqual(values["MAE"], .2)
        self.assertAlmostEqual(values["RMSE"], .2)
        self.assertAlmostEqual(values["nMAE_pct"], 20)
        self.assertAlmostEqual(values["Bias"], 0)

    def test_simplicity_preference(self):
        rows = [dict(id="compact", feature_count=20, architecture="global", MAE=.1, std_fold_MAE=.01),
                dict(id="large", feature_count=206, architecture="global", MAE=.099, std_fold_MAE=.01)]
        self.assertEqual(choose_simple(rows, self.config)["id"], "compact")

    def test_final_prediction_keys_bounds_and_no_targets(self):
        output = pd.read_parquet(ROOT / "predictions/final_forecast.parquet")
        pd.testing.assert_frame_equal(output[KEYS], self.comp[KEYS])
        self.assertTrue(output.predicted_normalized_active_power.between(0, 1).all())
        self.assertNotIn(TARGET, output)
        self.assertEqual(len(output), 2688)

    def test_final_registry_checkpoints_precede_every_issue(self):
        report = json.loads((ROOT / "reports/prediction_validation.json").read_text(encoding="utf-8"))
        self.assertTrue(report["one_prediction_per_input_key"])
        for batch in report["batches"]:
            self.assertLess(pd.Timestamp(batch["train_max_available"]), pd.Timestamp(batch["issue"]))

    def test_final_features_are_exact_model_features(self):
        import joblib
        registry = json.loads((ROOT / "models/model_registry.json").read_text(encoding="utf-8"))
        features = json.loads((ROOT / "models/final_features.json").read_text(encoding="utf-8"))
        union = set()
        for horizon, route in registry["routes"].items():
            for segment in route["segments"]:
                expected = features["by_route"][horizon + "__" + segment["segment"]]
                self.assertEqual(segment["features"], expected)
                union.update(expected)
                bundle = joblib.load(ROOT / segment["checkpoints"][0]["model_file"])
                self.assertEqual(bundle["schema"]["features"], expected)
        self.assertEqual(union, set(features["features"]))

    def test_all_experiments_use_identical_oof_rows(self):
        run = json.loads((ROOT / "reports/ml_active_run.json").read_text(encoding="utf-8"))
        leaderboard = pd.read_csv(ROOT / "reports/model_leaderboard.csv")
        expected = sorted(np.concatenate([fold["valid"] for fold in self.folds]))
        for experiment in leaderboard.id:
            predictions = pd.read_parquet(ROOT / "experiments" / run["run_id"] / experiment / "oof_predictions.parquet")
            self.assertEqual(sorted(predictions.row_id.tolist()), expected)
            self.assertTrue(np.isfinite(predictions.prediction).all())

    def test_seed_repeatability_on_small_fit(self):
        fit = self.train.iloc[:2000]
        features = ["turbine_id", "lead_hours", "gfs_wind_speed_100m"]
        a = fit_learner(fit, features, "LightGBM", self.config, fixed_iterations=15)
        b = fit_learner(fit, features, "LightGBM", self.config, fixed_iterations=15)
        pred_a, _ = predict_learner(a, fit.iloc[:100])
        pred_b, _ = predict_learner(b, fit.iloc[:100])
        np.testing.assert_array_equal(pred_a, pred_b)

    def test_feature_count_curve_has_one_global_comparison_per_set(self):
        curve = pd.read_csv(ROOT / "reports/feature_count_experiment.csv")
        self.assertFalse(curve.duplicated(["model", "set_label"]).any())
        self.assertEqual(set(curve.requested_feature_count), {10, 15, 20, 21, 30, 50, 206})


if __name__ == "__main__":
    unittest.main()
