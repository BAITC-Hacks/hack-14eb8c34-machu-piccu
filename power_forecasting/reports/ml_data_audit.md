# ML data audit

Train: (64503, 262); competition: (2688, 261). Target: normalized_active_power. Upstream safe candidates: 206; compact CORE: 21.

Duplicate full rows: 0; duplicate forecast keys: 0. Unique turbine/target observations: 32263. The same target legitimately appears in D1 and D2; folds split by target time for all turbines.

Target is named normalized active power in source and bounded in BOTH filtered training and unfiltered prepared hourly SCADA. Clipping [0,1] is supported by observed range, not proof of the operator's normalization convention. Nameplate capacity is unavailable.

Unfiltered hourly range: 0.00166667–0.99833333.

## Target distribution (forecast rows)

| statistic | value |
| --- | --- |
| count | 64503.00000 |
| mean | 0.36156 |
| std | 0.35539 |
| min | 0.00167 |
| 1% | 0.00833 |
| 10% | 0.01000 |
| 50% | 0.22500 |
| 90% | 0.96500 |
| 99% | 0.99000 |
| max | 0.99833 |

## Turbine / horizon counts

| turbine_id | horizon_bucket | rows |
| --- | --- | --- |
| turbine_1 | D1 | 15498 |
| turbine_1 | D2 | 15476 |
| turbine_2 | D1 | 16765 |
| turbine_2 | D2 | 16764 |

## Per lead hour

| lead_hours | rows |
| --- | --- |
| 1 | 1359 |
| 2 | 1361 |
| 3 | 1360 |
| 4 | 1359 |
| 5 | 1358 |
| 6 | 1356 |
| 7 | 1350 |
| 8 | 1344 |
| 9 | 1347 |
| 10 | 1330 |
| 11 | 1319 |
| 12 | 1309 |
| 13 | 1312 |
| 14 | 1318 |
| 15 | 1324 |
| 16 | 1330 |
| 17 | 1337 |
| 18 | 1345 |
| 19 | 1350 |
| 20 | 1358 |
| 21 | 1358 |
| 22 | 1360 |
| 23 | 1360 |
| 24 | 1359 |
| 25 | 1358 |
| 26 | 1360 |
| 27 | 1359 |
| 28 | 1358 |
| 29 | 1357 |
| 30 | 1355 |
| 31 | 1349 |
| 32 | 1343 |
| 33 | 1346 |
| 34 | 1329 |
| 35 | 1317 |
| 36 | 1308 |
| 37 | 1312 |
| 38 | 1318 |
| 39 | 1323 |
| 40 | 1329 |
| 41 | 1336 |
| 42 | 1344 |
| 43 | 1349 |
| 44 | 1357 |
| 45 | 1357 |
| 46 | 1359 |
| 47 | 1359 |
| 48 | 1358 |

## Calendar coverage

| target_local_time | rows | first | last |
| --- | --- | --- | --- |
| 2024-02 | 1211 | 2024-02-16 11:00:00 | 2024-02-29 23:00:00 |
| 2024-03 | 2976 | 2024-03-01 00:00:00 | 2024-03-31 23:00:00 |
| 2024-04 | 2852 | 2024-04-01 00:00:00 | 2024-04-30 23:00:00 |
| 2024-05 | 2156 | 2024-05-01 00:00:00 | 2024-05-31 23:00:00 |
| 2024-06 | 1408 | 2024-06-01 00:00:00 | 2024-06-30 23:00:00 |
| 2024-07 | 2088 | 2024-07-01 00:00:00 | 2024-07-31 23:00:00 |
| 2024-08 | 2942 | 2024-08-01 00:00:00 | 2024-08-31 23:00:00 |
| 2024-09 | 2866 | 2024-09-01 00:00:00 | 2024-09-30 23:00:00 |
| 2024-10 | 2900 | 2024-10-01 00:00:00 | 2024-10-31 23:00:00 |
| 2024-11 | 2880 | 2024-11-01 00:00:00 | 2024-11-30 23:00:00 |
| 2024-12 | 2964 | 2024-12-01 00:00:00 | 2024-12-31 23:00:00 |
| 2025-01 | 2976 | 2025-01-01 00:00:00 | 2025-01-31 23:00:00 |
| 2025-02 | 2660 | 2025-02-01 00:00:00 | 2025-02-28 23:00:00 |
| 2025-03 | 2910 | 2025-03-01 00:00:00 | 2025-03-31 23:00:00 |
| 2025-04 | 2750 | 2025-04-01 00:00:00 | 2025-04-30 23:00:00 |
| 2025-05 | 2816 | 2025-05-01 00:00:00 | 2025-05-31 23:00:00 |
| 2025-06 | 2828 | 2025-06-01 00:00:00 | 2025-06-30 23:00:00 |
| 2025-07 | 2944 | 2025-07-01 00:00:00 | 2025-07-31 23:00:00 |
| 2025-08 | 2948 | 2025-08-01 00:00:00 | 2025-08-31 23:00:00 |
| 2025-09 | 2876 | 2025-09-01 00:00:00 | 2025-09-30 23:00:00 |
| 2025-10 | 2748 | 2025-10-01 00:00:00 | 2025-10-31 23:00:00 |
| 2025-11 | 2880 | 2025-11-01 00:00:00 | 2025-11-30 23:00:00 |
| 2025-12 | 2948 | 2025-12-01 00:00:00 | 2025-12-31 23:00:00 |
| 2026-01 | 2976 | 2026-01-01 00:00:00 | 2026-01-31 23:00:00 |

