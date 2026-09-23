# Feature safety

Explicit allowlist: no eval/actual/target/timestamp/split fields in X.

Turbine and horizon are categorical, never arbitrary numerical IDs. Category vocabularies are fitted on training only. Invalid provider measurements are masked by existing valid flags; missing values are not backfilled.

Historical weather error features are checked against their latest-available provenance. Validation-month SCADA is excluded from their calculation; previous-month observations still require availability < issue.

Full206 is a benchmark only. CORE has 21 predictors; Full means compact Full Agent features (24), not all 206. Simple direction sin/cos are deterministic row-local transforms of archived circular means.

## SAFE CANDIDATES (NOT ALL USED)

| feature | dtype |
| --- | --- |
| lead_hours | int64 |
| horizon_bucket | str |
| archive_nominal_lead_hours | int64 |
| turbine_id | str |
| ecmwf_wind_speed_10m | float64 |
| ecmwf_wind_speed_100m | float64 |
| ecmwf_wind_direction_10m | float64 |
| ecmwf_wind_direction_100m | float64 |
| ecmwf_temperature_2m | float64 |
| ecmwf_surface_pressure | float64 |
| ecmwf_relative_humidity_2m | float64 |
| ecmwf_wind_gusts_10m | float64 |
| ecmwf_api_error | bool |
| ecmwf_missing_target_hour | bool |
| gfs_wind_speed_10m | float64 |
| gfs_wind_speed_100m | float64 |
| gfs_wind_direction_10m | float64 |
| gfs_wind_direction_100m | float64 |
| gfs_temperature_2m | float64 |
| gfs_surface_pressure | float64 |
| gfs_relative_humidity_2m | float64 |
| gfs_wind_gusts_10m | float64 |
| gfs_api_error | bool |
| gfs_missing_target_hour | bool |
| icon_wind_speed_10m | float64 |
| icon_wind_speed_100m | float64 |
| icon_wind_direction_10m | float64 |
| icon_wind_direction_100m | float64 |
| icon_temperature_2m | float64 |
| icon_surface_pressure | float64 |
| icon_relative_humidity_2m | float64 |
| icon_wind_gusts_10m | float64 |
| icon_api_error | bool |
| icon_missing_target_hour | bool |
| ecmwf_wind_speed_10m_valid | bool |
| ecmwf_wind_speed_100m_valid | bool |
| ecmwf_wind_direction_10m_valid | bool |
| ecmwf_wind_direction_100m_valid | bool |
| ecmwf_temperature_2m_valid | bool |
| ecmwf_surface_pressure_valid | bool |
| ecmwf_relative_humidity_2m_valid | bool |
| ecmwf_wind_gusts_10m_valid | bool |
| ecmwf_available | bool |
| ecmwf_missing_values_count | int8 |
| ecmwf_impossible_values_count | int8 |
| ecmwf_partial_coverage | bool |
| ecmwf_quality_ok | bool |
| gfs_wind_speed_10m_valid | bool |
| gfs_wind_speed_100m_valid | bool |
| gfs_wind_direction_10m_valid | bool |
| gfs_wind_direction_100m_valid | bool |
| gfs_temperature_2m_valid | bool |
| gfs_surface_pressure_valid | bool |
| gfs_relative_humidity_2m_valid | bool |
| gfs_wind_gusts_10m_valid | bool |
| gfs_available | bool |
| gfs_missing_values_count | int8 |
| gfs_impossible_values_count | int8 |
| gfs_partial_coverage | bool |
| gfs_quality_ok | bool |
| icon_wind_speed_10m_valid | bool |
| icon_wind_speed_100m_valid | bool |
| icon_wind_direction_10m_valid | bool |
| icon_wind_direction_100m_valid | bool |
| icon_temperature_2m_valid | bool |
| icon_surface_pressure_valid | bool |
| icon_relative_humidity_2m_valid | bool |
| icon_wind_gusts_10m_valid | bool |
| icon_available | bool |
| icon_missing_values_count | int8 |
| icon_impossible_values_count | int8 |
| icon_partial_coverage | bool |
| icon_quality_ok | bool |
| weather_models_available_count | int8 |
| weather_models_usable_count | int8 |
| weather_data_quality_score | float64 |
| weather_critical_missing | bool |
| ecmwf_wind_mae_7d | float64 |
| ecmwf_wind_rmse_7d | float64 |
| ecmwf_wind_bias_7d | float64 |
| ecmwf_wind_n_7d | float64 |
| ecmwf_wind_mae_30d | float64 |
| ecmwf_wind_rmse_30d | float64 |
| ecmwf_wind_bias_30d | float64 |
| ecmwf_wind_n_30d | float64 |
| ecmwf_wind_mae_90d | float64 |
| ecmwf_wind_rmse_90d | float64 |
| ecmwf_wind_bias_90d | float64 |
| ecmwf_wind_n_90d | float64 |
| ecmwf_temperature_mae_7d | float64 |
| ecmwf_temperature_rmse_7d | float64 |
| ecmwf_temperature_bias_7d | float64 |
| ecmwf_temperature_n_7d | float64 |
| ecmwf_temperature_mae_30d | float64 |
| ecmwf_temperature_rmse_30d | float64 |
| ecmwf_temperature_bias_30d | float64 |
| ecmwf_temperature_n_30d | float64 |
| ecmwf_temperature_mae_90d | float64 |
| ecmwf_temperature_rmse_90d | float64 |
| ecmwf_temperature_bias_90d | float64 |
| ecmwf_temperature_n_90d | float64 |
| gfs_wind_mae_7d | float64 |
| gfs_wind_rmse_7d | float64 |
| gfs_wind_bias_7d | float64 |
| gfs_wind_n_7d | float64 |
| gfs_wind_mae_30d | float64 |
| gfs_wind_rmse_30d | float64 |
| gfs_wind_bias_30d | float64 |
| gfs_wind_n_30d | float64 |
| gfs_wind_mae_90d | float64 |
| gfs_wind_rmse_90d | float64 |
| gfs_wind_bias_90d | float64 |
| gfs_wind_n_90d | float64 |
| gfs_temperature_mae_7d | float64 |
| gfs_temperature_rmse_7d | float64 |
| gfs_temperature_bias_7d | float64 |
| gfs_temperature_n_7d | float64 |
| gfs_temperature_mae_30d | float64 |
| gfs_temperature_rmse_30d | float64 |
| gfs_temperature_bias_30d | float64 |
| gfs_temperature_n_30d | float64 |
| gfs_temperature_mae_90d | float64 |
| gfs_temperature_rmse_90d | float64 |
| gfs_temperature_bias_90d | float64 |
| gfs_temperature_n_90d | float64 |
| icon_wind_mae_7d | float64 |
| icon_wind_rmse_7d | float64 |
| icon_wind_bias_7d | float64 |
| icon_wind_n_7d | float64 |
| icon_wind_mae_30d | float64 |
| icon_wind_rmse_30d | float64 |
| icon_wind_bias_30d | float64 |
| icon_wind_n_30d | float64 |
| icon_wind_mae_90d | float64 |
| icon_wind_rmse_90d | float64 |
| icon_wind_bias_90d | float64 |
| icon_wind_n_90d | float64 |
| icon_temperature_mae_7d | float64 |
| icon_temperature_rmse_7d | float64 |
| icon_temperature_bias_7d | float64 |
| icon_temperature_n_7d | float64 |
| icon_temperature_mae_30d | float64 |
| icon_temperature_rmse_30d | float64 |
| icon_temperature_bias_30d | float64 |
| icon_temperature_n_30d | float64 |
| icon_temperature_mae_90d | float64 |
| icon_temperature_rmse_90d | float64 |
| icon_temperature_bias_90d | float64 |
| icon_temperature_n_90d | float64 |
| wind_weights_cold_start | bool |
| ecmwf_weight | float64 |
| gfs_weight | float64 |
| icon_weight | float64 |
| best_weather_model_recent | str |
| temperature_weights_cold_start | bool |
| ecmwf_temperature_weight | float64 |
| gfs_temperature_weight | float64 |
| icon_temperature_weight | float64 |
| wind_speed_10m_mean | float64 |
| ensemble_wind_speed_10m | float64 |
| wind_speed_models_std | float64 |
| wind_speed_models_range | float64 |
| wind_speed_100m_mean | float64 |
| ensemble_wind_speed_100m | float64 |
| wind_direction_10m_circular_dispersion | float64 |
| ensemble_wind_direction_10m_circular_dispersion | float64 |
| wind_direction_10m_mean | float64 |
| ensemble_wind_direction_10m | float64 |
| wind_direction_100m_circular_dispersion | float64 |
| ensemble_wind_direction_100m_circular_dispersion | float64 |
| wind_direction_100m_mean | float64 |
| ensemble_wind_direction_100m | float64 |
| temperature_models_std | float64 |
| temperature_models_range | float64 |
| temperature_2m_mean | float64 |
| ensemble_temperature_2m | float64 |
| surface_pressure_mean | float64 |
| ensemble_surface_pressure | float64 |
| relative_humidity_2m_mean | float64 |
| ensemble_relative_humidity_2m | float64 |
| wind_gusts_10m_mean | float64 |
| ensemble_wind_gusts_10m | float64 |
| target_hour | int32 |
| target_day_of_week | int32 |
| target_month | int32 |
| target_day_of_year | int32 |
| hour_sin | float64 |
| hour_cos | float64 |
| day_of_year_sin | float64 |
| day_of_year_cos | float64 |
| ecmwf_wind_direction_10m_sin | float64 |
| ecmwf_wind_direction_10m_cos | float64 |
| ecmwf_wind_direction_100m_sin | float64 |
| ecmwf_wind_direction_100m_cos | float64 |
| gfs_wind_direction_10m_sin | float64 |
| gfs_wind_direction_10m_cos | float64 |
| gfs_wind_direction_100m_sin | float64 |
| gfs_wind_direction_100m_cos | float64 |
| icon_wind_direction_10m_sin | float64 |
| icon_wind_direction_10m_cos | float64 |
| icon_wind_direction_100m_sin | float64 |
| icon_wind_direction_100m_cos | float64 |
| ensemble_wind_direction_10m_sin | float64 |
| ensemble_wind_direction_10m_cos | float64 |
| ensemble_wind_direction_100m_sin | float64 |
| ensemble_wind_direction_100m_cos | float64 |

