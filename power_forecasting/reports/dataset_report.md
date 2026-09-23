# Итоговый датасет погоды для HackAlem

Parquet-файлы сформированы. Модель мощности не обучалась.

Всего строк в полном аудиторском dataset: 104,256. В training_dataset: 64,503. Competition: 2,688. Offline test: 2,688.
Признаков в allowlist: 206. Турбин: 2. Уникальных target timestamps: 26064.
Полный период target local time: 2023-03-11 00:00:00 – 2026-02-28 23:00:00.
Training target UTC: 2024-02-16 06:00:00+00:00 – 2026-01-31 18:00:00+00:00. Competition local: 2026-02-01 00:00:00 – 2026-02-28 23:00:00.
D1: 52,128; D2: 52,128. По lead_hours, турбине и split: dataset_row_counts.csv.
Исключено из обучающего export: 37,065 строк без полноценной SCADA-метки или без хотя бы одного провайдера с тремя основными погодными переменными. Все строки сохранены в master; ключи и причины — training_exclusions.csv.

UTC offset +5; timezone_status=inferred. Проверка: timezone_inference.csv, timezone_decision.md.
Offline test с известным target: 0 строк. Февральские метки не выдуманы.

## Покрытие провайдеров

Quality usable = валидные wind100m, direction100m, temperature, без API error или пропущенного target hour.

| Модель | Master, % | Training, % | Competition, % |
|---|---:|---:|---:|
| ECMWF | 66.62 | 97.16 | 100.00 |
| GFS | 68.42 | 100.00 | 100.00 |
| ICON | 68.40 | 99.98 | 100.00 |

Coverage каждой переменной и номинального lead: weather_coverage_report.csv. Первые и последние даты относятся только к запрошенному интервалу, не ко всему архиву провайдера.
Missing каждого признака: feature_missingness.csv. Веса: ensemble_weight_distribution.csv. Журнал всех запросов и хеши ответов: weather_request_manifest.csv.

## Сравнение погоды на общих часах

Ретроспективная оценка по train SCADA, одинаковые часы для всех моделей. Не является независимым holdout-тестом модели мощности. Bias = forecast − observation, ветер в м/с. Высота SCADA-датчика неизвестна.

| Weather model | Wind MAE D1 | Wind MAE D2 | Coverage D1/D2, % | Bias D1/D2 |
|---|---:|---:|---|---|
| ECMWF | 2.1615 | 2.3678 | 100.0/100.0 | 0.5835/0.5866 |
| GFS | 2.6010 | 2.7541 | 100.0/100.0 | 0.9763/0.9184 |
| ICON | 2.2131 | 2.3772 | 100.0/100.0 | -0.4679/-0.4983 |
| Simple Ensemble | 1.8800 | 2.0411 | 100.0/100.0 | 0.3639/0.3356 |
| Weighted Ensemble | 1.8660 | 2.0297 | 100.0/100.0 | 0.3327/0.3087 |

Показатели по каждой турбине, температуру, RMSE и оценку на всех доступных строках см. weather_provider_metrics.csv.

## Проверка утечек и ограничения

Проверено 104,256 строк: PASS_UNDER_DOCUMENTED_LEAD_TIME_SEMANTICS.
Rolling окна используют только outcome с observation_available_time строго меньше issue_time. Февральские наблюдения исключены из расчёта весов независимо от наличия offline targets.
Обучающий export и competition export не содержат eval_actual_* и производных от будущей SCADA. Используйте feature_columns.json как явный список X.
Previous Runs API provides forecasts at fixed historical lead-time offsets but does not expose exact historical API publication timestamps for every individual value.

Это согласованное методологическое ограничение, не blocker. D1/D2 — фиксированные offsets 24/48 ч, а lead_hours — отдельный горизонт строки внутри суточного расписания. Точное время публикации или source run не заявляется.
Тесты и их актуальный результат: tests_report.json (после python -m src.run_tests).
