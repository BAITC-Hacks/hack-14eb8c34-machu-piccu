# Итоговый ML-отчёт: прогноз нормализованной мощности

Проверка завершения: 42 теста пройдены. Повторное обучение финальных checkpoints и отдельный `predict.py` дали идентичный Parquet-прогноз по SHA-256; подробности в ml_reproducibility.md.

| Configuration | MAE | RMSE | nMAE | Bias | MAE_D1 | MAE_D2 |
| --- | --- | --- | --- | --- | --- | --- |
| Selected routing policy | 0.15054 | 0.22813 | 0.15054 | 0.01072 | 0.14234 | 0.15875 |
| LightGBM__Top15__global__default | 0.15054 | 0.22813 | 0.15054 | 0.01072 | 0.14234 | 0.15875 |
| LightGBM__Top15__turbine__default | 0.15058 | 0.22818 | 0.15058 | 0.00968 | 0.14265 | 0.15851 |
| LightGBM__Top20__global__default | 0.15119 | 0.22866 | 0.15119 | 0.01376 | 0.14281 | 0.15957 |
| LightGBM__Top15__horizon_turbine__default | 0.15121 | 0.22855 | 0.15121 | 0.01044 | 0.14232 | 0.16010 |
| LightGBM__Top20__global__richer | 0.15128 | 0.22817 | 0.15128 | 0.01190 | 0.14315 | 0.15941 |
| LightGBM__Top15__global__richer | 0.15134 | 0.22887 | 0.15134 | 0.01149 | 0.14335 | 0.15934 |
| LightGBM__Top15__global__regularized | 0.15138 | 0.22984 | 0.15138 | 0.01489 | 0.14313 | 0.15963 |
| CatBoost__Top15__global__default | 0.15162 | 0.22904 | 0.15162 | 0.02139 | 0.14358 | 0.15965 |
| LightGBM__Top50__global__default | 0.15168 | 0.22786 | 0.15168 | 0.01148 | 0.14367 | 0.15968 |
| LightGBM__Top15__horizon__default | 0.15173 | 0.22845 | 0.15173 | 0.01150 | 0.14283 | 0.16063 |

## 1. Dataset

64,503 строк обучения; 2,688 competition-строк; две турбины. Target: normalized_active_power. Источники Parquet не изменены. Offline February файл не загружался для обучения или отбора. Диапазон target подтверждён также по исходному подготовленному hourly SCADA. Подробности: ml_data_audit.md.

## 2. Validation methodology

Последние четыре календарных месяца с достаточным покрытием выбраны автоматически. Split по target_time одновременно для всех турбин и D1/D2. Перед каждым месяцем модель обучается только на метках, доступных строго раньше самого раннего forecast_issue_time этого месяца; пограничные часы исключены. Параметры early stopping определяются во внутреннем последнем 21-дневном участке прошлого с дополнительным availability purge; затем модель переобучается на всём разрешённом outer train. Outer validation не используется для early stopping.

| fold | train_rows | validation_rows | train_max_target | train_max_available | validation_min_target | validation_max_target | first_forecast_issue | history_target_cutoff | purged_boundary_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-10 | 52751 | 2748 | 2025-09-28 16:00:00+00:00 | 2025-09-28 18:00:00+00:00 | 2025-09-30 19:00:00+00:00 | 2025-10-31 18:00:00+00:00 | 2025-09-28 19:00:00+00:00 | 2025-09-30 19:00:00+00:00 | 200 |
| 2025-11 | 55499 | 2880 | 2025-10-29 16:00:00+00:00 | 2025-10-29 18:00:00+00:00 | 2025-10-31 19:00:00+00:00 | 2025-11-30 18:00:00+00:00 | 2025-10-29 19:00:00+00:00 | 2025-10-31 19:00:00+00:00 | 200 |
| 2025-12 | 58379 | 2948 | 2025-11-28 16:00:00+00:00 | 2025-11-28 18:00:00+00:00 | 2025-11-30 19:00:00+00:00 | 2025-12-31 18:00:00+00:00 | 2025-11-28 19:00:00+00:00 | 2025-11-30 19:00:00+00:00 | 200 |
| 2026-01 | 61327 | 2976 | 2025-12-29 16:00:00+00:00 | 2025-12-29 18:00:00+00:00 | 2025-12-31 19:00:00+00:00 | 2026-01-31 18:00:00+00:00 | 2025-12-29 19:00:00+00:00 | 2025-12-31 19:00:00+00:00 | 200 |