## EXCLUDED FEATURES / REASON FOR EXCLUSION

| feature | reason |
| --- | --- |
| forecast_issue_time | Raw timestamp; only explicit calendar transforms allowed |
| target_time | Raw timestamp; only explicit calendar transforms allowed |
| archive_day | Not in audited upstream feature allowlist; metadata/ID/provenance |
| forecast_day | Not in audited upstream feature allowlist; metadata/ID/provenance |
| target_local_time | Raw timestamp; only explicit calendar transforms allowed |
| archive_reference_time | Raw timestamp; only explicit calendar transforms allowed |
| dataset_split | Split identifier |
| ecmwf_cache_key | Not in audited upstream feature allowlist; metadata/ID/provenance |
| ecmwf_grid_latitude | Not in audited upstream feature allowlist; metadata/ID/provenance |
| ecmwf_grid_longitude | Not in audited upstream feature allowlist; metadata/ID/provenance |
| gfs_cache_key | Not in audited upstream feature allowlist; metadata/ID/provenance |
| gfs_grid_latitude | Not in audited upstream feature allowlist; metadata/ID/provenance |
| gfs_grid_longitude | Not in audited upstream feature allowlist; metadata/ID/provenance |
| icon_cache_key | Not in audited upstream feature allowlist; metadata/ID/provenance |
| icon_grid_latitude | Not in audited upstream feature allowlist; metadata/ID/provenance |
| icon_grid_longitude | Not in audited upstream feature allowlist; metadata/ID/provenance |
| methodology_status | Not in audited upstream feature allowlist; metadata/ID/provenance |
| weather_archive_method | Not in audited upstream feature allowlist; metadata/ID/provenance |
| weather_archive_confidence | Not in audited upstream feature allowlist; metadata/ID/provenance |
| timezone_status | Not in audited upstream feature allowlist; metadata/ID/provenance |
| scada_utc_offset_hours | Observed/evaluation/provenance field; not a predictor |
| weather_configuration | Not in audited upstream feature allowlist; metadata/ID/provenance |
| ecmwf_duplicate_forecast | Not in audited upstream feature allowlist; metadata/ID/provenance |
| ecmwf_timestamps_consistent | Not in audited upstream feature allowlist; metadata/ID/provenance |
| ecmwf_run_time | Raw timestamp; only explicit calendar transforms allowed |
| ecmwf_estimated_availability_time | Raw timestamp; only explicit calendar transforms allowed |
| ecmwf_stale_run | Not in audited upstream feature allowlist; metadata/ID/provenance |
| gfs_duplicate_forecast | Not in audited upstream feature allowlist; metadata/ID/provenance |
| gfs_timestamps_consistent | Not in audited upstream feature allowlist; metadata/ID/provenance |
| gfs_run_time | Raw timestamp; only explicit calendar transforms allowed |
| gfs_estimated_availability_time | Raw timestamp; only explicit calendar transforms allowed |
| gfs_stale_run | Not in audited upstream feature allowlist; metadata/ID/provenance |
| icon_duplicate_forecast | Not in audited upstream feature allowlist; metadata/ID/provenance |
| icon_timestamps_consistent | Not in audited upstream feature allowlist; metadata/ID/provenance |
| icon_run_time | Raw timestamp; only explicit calendar transforms allowed |
| icon_estimated_availability_time | Raw timestamp; only explicit calendar transforms allowed |
| icon_stale_run | Not in audited upstream feature allowlist; metadata/ID/provenance |
| ecmwf_wind_history_latest_7d | Observed/evaluation/provenance field; not a predictor |
| ecmwf_wind_history_latest_30d | Observed/evaluation/provenance field; not a predictor |
| ecmwf_wind_history_latest_90d | Observed/evaluation/provenance field; not a predictor |
| ecmwf_temperature_history_latest_7d | Observed/evaluation/provenance field; not a predictor |
| ecmwf_temperature_history_latest_30d | Observed/evaluation/provenance field; not a predictor |
| ecmwf_temperature_history_latest_90d | Observed/evaluation/provenance field; not a predictor |
| gfs_wind_history_latest_7d | Observed/evaluation/provenance field; not a predictor |
| gfs_wind_history_latest_30d | Observed/evaluation/provenance field; not a predictor |
| gfs_wind_history_latest_90d | Observed/evaluation/provenance field; not a predictor |
| gfs_temperature_history_latest_7d | Observed/evaluation/provenance field; not a predictor |
| gfs_temperature_history_latest_30d | Observed/evaluation/provenance field; not a predictor |
| gfs_temperature_history_latest_90d | Observed/evaluation/provenance field; not a predictor |
| icon_wind_history_latest_7d | Observed/evaluation/provenance field; not a predictor |
| icon_wind_history_latest_30d | Observed/evaluation/provenance field; not a predictor |
| icon_wind_history_latest_90d | Observed/evaluation/provenance field; not a predictor |
| icon_temperature_history_latest_7d | Observed/evaluation/provenance field; not a predictor |
| icon_temperature_history_latest_30d | Observed/evaluation/provenance field; not a predictor |
| icon_temperature_history_latest_90d | Observed/evaluation/provenance field; not a predictor |
| normalized_active_power | Supervised target; never X |

