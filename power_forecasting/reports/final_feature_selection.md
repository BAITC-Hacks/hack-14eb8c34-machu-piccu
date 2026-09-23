# Final feature selection

Final union: 15 features; per-route counts: {'D1__global': 15, 'D2__global': 15}. models/final_features.json contains only actual predictors.

Native final importance is descriptive, not the data used to select features. Selection ranking was fitted on first-fold historical train only; subset choice used aggregate walk-forward validation. Full206 remained a benchmark.

## CORE vs SELECTED vs FULL

| model | set_label | requested_feature_count | feature_count | validation_MAE | validation_RMSE | D1_MAE | D2_MAE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CatBoost | Top10 | 10 | 10 | 0.15556 | 0.23516 | 0.14705 | 0.16407 |
| CatBoost | Top15 | 15 | 15 | 0.15162 | 0.22904 | 0.14358 | 0.15965 |
| CatBoost | Top20 | 20 | 20 | 0.15317 | 0.23078 | 0.14483 | 0.16151 |
| CatBoost | CORE | 21 | 21 | 0.15708 | 0.23631 | 0.14852 | 0.16564 |
| CatBoost | SELECTED / Top30 | 30 | 30 | 0.15461 | 0.23244 | 0.14604 | 0.16317 |
| CatBoost | Top50 | 50 | 50 | 0.15451 | 0.23244 | 0.14620 | 0.16283 |
| CatBoost | FULL safe benchmark | 206 | 206 | 0.16159 | 0.23746 | 0.15331 | 0.16987 |
| LightGBM | Top10 | 10 | 10 | 0.15621 | 0.23442 | 0.14783 | 0.16460 |
| LightGBM | Top15 | 15 | 15 | 0.15054 | 0.22813 | 0.14234 | 0.15875 |
| LightGBM | Top20 | 20 | 20 | 0.15119 | 0.22866 | 0.14281 | 0.15957 |
| LightGBM | CORE | 21 | 21 | 0.15619 | 0.23436 | 0.14790 | 0.16447 |
| LightGBM | SELECTED / Top30 | 30 | 30 | 0.15218 | 0.23065 | 0.14331 | 0.16105 |
| LightGBM | Top50 | 50 | 50 | 0.15168 | 0.22786 | 0.14367 | 0.15968 |
| LightGBM | FULL safe benchmark | 206 | 206 | 0.15408 | 0.23039 | 0.14481 | 0.16334 |

## Selected features

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

## Removed safe candidates