## 3. Leakage prevention

Никаких случайных split, future backfill, actual weather, eval_* или raw timestamps в X. Категории и статистический отбор признаков обучаются только на прошлом. Дубликаты D1/D2 не пересекают границы. Weather-performance признаки validation пересчитаны в отдельном ML view только по наблюдениям до проверочного месяца с availability < issue; исходные weather файлы и pipeline не менялись. Это имитирует отсутствие новых SCADA-ответов в феврале. История внутри train остаётся point-in-time online.

## 4. Baselines и ratios

Среднее/медиана turbine × hour рассчитаны на уникальных исторических наблюдениях, чтобы D1/D2 не удваивали один target. Persistence использует только доступное до issue наблюдение из предыдущих месяцев, поэтому стареет внутри месяца: это честная offline-версия, не online persistence с доступом к проверочным ответам.

| model | MAE | RMSE | MAE_D1 | MAE_D2 |
| --- | --- | --- | --- | --- |
| HistoricalMedian | 0.30086 | 0.38488 | 0.30086 | 0.30086 |
| HistoricalMean | 0.31828 | 0.36039 | 0.31828 | 0.31828 |
| Persistence | 0.34889 | 0.45508 | 0.34661 | 0.35118 |

| comparison | MAE_before | MAE_after | ratio_after_before | absolute_improvement | relative_improvement_pct |
| --- | --- | --- | --- | --- | --- |
| Selected ML vs best simple baseline: HistoricalMedian | 0.30086 | 0.15054 | 0.50038 | 0.15032 | 49.96193 |
| Selected ML vs best controlled single-provider ML: ECMWF | 0.16876 | 0.15054 | 0.89207 | 0.01821 | 10.79298 |

Описательный 95% интервал выигрыша MAE против baseline при paired bootstrap по UTC-дням: [0.11849, 0.17871]. Он не корректирует перебор моделей и не заменяет независимый test.

## 5. Weather provider comparison

Одинаковый LightGBM, одинаковые параметры и folds; Full = 24 компактных признака агента.

| Weather Strategy | model | D1 MAE | D2 MAE | Overall MAE | ratio_vs_best_single | Improvement vs best single provider (%) |
| --- | --- | --- | --- | --- | --- | --- |
| ECMWF | LightGBM (same settings) | 0.16143 | 0.17609 | 0.16876 | 1.00000 | 0.00000 |
| GFS | LightGBM (same settings) | 0.16757 | 0.18384 | 0.17571 | 1.04117 | -4.11699 |
| ICON | LightGBM (same settings) | 0.18031 | 0.19725 | 0.18878 | 1.11865 | -11.86457 |
| Simple | LightGBM (same settings) | 0.14983 | 0.16308 | 0.15645 | 0.92709 | 7.29092 |
| Weighted | LightGBM (same settings) | 0.15202 | 0.16802 | 0.16002 | 0.94821 | 5.17866 |
| All | LightGBM (same settings) | 0.14887 | 0.16595 | 0.15741 | 0.93276 | 6.72413 |
| All_Disagreement | LightGBM (same settings) | 0.14920 | 0.16647 | 0.15783 | 0.93525 | 6.47498 |
| Full | LightGBM (same settings) | 0.14791 | 0.16516 | 0.15653 | 0.92756 | 7.24375 |

## 6. Model tournament

