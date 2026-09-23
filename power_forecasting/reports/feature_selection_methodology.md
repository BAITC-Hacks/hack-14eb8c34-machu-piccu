# Feature selection methodology

Ranking fitted only on first-fold training: latest target 2025-09-28 16:00:00+00:00. No outer validation or competition targets used.

CORE is physically motivated, fixed in advance (21 features). Compact Full adds provider quality flags (24). Full206 is a reference benchmark, never the default final set.

Training-only native LightGBM importance ranks candidates. Missingness >60%, dominant value >=99.5%, redundant raw angles/calendars, rolling windows/metrics other than wind MAE 30d are removed. Absolute training-only pairwise correlation >0.98 removes lower-ranked proxies. Turbine and lead are protected for routing/identity. Selection is frozen before scoring any outer month.

Top-N means up to N eligible predictors; requested and actual counts are both reported. Top50 may contain fewer than 50 if the safety/redundancy filters leave fewer candidates. No unsafe or redundant columns are added merely to reach a count. The same ranked list is used in every fold.

The 0.5% relative-MAE near-best band favors fewer features and simpler architecture. More than 35 features require at least 2% relative reduction versus the best compact candidate. These are practical thresholds, not statistical significance claims.

| feature | importance_training_only | selected_candidate | reason |
| --- | --- | --- | --- |
| turbine_id | 0.00603 | True | Ranked safe candidate |
| lead_hours | 0.00036 | True | Ranked safe candidate |
| ensemble_wind_speed_100m | 0.43522 | True | Ranked safe candidate |
| wind_speed_100m_mean | 0.09294 | False | Strongly correlated training-only proxy for ensemble_wind_speed_100m |
| ecmwf_wind_speed_10m | 0.06881 | True | Ranked safe candidate |
| wind_speed_10m_mean | 0.04755 | True | Ranked safe candidate |
| ecmwf_surface_pressure | 0.01323 | True | Ranked safe candidate |
| ensemble_wind_speed_10m | 0.01272 | False | Strongly correlated training-only proxy for wind_speed_10m_mean |
| day_of_year_cos | 0.01084 | True | Ranked safe candidate |
| day_of_year_sin | 0.01066 | True | Ranked safe candidate |
| ecmwf_wind_speed_100m | 0.00935 | True | Ranked safe candidate |
| gfs_wind_direction_100m_sin | 0.00890 | True | Ranked safe candidate |
| target_day_of_year | 0.00878 | False | Redundant horizon or raw calendar; use lead and cyclic time |
| icon_wind_gusts_10m | 0.00811 | True | Ranked safe candidate |
| gfs_wind_direction_10m_cos | 0.00786 | True | Ranked safe candidate |
| hour_sin | 0.00705 | True | Ranked safe candidate |
| icon_wind_speed_100m | 0.00640 | True | Ranked safe candidate |
| gfs_wind_direction_10m | 0.00623 | False | Raw angle replaced by sine/cosine |
| gfs_relative_humidity_2m | 0.00587 | True | Ranked safe candidate |
| icon_surface_pressure | 0.00546 | False | Strongly correlated training-only proxy for ecmwf_surface_pressure |
| gfs_surface_pressure | 0.00494 | False | Strongly correlated training-only proxy for ecmwf_surface_pressure |
| gfs_wind_speed_10m | 0.00466 | True | Ranked safe candidate |
| target_day_of_week | 0.00466 | False | Redundant horizon or raw calendar; use lead and cyclic time |
| ecmwf_relative_humidity_2m | 0.00459 | True | Ranked safe candidate |
| target_hour | 0.00434 | False | Redundant horizon or raw calendar; use lead and cyclic time |
| ecmwf_temperature_2m | 0.00418 | True | Ranked safe candidate |
| ensemble_wind_direction_100m_circular_dispersion | 0.00398 | True | Ranked safe candidate |
| hour_cos | 0.00388 | True | Ranked safe candidate |
| icon_wind_bias_90d | 0.00385 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_direction_100m | 0.00343 | False | Raw angle replaced by sine/cosine |
| ensemble_relative_humidity_2m | 0.00339 | True | Ranked safe candidate |
| ensemble_wind_gusts_10m | 0.00337 | True | Ranked safe candidate |
| gfs_wind_direction_10m_sin | 0.00333 | True | Ranked safe candidate |
| surface_pressure_mean | 0.00331 | False | Strongly correlated training-only proxy for ecmwf_surface_pressure |
| gfs_wind_bias_7d | 0.00328 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_2m | 0.00323 | False | Strongly correlated training-only proxy for ecmwf_temperature_2m |
| icon_temperature_2m | 0.00319 | False | Strongly correlated training-only proxy for ecmwf_temperature_2m |
| ecmwf_wind_bias_7d | 0.00308 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_direction_10m | 0.00304 | False | Raw angle replaced by sine/cosine |
| ecmwf_temperature_bias_7d | 0.00304 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_bias_7d | 0.00304 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_direction_100m_sin | 0.00295 | True | Ranked safe candidate |
| gfs_temperature_mae_30d | 0.00294 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| wind_speed_models_std | 0.00294 | True | Ranked safe candidate |
| wind_speed_models_range | 0.00291 | False | Strongly correlated training-only proxy for wind_speed_models_std |
| wind_direction_10m_mean | 0.00277 | False | Raw angle replaced by sine/cosine |
| gfs_temperature_rmse_7d | 0.00273 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ensemble_wind_direction_10m | 0.00269 | False | Raw angle replaced by sine/cosine |
| icon_temperature_rmse_30d | 0.00262 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_bias_7d | 0.00262 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_direction_10m_sin | 0.00256 | True | Ranked safe candidate |
| icon_weight | 0.00249 | True | Ranked safe candidate |
| gfs_wind_rmse_7d | 0.00235 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_weight | 0.00233 | True | Ranked safe candidate |
| gfs_wind_mae_30d | 0.00228 | True | Ranked safe candidate |
| ecmwf_wind_rmse_7d | 0.00221 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| wind_gusts_10m_mean | 0.00219 | False | Strongly correlated training-only proxy for ensemble_wind_gusts_10m |
| icon_temperature_rmse_7d | 0.00217 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_mae_7d | 0.00215 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_speed_10m | 0.00212 | True | Ranked safe candidate |
| icon_temperature_mae_7d | 0.00210 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_weight | 0.00205 | True | Ranked safe candidate |
| ensemble_surface_pressure | 0.00201 | False | Strongly correlated training-only proxy for ecmwf_surface_pressure |
| gfs_temperature_mae_7d | 0.00201 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| temperature_models_std | 0.00191 | True | Ranked safe candidate |
| ensemble_wind_direction_100m_sin | 0.00190 | True | Ranked safe candidate |
| gfs_temperature_weight | 0.00189 | True | Ranked safe candidate |
| relative_humidity_2m_mean | 0.00186 | False | Strongly correlated training-only proxy for ensemble_relative_humidity_2m |
| ecmwf_temperature_bias_30d | 0.00184 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_bias_30d | 0.00183 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_rmse_90d | 0.00179 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_bias_30d | 0.00179 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_rmse_7d | 0.00175 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ensemble_temperature_2m | 0.00175 | False | Strongly correlated training-only proxy for ecmwf_temperature_2m |
| gfs_wind_mae_7d | 0.00174 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| temperature_2m_mean | 0.00172 | False | Strongly correlated training-only proxy for ecmwf_temperature_2m |
| gfs_wind_speed_100m | 0.00167 | True | Ranked safe candidate |
| ensemble_wind_direction_10m_cos | 0.00165 | True | Ranked safe candidate |
| icon_temperature_mae_30d | 0.00161 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_n_90d | 0.00161 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_mae_7d | 0.00159 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_direction_10m | 0.00159 | False | Raw angle replaced by sine/cosine |
| icon_temperature_weight | 0.00159 | True | Ranked safe candidate |
| ensemble_wind_direction_10m_sin | 0.00158 | True | Ranked safe candidate |
| ecmwf_wind_direction_100m_cos | 0.00155 | True | Ranked safe candidate |
| icon_wind_direction_10m_sin | 0.00155 | True | Ranked safe candidate |
| ecmwf_temperature_bias_90d | 0.00153 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_n_30d | 0.00149 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_gusts_10m | 0.00148 | True | Ranked safe candidate |
| ecmwf_temperature_mae_30d | 0.00147 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_n_7d | 0.00147 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| wind_direction_100m_circular_dispersion | 0.00146 | False | Strongly correlated training-only proxy for ensemble_wind_direction_100m_circular_dispersion |
| ecmwf_temperature_mae_90d | 0.00146 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_relative_humidity_2m | 0.00144 | True | Ranked safe candidate |
| ecmwf_wind_mae_30d | 0.00143 | True | Ranked safe candidate |
| icon_wind_direction_100m | 0.00140 | False | Raw angle replaced by sine/cosine |
| gfs_temperature_rmse_30d | 0.00137 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_direction_100m | 0.00136 | False | Raw angle replaced by sine/cosine |
| gfs_wind_mae_90d | 0.00135 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_rmse_30d | 0.00131 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_rmse_7d | 0.00130 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_n_30d | 0.00130 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_bias_7d | 0.00129 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ensemble_wind_direction_100m_cos | 0.00128 | True | Ranked safe candidate |
| icon_wind_bias_30d | 0.00128 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_mae_7d | 0.00124 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| wind_direction_100m_mean | 0.00116 | False | Raw angle replaced by sine/cosine |
| wind_direction_10m_circular_dispersion | 0.00112 | True | Ranked safe candidate |
| gfs_weight | 0.00105 | True | Ranked safe candidate |
| ecmwf_wind_bias_90d | 0.00105 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_bias_90d | 0.00105 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_direction_10m_cos | 0.00102 | True | Ranked safe candidate |
| icon_wind_mae_30d | 0.00098 | True | Ranked safe candidate |
| icon_wind_rmse_30d | 0.00096 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_n_90d | 0.00096 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_rmse_30d | 0.00096 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_rmse_90d | 0.00095 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_mae_90d | 0.00092 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_rmse_30d | 0.00091 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_mae_90d | 0.00089 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_bias_30d | 0.00089 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ensemble_wind_direction_10m_circular_dispersion | 0.00085 | False | Strongly correlated training-only proxy for wind_direction_10m_circular_dispersion |
| icon_wind_direction_100m_cos | 0.00084 | True | Ranked safe candidate |
| icon_wind_direction_10m_cos | 0.00082 | True | Ranked safe candidate |
| gfs_wind_direction_100m_cos | 0.00076 | True | Ranked safe candidate |
| icon_wind_direction_100m_sin | 0.00075 | True | Ranked safe candidate |
| gfs_temperature_n_90d | 0.00073 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_n_7d | 0.00063 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_n_30d | 0.00060 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ensemble_wind_direction_100m | 0.00059 | False | Raw angle replaced by sine/cosine |
| temperature_models_range | 0.00059 | False | Strongly correlated training-only proxy for temperature_models_std |
| ecmwf_temperature_n_7d | 0.00058 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_rmse_90d | 0.00053 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_bias_30d | 0.00052 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_rmse_90d | 0.00047 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_rmse_90d | 0.00046 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_bias_90d | 0.00043 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_mae_90d | 0.00041 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_mae_90d | 0.00040 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_n_90d | 0.00039 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_bias_90d | 0.00034 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| target_month | 0.00027 | False | Redundant horizon or raw calendar; use lead and cyclic time |
| icon_temperature_n_30d | 0.00025 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_rmse_90d | 0.00024 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_n_30d | 0.00022 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| wind_weights_cold_start | 0.00020 | True | Ranked safe candidate |
| icon_wind_n_7d | 0.00019 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_n_90d | 0.00014 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_n_30d | 0.00005 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| archive_nominal_lead_hours | 0.00000 | False | Redundant horizon or raw calendar; use lead and cyclic time |
| best_weather_model_recent | 0.00000 | True | Ranked safe candidate |
| ecmwf_api_error | 0.00000 | False | Constant / near-constant on first training interval |
| ecmwf_available | 0.00000 | False | Constant / near-constant on first training interval |
| ecmwf_impossible_values_count | 0.00000 | False | Constant / near-constant on first training interval |
| ecmwf_missing_target_hour | 0.00000 | False | Constant / near-constant on first training interval |
| ecmwf_missing_values_count | 0.00000 | True | Ranked safe candidate |
| ecmwf_partial_coverage | 0.00000 | False | Constant / near-constant on first training interval |
| ecmwf_quality_ok | 0.00000 | False | Strongly correlated training-only proxy for ecmwf_missing_values_count |
| ecmwf_relative_humidity_2m_valid | 0.00000 | True | Ranked safe candidate |
| ecmwf_surface_pressure_valid | 0.00000 | False | Constant / near-constant on first training interval |
| ecmwf_temperature_2m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| ecmwf_wind_direction_100m_valid | 0.00000 | False | Strongly correlated training-only proxy for ecmwf_missing_values_count |
| ecmwf_wind_direction_10m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| ecmwf_wind_gusts_10m | 0.00000 | False | Excessive missingness on first training interval |
| ecmwf_wind_gusts_10m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| ecmwf_wind_speed_100m_valid | 0.00000 | False | Strongly correlated training-only proxy for ecmwf_missing_values_count |
| ecmwf_wind_speed_10m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_api_error | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_available | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_impossible_values_count | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_missing_target_hour | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_missing_values_count | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_partial_coverage | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_quality_ok | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_relative_humidity_2m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_surface_pressure_valid | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_temperature_2m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_temperature_n_7d | 0.00000 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_direction_100m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_wind_direction_10m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_wind_gusts_10m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_wind_speed_100m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| gfs_wind_speed_10m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| horizon_bucket | 0.00000 | False | Redundant horizon or raw calendar; use lead and cyclic time |
| icon_api_error | 0.00000 | False | Constant / near-constant on first training interval |
| icon_available | 0.00000 | False | Constant / near-constant on first training interval |
| icon_impossible_values_count | 0.00000 | False | Constant / near-constant on first training interval |
| icon_missing_target_hour | 0.00000 | False | Constant / near-constant on first training interval |
| icon_missing_values_count | 0.00000 | False | Constant / near-constant on first training interval |
| icon_partial_coverage | 0.00000 | False | Constant / near-constant on first training interval |
| icon_quality_ok | 0.00000 | False | Constant / near-constant on first training interval |
| icon_relative_humidity_2m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| icon_surface_pressure_valid | 0.00000 | False | Constant / near-constant on first training interval |
| icon_temperature_2m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| icon_temperature_n_7d | 0.00000 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_n_90d | 0.00000 | False | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_direction_100m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| icon_wind_direction_10m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| icon_wind_gusts_10m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| icon_wind_speed_100m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| icon_wind_speed_10m_valid | 0.00000 | False | Constant / near-constant on first training interval |
| temperature_weights_cold_start | 0.00000 | False | Constant / near-constant on first training interval |
| weather_critical_missing | 0.00000 | False | Constant / near-constant on first training interval |
| weather_data_quality_score | 0.00000 | False | Strongly correlated training-only proxy for ecmwf_missing_values_count |
| weather_models_available_count | 0.00000 | False | Constant / near-constant on first training interval |
| weather_models_usable_count | 0.00000 | False | Strongly correlated training-only proxy for ecmwf_missing_values_count |