## Experiment groups

| group | count | features |
| --- | --- | --- |
| ECMWF | 11 | turbine_id, lead_hours, hour_sin, hour_cos, day_of_year_sin, day_of_year_cos, ecmwf_wind_speed_100m, ecmwf_wind_direction_100m_sin, ecmwf_wind_direction_100m_cos, ecmwf_temperature_2m, ecmwf_quality_ok |
| GFS | 11 | turbine_id, lead_hours, hour_sin, hour_cos, day_of_year_sin, day_of_year_cos, gfs_wind_speed_100m, gfs_wind_direction_100m_sin, gfs_wind_direction_100m_cos, gfs_temperature_2m, gfs_quality_ok |
| ICON | 11 | turbine_id, lead_hours, hour_sin, hour_cos, day_of_year_sin, day_of_year_cos, icon_wind_speed_100m, icon_wind_direction_100m_sin, icon_wind_direction_100m_cos, icon_temperature_2m, icon_quality_ok |
| Simple | 10 | turbine_id, lead_hours, hour_sin, hour_cos, day_of_year_sin, day_of_year_cos, wind_speed_100m_mean, wind_direction_100m_mean_sin, wind_direction_100m_mean_cos, temperature_2m_mean |
| Weighted | 13 | turbine_id, lead_hours, hour_sin, hour_cos, day_of_year_sin, day_of_year_cos, ensemble_wind_speed_100m, ensemble_wind_direction_100m_sin, ensemble_wind_direction_100m_cos, ensemble_temperature_2m, ecmwf_weight, gfs_weight, icon_weight |
| All | 16 | turbine_id, lead_hours, hour_sin, hour_cos, day_of_year_sin, day_of_year_cos, ecmwf_wind_speed_100m, ecmwf_wind_direction_100m_sin, ecmwf_wind_direction_100m_cos, gfs_wind_speed_100m, gfs_wind_direction_100m_sin, gfs_wind_direction_100m_cos, icon_wind_speed_100m, icon_wind_direction_100m_sin, icon_wind_direction_100m_cos, temperature_2m_mean |
| All_Disagreement | 17 | turbine_id, lead_hours, hour_sin, hour_cos, day_of_year_sin, day_of_year_cos, ecmwf_wind_speed_100m, ecmwf_wind_direction_100m_sin, ecmwf_wind_direction_100m_cos, gfs_wind_speed_100m, gfs_wind_direction_100m_sin, gfs_wind_direction_100m_cos, icon_wind_speed_100m, icon_wind_direction_100m_sin, icon_wind_direction_100m_cos, temperature_2m_mean, wind_speed_models_std |
| Full | 24 | turbine_id, lead_hours, hour_sin, hour_cos, day_of_year_sin, day_of_year_cos, ecmwf_wind_speed_100m, ecmwf_wind_direction_100m_sin, ecmwf_wind_direction_100m_cos, gfs_wind_speed_100m, gfs_wind_direction_100m_sin, gfs_wind_direction_100m_cos, icon_wind_speed_100m, icon_wind_direction_100m_sin, icon_wind_direction_100m_cos, temperature_2m_mean, wind_speed_models_std, ensemble_wind_speed_100m, ecmwf_wind_mae_30d, gfs_wind_mae_30d, icon_wind_mae_30d, ecmwf_quality_ok, gfs_quality_ok, icon_quality_ok |
| Full206 | 206 | lead_hours, horizon_bucket, archive_nominal_lead_hours, turbine_id, ecmwf_wind_speed_10m, ecmwf_wind_speed_100m, ecmwf_wind_direction_10m, ecmwf_wind_direction_100m, ecmwf_temperature_2m, ecmwf_surface_pressure, ecmwf_relative_humidity_2m, ecmwf_wind_gusts_10m, ecmwf_api_error, ecmwf_missing_target_hour, gfs_wind_speed_10m, gfs_wind_speed_100m, gfs_wind_direction_10m, gfs_wind_direction_100m, gfs_temperature_2m, gfs_surface_pressure, gfs_relative_humidity_2m, gfs_wind_gusts_10m, gfs_api_error, gfs_missing_target_hour, icon_wind_speed_10m, icon_wind_speed_100m, icon_wind_direction_10m, icon_wind_direction_100m, icon_temperature_2m, icon_surface_pressure, icon_relative_humidity_2m, icon_wind_gusts_10m, icon_api_error, icon_missing_target_hour, ecmwf_wind_speed_10m_valid, ecmwf_wind_speed_100m_valid, ecmwf_wind_direction_10m_valid, ecmwf_wind_direction_100m_valid, ecmwf_temperature_2m_valid, ecmwf_surface_pressure_valid, ecmwf_relative_humidity_2m_valid, ecmwf_wind_gusts_10m_valid, ecmwf_available, ecmwf_missing_values_count, ecmwf_impossible_values_count, ecmwf_partial_coverage, ecmwf_quality_ok, gfs_wind_speed_10m_valid, gfs_wind_speed_100m_valid, gfs_wind_direction_10m_valid, gfs_wind_direction_100m_valid, gfs_temperature_2m_valid, gfs_surface_pressure_valid, gfs_relative_humidity_2m_valid, gfs_wind_gusts_10m_valid, gfs_available, gfs_missing_values_count, gfs_impossible_values_count, gfs_partial_coverage, gfs_quality_ok, icon_wind_speed_10m_valid, icon_wind_speed_100m_valid, icon_wind_direction_10m_valid, icon_wind_direction_100m_valid, icon_temperature_2m_valid, icon_surface_pressure_valid, icon_relative_humidity_2m_valid, icon_wind_gusts_10m_valid, icon_available, icon_missing_values_count, icon_impossible_values_count, icon_partial_coverage, icon_quality_ok, weather_models_available_count, weather_models_usable_count, weather_data_quality_score, weather_critical_missing, ecmwf_wind_mae_7d, ecmwf_wind_rmse_7d, ecmwf_wind_bias_7d, ecmwf_wind_n_7d, ecmwf_wind_mae_30d, ecmwf_wind_rmse_30d, ecmwf_wind_bias_30d, ecmwf_wind_n_30d, ecmwf_wind_mae_90d, ecmwf_wind_rmse_90d, ecmwf_wind_bias_90d, ecmwf_wind_n_90d, ecmwf_temperature_mae_7d, ecmwf_temperature_rmse_7d, ecmwf_temperature_bias_7d, ecmwf_temperature_n_7d, ecmwf_temperature_mae_30d, ecmwf_temperature_rmse_30d, ecmwf_temperature_bias_30d, ecmwf_temperature_n_30d, ecmwf_temperature_mae_90d, ecmwf_temperature_rmse_90d, ecmwf_temperature_bias_90d, ecmwf_temperature_n_90d, gfs_wind_mae_7d, gfs_wind_rmse_7d, gfs_wind_bias_7d, gfs_wind_n_7d, gfs_wind_mae_30d, gfs_wind_rmse_30d, gfs_wind_bias_30d, gfs_wind_n_30d, gfs_wind_mae_90d, gfs_wind_rmse_90d, gfs_wind_bias_90d, gfs_wind_n_90d, gfs_temperature_mae_7d, gfs_temperature_rmse_7d, gfs_temperature_bias_7d, gfs_temperature_n_7d, gfs_temperature_mae_30d, gfs_temperature_rmse_30d, gfs_temperature_bias_30d, gfs_temperature_n_30d, gfs_temperature_mae_90d, gfs_temperature_rmse_90d, gfs_temperature_bias_90d, gfs_temperature_n_90d, icon_wind_mae_7d, icon_wind_rmse_7d, icon_wind_bias_7d, icon_wind_n_7d, icon_wind_mae_30d, icon_wind_rmse_30d, icon_wind_bias_30d, icon_wind_n_30d, icon_wind_mae_90d, icon_wind_rmse_90d, icon_wind_bias_90d, icon_wind_n_90d, icon_temperature_mae_7d, icon_temperature_rmse_7d, icon_temperature_bias_7d, icon_temperature_n_7d, icon_temperature_mae_30d, icon_temperature_rmse_30d, icon_temperature_bias_30d, icon_temperature_n_30d, icon_temperature_mae_90d, icon_temperature_rmse_90d, icon_temperature_bias_90d, icon_temperature_n_90d, wind_weights_cold_start, ecmwf_weight, gfs_weight, icon_weight, best_weather_model_recent, temperature_weights_cold_start, ecmwf_temperature_weight, gfs_temperature_weight, icon_temperature_weight, wind_speed_10m_mean, ensemble_wind_speed_10m, wind_speed_models_std, wind_speed_models_range, wind_speed_100m_mean, ensemble_wind_speed_100m, wind_direction_10m_circular_dispersion, ensemble_wind_direction_10m_circular_dispersion, wind_direction_10m_mean, ensemble_wind_direction_10m, wind_direction_100m_circular_dispersion, ensemble_wind_direction_100m_circular_dispersion, wind_direction_100m_mean, ensemble_wind_direction_100m, temperature_models_std, temperature_models_range, temperature_2m_mean, ensemble_temperature_2m, surface_pressure_mean, ensemble_surface_pressure, relative_humidity_2m_mean, ensemble_relative_humidity_2m, wind_gusts_10m_mean, ensemble_wind_gusts_10m, target_hour, target_day_of_week, target_month, target_day_of_year, hour_sin, hour_cos, day_of_year_sin, day_of_year_cos, ecmwf_wind_direction_10m_sin, ecmwf_wind_direction_10m_cos, ecmwf_wind_direction_100m_sin, ecmwf_wind_direction_100m_cos, gfs_wind_direction_10m_sin, gfs_wind_direction_10m_cos, gfs_wind_direction_100m_sin, gfs_wind_direction_100m_cos, icon_wind_direction_10m_sin, icon_wind_direction_10m_cos, icon_wind_direction_100m_sin, icon_wind_direction_100m_cos, ensemble_wind_direction_10m_sin, ensemble_wind_direction_10m_cos, ensemble_wind_direction_100m_sin, ensemble_wind_direction_100m_cos |
| CORE | 21 | turbine_id, lead_hours, hour_sin, hour_cos, day_of_year_sin, day_of_year_cos, ecmwf_wind_speed_100m, ecmwf_wind_direction_100m_sin, ecmwf_wind_direction_100m_cos, gfs_wind_speed_100m, gfs_wind_direction_100m_sin, gfs_wind_direction_100m_cos, icon_wind_speed_100m, icon_wind_direction_100m_sin, icon_wind_direction_100m_cos, temperature_2m_mean, wind_speed_models_std, ensemble_wind_speed_100m, ecmwf_wind_mae_30d, gfs_wind_mae_30d, icon_wind_mae_30d |
| Full_No_Performance | 21 | turbine_id, lead_hours, hour_sin, hour_cos, day_of_year_sin, day_of_year_cos, ecmwf_wind_speed_100m, ecmwf_wind_direction_100m_sin, ecmwf_wind_direction_100m_cos, gfs_wind_speed_100m, gfs_wind_direction_100m_sin, gfs_wind_direction_100m_cos, icon_wind_speed_100m, icon_wind_direction_100m_sin, icon_wind_direction_100m_cos, temperature_2m_mean, wind_speed_models_std, ensemble_wind_speed_100m, ecmwf_quality_ok, gfs_quality_ok, icon_quality_ok |