## All columns, dtypes and missingness

| column | dtype | missing_n | missing_pct |
| --- | --- | --- | --- |
| forecast_issue_time | datetime64[us, UTC] | 0 | 0.00000 |
| lead_hours | int64 | 0 | 0.00000 |
| target_time | datetime64[us, UTC] | 0 | 0.00000 |
| archive_day | int64 | 0 | 0.00000 |
| forecast_day | int64 | 0 | 0.00000 |
| horizon_bucket | str | 0 | 0.00000 |
| target_local_time | datetime64[us] | 0 | 0.00000 |
| archive_nominal_lead_hours | int64 | 0 | 0.00000 |
| archive_reference_time | datetime64[us, UTC] | 0 | 0.00000 |
| dataset_split | str | 0 | 0.00000 |
| turbine_id | str | 0 | 0.00000 |
| ecmwf_wind_speed_10m | float64 | 0 | 0.00000 |
| ecmwf_wind_speed_100m | float64 | 1831 | 2.83863 |
| ecmwf_wind_direction_10m | float64 | 0 | 0.00000 |
| ecmwf_wind_direction_100m | float64 | 1831 | 2.83863 |
| ecmwf_temperature_2m | float64 | 0 | 0.00000 |
| ecmwf_surface_pressure | float64 | 0 | 0.00000 |
| ecmwf_relative_humidity_2m | float64 | 1255 | 1.94565 |
| ecmwf_wind_gusts_10m | float64 | 64503 | 100.00000 |
| ecmwf_api_error | bool | 0 | 0.00000 |
| ecmwf_missing_target_hour | bool | 0 | 0.00000 |
| ecmwf_cache_key | str | 0 | 0.00000 |
| ecmwf_grid_latitude | float64 | 0 | 0.00000 |
| ecmwf_grid_longitude | float64 | 0 | 0.00000 |
| gfs_wind_speed_10m | float64 | 0 | 0.00000 |
| gfs_wind_speed_100m | float64 | 0 | 0.00000 |
| gfs_wind_direction_10m | float64 | 0 | 0.00000 |
| gfs_wind_direction_100m | float64 | 0 | 0.00000 |
| gfs_temperature_2m | float64 | 0 | 0.00000 |
| gfs_surface_pressure | float64 | 0 | 0.00000 |
| gfs_relative_humidity_2m | float64 | 0 | 0.00000 |
| gfs_wind_gusts_10m | float64 | 0 | 0.00000 |
| gfs_api_error | bool | 0 | 0.00000 |
| gfs_missing_target_hour | bool | 0 | 0.00000 |
| gfs_cache_key | str | 0 | 0.00000 |
| gfs_grid_latitude | float64 | 0 | 0.00000 |
| gfs_grid_longitude | float64 | 0 | 0.00000 |
| icon_wind_speed_10m | float64 | 0 | 0.00000 |
| icon_wind_speed_100m | float64 | 11 | 0.01705 |
| icon_wind_direction_10m | float64 | 0 | 0.00000 |
| icon_wind_direction_100m | float64 | 11 | 0.01705 |
| icon_temperature_2m | float64 | 0 | 0.00000 |
| icon_surface_pressure | float64 | 0 | 0.00000 |
| icon_relative_humidity_2m | float64 | 0 | 0.00000 |
| icon_wind_gusts_10m | float64 | 0 | 0.00000 |
| icon_api_error | bool | 0 | 0.00000 |
| icon_missing_target_hour | bool | 0 | 0.00000 |
| icon_cache_key | str | 0 | 0.00000 |
| icon_grid_latitude | float64 | 0 | 0.00000 |
| icon_grid_longitude | float64 | 0 | 0.00000 |
| methodology_status | str | 0 | 0.00000 |
| weather_archive_method | str | 0 | 0.00000 |
| weather_archive_confidence | str | 0 | 0.00000 |
| timezone_status | str | 0 | 0.00000 |
| scada_utc_offset_hours | int64 | 0 | 0.00000 |
| weather_configuration | str | 0 | 0.00000 |
| ecmwf_wind_speed_10m_valid | bool | 0 | 0.00000 |
| ecmwf_wind_speed_100m_valid | bool | 0 | 0.00000 |
| ecmwf_wind_direction_10m_valid | bool | 0 | 0.00000 |
| ecmwf_wind_direction_100m_valid | bool | 0 | 0.00000 |
| ecmwf_temperature_2m_valid | bool | 0 | 0.00000 |
| ecmwf_surface_pressure_valid | bool | 0 | 0.00000 |
| ecmwf_relative_humidity_2m_valid | bool | 0 | 0.00000 |
| ecmwf_wind_gusts_10m_valid | bool | 0 | 0.00000 |
| ecmwf_available | bool | 0 | 0.00000 |
| ecmwf_missing_values_count | int8 | 0 | 0.00000 |
| ecmwf_impossible_values_count | int8 | 0 | 0.00000 |
| ecmwf_partial_coverage | bool | 0 | 0.00000 |
| ecmwf_quality_ok | bool | 0 | 0.00000 |
| ecmwf_duplicate_forecast | bool | 0 | 0.00000 |
| ecmwf_timestamps_consistent | bool | 0 | 0.00000 |
| ecmwf_run_time | datetime64[ns, UTC] | 64503 | 100.00000 |
| ecmwf_estimated_availability_time | datetime64[ns, UTC] | 64503 | 100.00000 |
| ecmwf_stale_run | boolean | 64503 | 100.00000 |
| gfs_wind_speed_10m_valid | bool | 0 | 0.00000 |
| gfs_wind_speed_100m_valid | bool | 0 | 0.00000 |
| gfs_wind_direction_10m_valid | bool | 0 | 0.00000 |
| gfs_wind_direction_100m_valid | bool | 0 | 0.00000 |
| gfs_temperature_2m_valid | bool | 0 | 0.00000 |
| gfs_surface_pressure_valid | bool | 0 | 0.00000 |
| gfs_relative_humidity_2m_valid | bool | 0 | 0.00000 |
| gfs_wind_gusts_10m_valid | bool | 0 | 0.00000 |
| gfs_available | bool | 0 | 0.00000 |
| gfs_missing_values_count | int8 | 0 | 0.00000 |
| gfs_impossible_values_count | int8 | 0 | 0.00000 |
| gfs_partial_coverage | bool | 0 | 0.00000 |
| gfs_quality_ok | bool | 0 | 0.00000 |
| gfs_duplicate_forecast | bool | 0 | 0.00000 |
| gfs_timestamps_consistent | bool | 0 | 0.00000 |
| gfs_run_time | datetime64[ns, UTC] | 64503 | 100.00000 |
| gfs_estimated_availability_time | datetime64[ns, UTC] | 64503 | 100.00000 |
| gfs_stale_run | boolean | 64503 | 100.00000 |
| icon_wind_speed_10m_valid | bool | 0 | 0.00000 |
| icon_wind_speed_100m_valid | bool | 0 | 0.00000 |
| icon_wind_direction_10m_valid | bool | 0 | 0.00000 |
| icon_wind_direction_100m_valid | bool | 0 | 0.00000 |
| icon_temperature_2m_valid | bool | 0 | 0.00000 |
| icon_surface_pressure_valid | bool | 0 | 0.00000 |
| icon_relative_humidity_2m_valid | bool | 0 | 0.00000 |
| icon_wind_gusts_10m_valid | bool | 0 | 0.00000 |
| icon_available | bool | 0 | 0.00000 |
| icon_missing_values_count | int8 | 0 | 0.00000 |
| icon_impossible_values_count | int8 | 0 | 0.00000 |
| icon_partial_coverage | bool | 0 | 0.00000 |
| icon_quality_ok | bool | 0 | 0.00000 |
| icon_duplicate_forecast | bool | 0 | 0.00000 |
| icon_timestamps_consistent | bool | 0 | 0.00000 |
| icon_run_time | datetime64[ns, UTC] | 64503 | 100.00000 |
| icon_estimated_availability_time | datetime64[ns, UTC] | 64503 | 100.00000 |
| icon_stale_run | boolean | 64503 | 100.00000 |
| weather_models_available_count | int8 | 0 | 0.00000 |
| weather_models_usable_count | int8 | 0 | 0.00000 |
| weather_data_quality_score | float64 | 0 | 0.00000 |
| weather_critical_missing | bool | 0 | 0.00000 |
| ecmwf_wind_mae_7d | float64 | 2173 | 3.36884 |
| ecmwf_wind_rmse_7d | float64 | 2173 | 3.36884 |
| ecmwf_wind_bias_7d | float64 | 2173 | 3.36884 |
| ecmwf_wind_n_7d | float64 | 0 | 0.00000 |
| ecmwf_wind_history_latest_7d | datetime64[ns, UTC] | 2173 | 3.36884 |
| ecmwf_wind_mae_30d | float64 | 2173 | 3.36884 |
| ecmwf_wind_rmse_30d | float64 | 2173 | 3.36884 |
| ecmwf_wind_bias_30d | float64 | 2173 | 3.36884 |
| ecmwf_wind_n_30d | float64 | 0 | 0.00000 |
| ecmwf_wind_history_latest_30d | datetime64[ns, UTC] | 2173 | 3.36884 |
| ecmwf_wind_mae_90d | float64 | 2079 | 3.22311 |
| ecmwf_wind_rmse_90d | float64 | 2079 | 3.22311 |
| ecmwf_wind_bias_90d | float64 | 2079 | 3.22311 |
| ecmwf_wind_n_90d | float64 | 0 | 0.00000 |
| ecmwf_wind_history_latest_90d | datetime64[ns, UTC] | 2079 | 3.22311 |
| ecmwf_temperature_mae_7d | float64 | 94 | 0.14573 |
| ecmwf_temperature_rmse_7d | float64 | 94 | 0.14573 |
| ecmwf_temperature_bias_7d | float64 | 94 | 0.14573 |
| ecmwf_temperature_n_7d | float64 | 0 | 0.00000 |
| ecmwf_temperature_history_latest_7d | datetime64[ns, UTC] | 94 | 0.14573 |
| ecmwf_temperature_mae_30d | float64 | 94 | 0.14573 |
| ecmwf_temperature_rmse_30d | float64 | 94 | 0.14573 |
| ecmwf_temperature_bias_30d | float64 | 94 | 0.14573 |
| ecmwf_temperature_n_30d | float64 | 0 | 0.00000 |
| ecmwf_temperature_history_latest_30d | datetime64[ns, UTC] | 94 | 0.14573 |
| ecmwf_temperature_mae_90d | float64 | 0 | 0.00000 |
| ecmwf_temperature_rmse_90d | float64 | 0 | 0.00000 |
| ecmwf_temperature_bias_90d | float64 | 0 | 0.00000 |
| ecmwf_temperature_n_90d | float64 | 0 | 0.00000 |
| ecmwf_temperature_history_latest_90d | datetime64[ns, UTC] | 0 | 0.00000 |
| gfs_wind_mae_7d | float64 | 277 | 0.42944 |
| gfs_wind_rmse_7d | float64 | 277 | 0.42944 |
| gfs_wind_bias_7d | float64 | 277 | 0.42944 |
| gfs_wind_n_7d | float64 | 0 | 0.00000 |
| gfs_wind_history_latest_7d | datetime64[ns, UTC] | 277 | 0.42944 |
| gfs_wind_mae_30d | float64 | 277 | 0.42944 |
| gfs_wind_rmse_30d | float64 | 277 | 0.42944 |
| gfs_wind_bias_30d | float64 | 277 | 0.42944 |
| gfs_wind_n_30d | float64 | 0 | 0.00000 |
| gfs_wind_history_latest_30d | datetime64[ns, UTC] | 277 | 0.42944 |
| gfs_wind_mae_90d | float64 | 183 | 0.28371 |
| gfs_wind_rmse_90d | float64 | 183 | 0.28371 |
| gfs_wind_bias_90d | float64 | 183 | 0.28371 |
| gfs_wind_n_90d | float64 | 0 | 0.00000 |
| gfs_wind_history_latest_90d | datetime64[ns, UTC] | 183 | 0.28371 |
| gfs_temperature_mae_7d | float64 | 94 | 0.14573 |
| gfs_temperature_rmse_7d | float64 | 94 | 0.14573 |
| gfs_temperature_bias_7d | float64 | 94 | 0.14573 |
| gfs_temperature_n_7d | float64 | 0 | 0.00000 |
| gfs_temperature_history_latest_7d | datetime64[ns, UTC] | 94 | 0.14573 |
| gfs_temperature_mae_30d | float64 | 94 | 0.14573 |
| gfs_temperature_rmse_30d | float64 | 94 | 0.14573 |
| gfs_temperature_bias_30d | float64 | 94 | 0.14573 |
| gfs_temperature_n_30d | float64 | 0 | 0.00000 |
| gfs_temperature_history_latest_30d | datetime64[ns, UTC] | 94 | 0.14573 |
| gfs_temperature_mae_90d | float64 | 0 | 0.00000 |
| gfs_temperature_rmse_90d | float64 | 0 | 0.00000 |
| gfs_temperature_bias_90d | float64 | 0 | 0.00000 |
| gfs_temperature_n_90d | float64 | 0 | 0.00000 |
| gfs_temperature_history_latest_90d | datetime64[ns, UTC] | 0 | 0.00000 |
| icon_wind_mae_7d | float64 | 277 | 0.42944 |
| icon_wind_rmse_7d | float64 | 277 | 0.42944 |
| icon_wind_bias_7d | float64 | 277 | 0.42944 |
| icon_wind_n_7d | float64 | 0 | 0.00000 |
| icon_wind_history_latest_7d | datetime64[ns, UTC] | 277 | 0.42944 |
| icon_wind_mae_30d | float64 | 277 | 0.42944 |
| icon_wind_rmse_30d | float64 | 277 | 0.42944 |
| icon_wind_bias_30d | float64 | 277 | 0.42944 |
| icon_wind_n_30d | float64 | 0 | 0.00000 |
| icon_wind_history_latest_30d | datetime64[ns, UTC] | 277 | 0.42944 |
| icon_wind_mae_90d | float64 | 183 | 0.28371 |
| icon_wind_rmse_90d | float64 | 183 | 0.28371 |
| icon_wind_bias_90d | float64 | 183 | 0.28371 |
| icon_wind_n_90d | float64 | 0 | 0.00000 |
| icon_wind_history_latest_90d | datetime64[ns, UTC] | 183 | 0.28371 |
| icon_temperature_mae_7d | float64 | 94 | 0.14573 |
| icon_temperature_rmse_7d | float64 | 94 | 0.14573 |
| icon_temperature_bias_7d | float64 | 94 | 0.14573 |
| icon_temperature_n_7d | float64 | 0 | 0.00000 |
| icon_temperature_history_latest_7d | datetime64[ns, UTC] | 94 | 0.14573 |
| icon_temperature_mae_30d | float64 | 94 | 0.14573 |
| icon_temperature_rmse_30d | float64 | 94 | 0.14573 |
| icon_temperature_bias_30d | float64 | 94 | 0.14573 |
| icon_temperature_n_30d | float64 | 0 | 0.00000 |
| icon_temperature_history_latest_30d | datetime64[ns, UTC] | 94 | 0.14573 |
| icon_temperature_mae_90d | float64 | 0 | 0.00000 |
| icon_temperature_rmse_90d | float64 | 0 | 0.00000 |
| icon_temperature_bias_90d | float64 | 0 | 0.00000 |
| icon_temperature_n_90d | float64 | 0 | 0.00000 |
| icon_temperature_history_latest_90d | datetime64[ns, UTC] | 0 | 0.00000 |
| wind_weights_cold_start | bool | 0 | 0.00000 |
| ecmwf_weight | float64 | 0 | 0.00000 |
| gfs_weight | float64 | 0 | 0.00000 |
| icon_weight | float64 | 0 | 0.00000 |
| best_weather_model_recent | str | 0 | 0.00000 |
| temperature_weights_cold_start | bool | 0 | 0.00000 |
| ecmwf_temperature_weight | float64 | 0 | 0.00000 |
| gfs_temperature_weight | float64 | 0 | 0.00000 |
| icon_temperature_weight | float64 | 0 | 0.00000 |
| wind_speed_10m_mean | float64 | 0 | 0.00000 |
| ensemble_wind_speed_10m | float64 | 0 | 0.00000 |
| wind_speed_models_std | float64 | 0 | 0.00000 |
| wind_speed_models_range | float64 | 0 | 0.00000 |
| wind_speed_100m_mean | float64 | 0 | 0.00000 |
| ensemble_wind_speed_100m | float64 | 0 | 0.00000 |
| wind_direction_10m_circular_dispersion | float64 | 0 | 0.00000 |
| ensemble_wind_direction_10m_circular_dispersion | float64 | 0 | 0.00000 |
| wind_direction_10m_mean | float64 | 0 | 0.00000 |
| ensemble_wind_direction_10m | float64 | 0 | 0.00000 |
| wind_direction_100m_circular_dispersion | float64 | 0 | 0.00000 |
| ensemble_wind_direction_100m_circular_dispersion | float64 | 0 | 0.00000 |
| wind_direction_100m_mean | float64 | 0 | 0.00000 |
| ensemble_wind_direction_100m | float64 | 0 | 0.00000 |
| temperature_models_std | float64 | 0 | 0.00000 |
| temperature_models_range | float64 | 0 | 0.00000 |
| temperature_2m_mean | float64 | 0 | 0.00000 |
| ensemble_temperature_2m | float64 | 0 | 0.00000 |
| surface_pressure_mean | float64 | 0 | 0.00000 |
| ensemble_surface_pressure | float64 | 0 | 0.00000 |
| relative_humidity_2m_mean | float64 | 0 | 0.00000 |
| ensemble_relative_humidity_2m | float64 | 0 | 0.00000 |
| wind_gusts_10m_mean | float64 | 0 | 0.00000 |
| ensemble_wind_gusts_10m | float64 | 0 | 0.00000 |
| target_hour | int32 | 0 | 0.00000 |
| target_day_of_week | int32 | 0 | 0.00000 |
| target_month | int32 | 0 | 0.00000 |
| target_day_of_year | int32 | 0 | 0.00000 |
| hour_sin | float64 | 0 | 0.00000 |
| hour_cos | float64 | 0 | 0.00000 |
| day_of_year_sin | float64 | 0 | 0.00000 |
| day_of_year_cos | float64 | 0 | 0.00000 |
| ecmwf_wind_direction_10m_sin | float64 | 0 | 0.00000 |
| ecmwf_wind_direction_10m_cos | float64 | 0 | 0.00000 |
| ecmwf_wind_direction_100m_sin | float64 | 1831 | 2.83863 |
| ecmwf_wind_direction_100m_cos | float64 | 1831 | 2.83863 |
| gfs_wind_direction_10m_sin | float64 | 0 | 0.00000 |
| gfs_wind_direction_10m_cos | float64 | 0 | 0.00000 |
| gfs_wind_direction_100m_sin | float64 | 0 | 0.00000 |
| gfs_wind_direction_100m_cos | float64 | 0 | 0.00000 |
| icon_wind_direction_10m_sin | float64 | 0 | 0.00000 |
| icon_wind_direction_10m_cos | float64 | 0 | 0.00000 |
| icon_wind_direction_100m_sin | float64 | 11 | 0.01705 |
| icon_wind_direction_100m_cos | float64 | 11 | 0.01705 |
| ensemble_wind_direction_10m_sin | float64 | 0 | 0.00000 |
| ensemble_wind_direction_10m_cos | float64 | 0 | 0.00000 |
| ensemble_wind_direction_100m_sin | float64 | 0 | 0.00000 |
| ensemble_wind_direction_100m_cos | float64 | 0 | 0.00000 |
| normalized_active_power | float64 | 0 | 0.00000 |

Evaluation-only/provenance columns are identified in feature_safety_report.md. Offline February file is never loaded by ML training or selection.