Выполнено 53 конфигураций × 4 одинаковых outer folds. CatBoost, LightGBM, XGBoost × 8 погодных групп, CORE, компактные наборы, Full206 benchmark, tuning и архитектуры. Все параметры, stopping iterations и OOF сохранены в experiments/644e19e22a6c2779; сводка model_leaderboard.csv/.md, детализация model_fold_metrics.csv и model_segment_metrics.csv. Полный 206-признаковый набор не является моделью по умолчанию.

## 7. D1 vs D2

Выбор по совокупности четырёх месяцев, отдельно по горизонтам, с предпочтением общей модели при выигрыше менее 0.5%.

| horizon | configuration | features | validation_MAE |
| --- | --- | --- | --- |
| D1 | LightGBM__Top15__global__default | 15 | 0.14234 |
| D2 | LightGBM__Top15__global__default | 15 | 0.15875 |

## 8. Turbine strategy

Для одного и того же лучшего global learner/group/parameters проверены global, separate horizons, separate turbines, separate horizons × turbines. При близком MAE выбирается более простая архитектура.

| turbine_id | horizon_bucket | n | MAE | RMSE | nMAE | nMAE_pct | Bias | R2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| turbine_1 | D1 | 2891 | 0.14184 | 0.21516 | 0.14184 | 14.18365 | 0.01086 | 0.64982 |
| turbine_1 | D2 | 2891 | 0.15828 | 0.23784 | 0.15828 | 15.82789 | 0.00526 | 0.57211 |
| turbine_2 | D1 | 2885 | 0.14284 | 0.21811 | 0.14284 | 14.28393 | 0.01619 | 0.63742 |
| turbine_2 | D2 | 2885 | 0.15922 | 0.24030 | 0.15922 | 15.92249 | 0.01058 | 0.55990 |

## 9. Ablation study и компактность

Численные сравнения: ablation_study.md/.csv. Кривая размера: feature_count_experiment.csv (Top10/15/20/30/50 и Full). Ранжирование и корреляции получены только на первом outer train, затем заморожены. Финальный набор: models/final_features.json; описание final_feature_selection.md.

| comparison | MAE_before | MAE_after | ratio_after_before | absolute_improvement | relative_improvement_pct |
| --- | --- | --- | --- | --- | --- |
| LightGBM: ECMWF -> GFS | 0.16876 | 0.17571 | 1.04117 | -0.00695 | -4.11699 |
| LightGBM: ECMWF -> ICON | 0.16876 | 0.18878 | 1.11865 | -0.02002 | -11.86457 |
| LightGBM: ECMWF -> Simple | 0.16876 | 0.15645 | 0.92709 | 0.01230 | 7.29092 |
| LightGBM: ECMWF -> Weighted | 0.16876 | 0.16002 | 0.94821 | 0.00874 | 5.17866 |
| LightGBM: Weighted -> All | 0.16002 | 0.15741 | 0.98370 | 0.00261 | 1.62988 |
| LightGBM: All -> All_Disagreement | 0.15741 | 0.15783 | 1.00267 | -0.00042 | -0.26711 |
| LightGBM: Full_No_Performance -> Full | 0.15499 | 0.15653 | 1.00997 | -0.00155 | -0.99722 |
| LightGBM__Top15__global__default -> horizon | 0.15054 | 0.15173 | 1.00787 | -0.00119 | -0.78745 |
| LightGBM__Top15__global__default -> turbine | 0.15054 | 0.15058 | 1.00022 | -0.00003 | -0.02228 |
| LightGBM__Top15__global__default -> horizon_turbine | 0.15054 | 0.15121 | 1.00439 | -0.00066 | -0.43944 |

## 10. Hyperparameter tuning

Только top-3 компактных конфигурации после турнира: по два контролируемых варианта (regularized/richer), максимум 800 деревьев. Inner chronological early stopping, MAE loss и MAE evaluation; случайного CV нет. Все fitted параметры сохранены по fold.

## 11. Winning model

| horizon | configuration | features | validation_MAE |
| --- | --- | --- | --- |
| D1 | LightGBM__Top15__global__default | 15 | 0.14234 |
| D2 | LightGBM__Top15__global__default | 15 | 0.15875 |