## USED FEATURES — FINAL MODEL

| feature | source | meaning | reason_for_inclusion | importance |
| --- | --- | --- | --- | --- |
| ensemble_wind_speed_100m | Historical-performance weighted weather | Weighted forecast; direction expressed by sine/cosine | Part of near-best compact walk-forward configuration; physically interpretable | 0.57942 |
| wind_speed_10m_mean | Archived weather aggregate | 10m forecast wind speed (m/s): near-surface regime, complementary to 100m flow | Part of near-best compact walk-forward configuration; physically interpretable | 0.12599 |
| ecmwf_wind_speed_10m | ECMWF | 10m forecast wind speed (m/s): near-surface regime, complementary to 100m flow | Part of near-best compact walk-forward configuration; physically interpretable | 0.05954 |
| day_of_year_cos | Target local calendar | Cyclic hour or annual phase | Part of near-best compact walk-forward configuration; physically interpretable | 0.03667 |
| day_of_year_sin | Target local calendar | Cyclic hour or annual phase | Part of near-best compact walk-forward configuration; physically interpretable | 0.03257 |
| ecmwf_surface_pressure | ECMWF | Forecast surface pressure (hPa): air-density / synoptic regime proxy | Part of near-best compact walk-forward configuration; physically interpretable | 0.03026 |
| gfs_wind_direction_10m_cos | GFS | Sine/cosine component of forecast direction: directional terrain and wake regimes, no raw angle discontinuity | Part of near-best compact walk-forward configuration; physically interpretable | 0.02553 |
| gfs_wind_direction_100m_sin | GFS | Sine/cosine component of forecast direction: directional terrain and wake regimes, no raw angle discontinuity | Part of near-best compact walk-forward configuration; physically interpretable | 0.02326 |
| ecmwf_wind_speed_100m | ECMWF | 100m forecast wind speed (m/s): proxy for inflow near turbine operating height | Part of near-best compact walk-forward configuration; physically interpretable | 0.02202 |
| icon_wind_gusts_10m | ICON | Forecast gust speed (m/s): turbulent / gusty wind regime proxy | Part of near-best compact walk-forward configuration; physically interpretable | 0.02055 |
| gfs_relative_humidity_2m | GFS | Forecast relative humidity (%): air-mass / moisture regime proxy, not proof of icing | Part of near-best compact walk-forward configuration; physically interpretable | 0.01590 |
| hour_sin | Target local calendar | Cyclic hour or annual phase | Part of near-best compact walk-forward configuration; physically interpretable | 0.01341 |
| icon_wind_speed_100m | ICON | 100m forecast wind speed (m/s): proxy for inflow near turbine operating height | Part of near-best compact walk-forward configuration; physically interpretable | 0.00634 |
| turbine_id | SCADA identifier | Categorical turbine identity; captures turbine differences | Part of near-best compact walk-forward configuration; physically interpretable | 0.00595 |
| lead_hours | Forecast schedule | Lead from issue to target, hours | Part of near-best compact walk-forward configuration; physically interpretable | 0.00259 |

The other safe candidates were benchmark/selection inputs only; final_removed_features.csv records why each was omitted.