| removed_feature | reason_for_removal |
| --- | --- |
| horizon_bucket | Redundant horizon or raw calendar; use lead and cyclic time |
| archive_nominal_lead_hours | Redundant horizon or raw calendar; use lead and cyclic time |
| ecmwf_wind_direction_10m | Raw angle replaced by sine/cosine |
| ecmwf_wind_direction_100m | Raw angle replaced by sine/cosine |
| ecmwf_temperature_2m | Not required by the chosen compact validation configuration |
| ecmwf_relative_humidity_2m | Not required by the chosen compact validation configuration |
| ecmwf_wind_gusts_10m | Excessive missingness on first training interval |
| ecmwf_api_error | Constant / near-constant on first training interval |
| ecmwf_missing_target_hour | Constant / near-constant on first training interval |
| gfs_wind_speed_10m | Not required by the chosen compact validation configuration |
| gfs_wind_speed_100m | Not required by the chosen compact validation configuration |
| gfs_wind_direction_10m | Raw angle replaced by sine/cosine |
| gfs_wind_direction_100m | Raw angle replaced by sine/cosine |
| gfs_temperature_2m | Strongly correlated training-only proxy for ecmwf_temperature_2m |
| gfs_surface_pressure | Strongly correlated training-only proxy for ecmwf_surface_pressure |
| gfs_wind_gusts_10m | Not required by the chosen compact validation configuration |
| gfs_api_error | Constant / near-constant on first training interval |
| gfs_missing_target_hour | Constant / near-constant on first training interval |
| icon_wind_speed_10m | Not required by the chosen compact validation configuration |
| icon_wind_direction_10m | Raw angle replaced by sine/cosine |
| icon_wind_direction_100m | Raw angle replaced by sine/cosine |
| icon_temperature_2m | Strongly correlated training-only proxy for ecmwf_temperature_2m |
| icon_surface_pressure | Strongly correlated training-only proxy for ecmwf_surface_pressure |
| icon_relative_humidity_2m | Not required by the chosen compact validation configuration |
| icon_api_error | Constant / near-constant on first training interval |
| icon_missing_target_hour | Constant / near-constant on first training interval |
| ecmwf_wind_speed_10m_valid | Constant / near-constant on first training interval |
| ecmwf_wind_speed_100m_valid | Strongly correlated training-only proxy for ecmwf_missing_values_count |
| ecmwf_wind_direction_10m_valid | Constant / near-constant on first training interval |
| ecmwf_wind_direction_100m_valid | Strongly correlated training-only proxy for ecmwf_missing_values_count |
| ecmwf_temperature_2m_valid | Constant / near-constant on first training interval |
| ecmwf_surface_pressure_valid | Constant / near-constant on first training interval |
| ecmwf_relative_humidity_2m_valid | Not required by the chosen compact validation configuration |
| ecmwf_wind_gusts_10m_valid | Constant / near-constant on first training interval |
| ecmwf_available | Constant / near-constant on first training interval |
| ecmwf_missing_values_count | Not required by the chosen compact validation configuration |
| ecmwf_impossible_values_count | Constant / near-constant on first training interval |
| ecmwf_partial_coverage | Constant / near-constant on first training interval |
| ecmwf_quality_ok | Strongly correlated training-only proxy for ecmwf_missing_values_count |
| gfs_wind_speed_10m_valid | Constant / near-constant on first training interval |
| gfs_wind_speed_100m_valid | Constant / near-constant on first training interval |
| gfs_wind_direction_10m_valid | Constant / near-constant on first training interval |
| gfs_wind_direction_100m_valid | Constant / near-constant on first training interval |
| gfs_temperature_2m_valid | Constant / near-constant on first training interval |
| gfs_surface_pressure_valid | Constant / near-constant on first training interval |
| gfs_relative_humidity_2m_valid | Constant / near-constant on first training interval |
| gfs_wind_gusts_10m_valid | Constant / near-constant on first training interval |
| gfs_available | Constant / near-constant on first training interval |
| gfs_missing_values_count | Constant / near-constant on first training interval |
| gfs_impossible_values_count | Constant / near-constant on first training interval |
| gfs_partial_coverage | Constant / near-constant on first training interval |
| gfs_quality_ok | Constant / near-constant on first training interval |
| icon_wind_speed_10m_valid | Constant / near-constant on first training interval |
| icon_wind_speed_100m_valid | Constant / near-constant on first training interval |
| icon_wind_direction_10m_valid | Constant / near-constant on first training interval |
| icon_wind_direction_100m_valid | Constant / near-constant on first training interval |
| icon_temperature_2m_valid | Constant / near-constant on first training interval |
| icon_surface_pressure_valid | Constant / near-constant on first training interval |
| icon_relative_humidity_2m_valid | Constant / near-constant on first training interval |
| icon_wind_gusts_10m_valid | Constant / near-constant on first training interval |
| icon_available | Constant / near-constant on first training interval |
| icon_missing_values_count | Constant / near-constant on first training interval |
| icon_impossible_values_count | Constant / near-constant on first training interval |
| icon_partial_coverage | Constant / near-constant on first training interval |
| icon_quality_ok | Constant / near-constant on first training interval |
| weather_models_available_count | Constant / near-constant on first training interval |
| weather_models_usable_count | Strongly correlated training-only proxy for ecmwf_missing_values_count |
| weather_data_quality_score | Strongly correlated training-only proxy for ecmwf_missing_values_count |
| weather_critical_missing | Constant / near-constant on first training interval |
| ecmwf_wind_mae_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_rmse_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_bias_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_n_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_mae_30d | Not required by the chosen compact validation configuration |
| ecmwf_wind_rmse_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_bias_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_n_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_mae_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_rmse_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_bias_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_wind_n_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_mae_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_rmse_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_bias_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_n_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_mae_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_rmse_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_bias_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_n_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_mae_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_rmse_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_bias_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| ecmwf_temperature_n_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_mae_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_rmse_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_bias_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_n_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_mae_30d | Not required by the chosen compact validation configuration |
| gfs_wind_rmse_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_bias_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_n_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_mae_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_rmse_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_bias_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_wind_n_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_mae_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_rmse_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_bias_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_n_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_mae_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_rmse_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_bias_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_n_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_mae_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_rmse_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_bias_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| gfs_temperature_n_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_mae_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_rmse_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_bias_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_n_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_mae_30d | Not required by the chosen compact validation configuration |
| icon_wind_rmse_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_bias_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_n_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_mae_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_rmse_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_bias_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_wind_n_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_mae_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_rmse_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_bias_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_n_7d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_mae_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_rmse_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_bias_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_n_30d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_mae_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_rmse_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_bias_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| icon_temperature_n_90d | Redundant rolling metric; retain only provider wind MAE 30d |
| wind_weights_cold_start | Not required by the chosen compact validation configuration |
| ecmwf_weight | Not required by the chosen compact validation configuration |
| gfs_weight | Not required by the chosen compact validation configuration |
| icon_weight | Not required by the chosen compact validation configuration |
| best_weather_model_recent | Not required by the chosen compact validation configuration |
| temperature_weights_cold_start | Constant / near-constant on first training interval |
| ecmwf_temperature_weight | Not required by the chosen compact validation configuration |
| gfs_temperature_weight | Not required by the chosen compact validation configuration |
| icon_temperature_weight | Not required by the chosen compact validation configuration |
| ensemble_wind_speed_10m | Strongly correlated training-only proxy for wind_speed_10m_mean |
| wind_speed_models_std | Not required by the chosen compact validation configuration |
| wind_speed_models_range | Strongly correlated training-only proxy for wind_speed_models_std |
| wind_speed_100m_mean | Strongly correlated training-only proxy for ensemble_wind_speed_100m |
| wind_direction_10m_circular_dispersion | Not required by the chosen compact validation configuration |
| ensemble_wind_direction_10m_circular_dispersion | Strongly correlated training-only proxy for wind_direction_10m_circular_dispersion |
| wind_direction_10m_mean | Raw angle replaced by sine/cosine |
| ensemble_wind_direction_10m | Raw angle replaced by sine/cosine |
| wind_direction_100m_circular_dispersion | Strongly correlated training-only proxy for ensemble_wind_direction_100m_circular_dispersion |
| ensemble_wind_direction_100m_circular_dispersion | Not required by the chosen compact validation configuration |
| wind_direction_100m_mean | Raw angle replaced by sine/cosine |
| ensemble_wind_direction_100m | Raw angle replaced by sine/cosine |
| temperature_models_std | Not required by the chosen compact validation configuration |
| temperature_models_range | Strongly correlated training-only proxy for temperature_models_std |
| temperature_2m_mean | Strongly correlated training-only proxy for ecmwf_temperature_2m |
| ensemble_temperature_2m | Strongly correlated training-only proxy for ecmwf_temperature_2m |
| surface_pressure_mean | Strongly correlated training-only proxy for ecmwf_surface_pressure |
| ensemble_surface_pressure | Strongly correlated training-only proxy for ecmwf_surface_pressure |
| relative_humidity_2m_mean | Strongly correlated training-only proxy for ensemble_relative_humidity_2m |
| ensemble_relative_humidity_2m | Not required by the chosen compact validation configuration |
| wind_gusts_10m_mean | Strongly correlated training-only proxy for ensemble_wind_gusts_10m |
| ensemble_wind_gusts_10m | Not required by the chosen compact validation configuration |
| target_hour | Redundant horizon or raw calendar; use lead and cyclic time |
| target_day_of_week | Redundant horizon or raw calendar; use lead and cyclic time |
| target_month | Redundant horizon or raw calendar; use lead and cyclic time |
| target_day_of_year | Redundant horizon or raw calendar; use lead and cyclic time |
| hour_cos | Not required by the chosen compact validation configuration |
| ecmwf_wind_direction_10m_sin | Not required by the chosen compact validation configuration |
| ecmwf_wind_direction_10m_cos | Not required by the chosen compact validation configuration |
| ecmwf_wind_direction_100m_sin | Not required by the chosen compact validation configuration |
| ecmwf_wind_direction_100m_cos | Not required by the chosen compact validation configuration |
| gfs_wind_direction_10m_sin | Not required by the chosen compact validation configuration |
| gfs_wind_direction_100m_cos | Not required by the chosen compact validation configuration |
| icon_wind_direction_10m_sin | Not required by the chosen compact validation configuration |
| icon_wind_direction_10m_cos | Not required by the chosen compact validation configuration |
| icon_wind_direction_100m_sin | Not required by the chosen compact validation configuration |
| icon_wind_direction_100m_cos | Not required by the chosen compact validation configuration |
| ensemble_wind_direction_10m_sin | Not required by the chosen compact validation configuration |
| ensemble_wind_direction_10m_cos | Not required by the chosen compact validation configuration |
| ensemble_wind_direction_100m_sin | Not required by the chosen compact validation configuration |
| ensemble_wind_direction_100m_cos | Not required by the chosen compact validation configuration |

Unsafe/technical columns excluded before selection are listed separately in feature_safety_report.md and ml_excluded_features.csv. Small measured gains do not establish statistical significance.