Финальные refit используют все допустимые исторические метки. Для ранних forecast_issue_time соревнования создаются дополнительные as-of checkpoints: нельзя применить модель, обученную на конце января, к прогнозу, выпущенному до этих наблюдений. Registry выбирает checkpoint с train_max_available < issue. Число деревьев — медиана inner-stopping результатов четырёх folds, а не подбор на феврале.

## 12. Feature importance

feature_importance.csv/.png: нормализованная native importance финальных моделей. shap_importance.csv: native Tree SHAP на 128 исторических строках на модель, только описательно; эти значения не использовались для отбора на outer validation. Коррелирующие признаки могут делить importance.

## 13. Error analysis

error_analysis.md/.csv: horizon, turbine, час, месяц, lead, режим ветра, мощности, disagreement. Spearman(disagreement, |power error|) = 0.0512. Связь не является доказательством причинности.

| fold | n | MAE | RMSE | nMAE | nMAE_pct | Bias | R2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-10 | 2748 | 0.13602 | 0.20698 | 0.13602 | 13.60152 | -0.02592 | 0.61685 |
| 2025-11 | 2880 | 0.12848 | 0.19681 | 0.12848 | 12.84812 | -0.00784 | 0.72524 |
| 2025-12 | 2948 | 0.17289 | 0.26160 | 0.17289 | 17.28891 | 0.01042 | 0.52862 |
| 2026-01 | 2976 | 0.16318 | 0.23914 | 0.16318 | 16.31775 | 0.06280 | 0.49785 |

## 14. Competition forecast

predictions/final_forecast.parquet и .csv: 2 688 строк, ключи входа, prediction, selected model/group и checkpoint. predict.py проверяет порядок/наличие признаков, кодирование категорий, finite и [0,1], количество/уникальность ключей, доступность меток модели на issue и hashes. model_registry.json задаёт маршрутизацию D1/D2 и при необходимости турбин. Февральских targets нет — февральские метрики не заявляются.

## 15. Limitations

- Все четыре месяца использованы для выбора моделей/признаков. Это out-of-fold validation, но не независимый финальный test; selection optimism возможен.
- Previous Runs API provides forecasts at fixed historical lead-time offsets but does not expose exact historical API publication timestamps for every individual value. Принята согласованная fixed lead-time методология, не точное воспроизведение snapshot одного NWP-run.
- UTC+5 — ранее inferred metadata; inference использовал период 2024–2025, включающий часть проверочных месяцев. В этом этапе timezone принят как зафиксированный input contract, не переоценивался. Поэтому end-to-end validation не является полностью независимой проверкой inference timezone. Для строго независимой оценки нужно внешнее подтверждение timezone или fold-local inference.
- SCADA availability = конец часа + 60 минут — допущение исходного pipeline. Отсутствуют высота датчика, флаги ограничения генерации/аварий и подтверждённая паспортная мощность.
- nMAE нормируется на диапазон [0,1], не на среднее фактической мощности. MAE ×100 — процентные пункты нормализованной шкалы; трактовка как доля nameplate capacity требует подтверждения оператора.
- Ранние периоды без полноценной погоды исключены исходным pipeline. Missing SCADA-часы не заполняются.
- Отбор/тюнинг ограничен CPU-бюджетом и указанным набором вариантов; глобальная оптимальность не заявляется.
- Model ensemble не добавлен по умолчанию: основной результат — компактные интерпретируемые individual models.

## Reproduction

`python train.py` — аудит, resume-enabled tournament, final refits, inference. `python predict.py` — только загрузка финальных моделей и прогноз. Seed/threads: ml_config.json; точные версии: requirements-ml.txt и models/environment.json. Run fingerprint включает исходные Parquet, ML-код и версии; старые experiment results сохраняются отдельно.

Официальные API обучения: [CatBoost fit](https://catboost.ai/docs/en/concepts/python-reference_catboostregressor_fit), [LightGBM](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMRegressor.html), [XGBoost](https://xgboost.readthedocs.io/en/stable/python/python_api.html).
