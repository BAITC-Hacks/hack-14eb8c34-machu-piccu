"""Point-in-time checks under the user-approved fixed-lead archive methodology."""
import numpy as np
import pandas as pd

LIMITATION = "Previous Runs API provides forecasts at fixed historical lead-time offsets but does not expose exact historical API publication timestamps for every individual value."


def require(condition, message):
    if not bool(condition):
        raise ValueError(message)


def validate_feature_columns(features):
    banned = [c for c in features if c.startswith(("eval_", "actual_", "scada_")) or c in ["normalized_active_power", "observation_available_time", "training_eligible"] or "history_latest" in c]
    require(not banned, f"Outcome/evaluation columns leaked into features: {banned}")


def estimated_run_availability(run_time, provider, config):
    return pd.Timestamp(run_time) + pd.Timedelta(hours=config["dissemination_buffers_hours"][provider])


def validate_point_in_time_integrity(frame, config, features=None):
    keys = ["turbine_id", "forecast_issue_time", "target_time", "weather_configuration"]
    require(not frame.duplicated(keys).any(), "Duplicate primary key")
    require(frame.forecast_issue_time.notna().all() and frame.target_time.notna().all(), "Null timestamps")
    require((frame.target_time > frame.forecast_issue_time).all(), "Target must be after issue")
    actual_lead = (frame.target_time - frame.forecast_issue_time).dt.total_seconds() / 3600
    require((actual_lead == frame.lead_hours).all(), "Incorrect lead_hours")
    require(frame.lead_hours.between(1, config["forecast_horizon_hours"]).all(), "Invalid lead range")
    expected_day = np.where(frame.lead_hours <= 24, 1, 2)
    require((frame.archive_day == expected_day).all(), "Wrong D1/D2 archive selection")
    require((frame.horizon_bucket == np.where(expected_day == 1, "D1", "D2")).all(), "Horizon bucket mismatch")
    require((frame.archive_nominal_lead_hours == frame.archive_day * 24).all(), "Wrong nominal archive lead")
    reference = frame.target_time - pd.to_timedelta(frame.archive_nominal_lead_hours, unit="h")
    require((frame.archive_reference_time == reference).all(), "Incorrect archive reference time")
    require((reference <= frame.forecast_issue_time).all(), "Archive nominal reference after issue")
    require((frame.weather_archive_method == "open_meteo_previous_runs").all(), "Non-approved archive method")
    require((frame.weather_archive_confidence == "fixed_lead_time_archive").all(), "Missing archive confidence")
    require((frame.methodology_status == "lead_time_archive").all(), "Missing methodology label")
    for model in config["weather_models"]:
        run = frame[f"{model}_run_time"]
        availability = frame[f"{model}_estimated_availability_time"]
        known = run.notna()
        if known.any():
            require((run[known] <= frame.loc[known, "forecast_issue_time"]).all(), "Provider run after issue")
            minimum = run[known] + pd.Timedelta(hours=config["dissemination_buffers_hours"][model])
            require(availability[known].notna().all(), "Known run requires estimated publication availability")
            require((availability[known] >= minimum).all(), "Dissemination buffer not applied")
            require((availability[known] <= frame.loc[known, "forecast_issue_time"]).all(), "Run not disseminated by issue")
        for kind in ["wind", "temperature"]:
            for days in config["rolling_windows"]:
                latest_col = f"{model}_{kind}_history_latest_{days}d"
                if latest_col in frame:
                    known_history = frame[latest_col].notna()
                    require((frame.loc[known_history, latest_col] < frame.loc[known_history, "forecast_issue_time"]).all(), "Future observation in rolling history")
                    for metric in ["mae", "rmse", "bias"]:
                        present = frame[f"{model}_{kind}_{metric}_{days}d"].notna()
                        require((~present | known_history).all(), "Metric without past-history provenance")
    train = frame.dataset_split == "train"
    competition = frame.dataset_split == "competition_test"
    require((train | competition).all(), "Unknown dataset split")
    require((frame.loc[train, "target_local_time"] <= pd.Timestamp(config["train_end"])).all(), "Train/test boundary violated")
    require(frame.loc[competition, "target_local_time"].between(pd.Timestamp(config["competition_start"]), pd.Timestamp(config["competition_end"])).all(), "Competition outside requested period")
    if features is not None:
        validate_feature_columns(features)
        require(set(features).issubset(frame.columns), "Missing features")
    return {"status": "PASS_UNDER_DOCUMENTED_LEAD_TIME_SEMANTICS", "rows_checked": len(frame), "exact_publication_timestamps_verified": False, "limitation": LIMITATION}
