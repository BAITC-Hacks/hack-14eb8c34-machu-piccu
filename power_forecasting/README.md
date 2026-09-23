# HackAlem — готовый погодный датасет

> **Для жюри:** в ветке `feature/jury-ready` уже включены данные, модели и результаты экспериментов. Начните с [JURY_GUIDE.md](JURY_GUIDE.md): `python judge.py` проверяет комплект и воспроизводит прогноз; `--retrain-winner` повторяет обучение на четырёх folds. Используйте Python 3.12 и requirements-jury.txt.

## Новый этап: ML-прогноз мощности

Погодный pipeline ниже сохранён без изменения. Отдельный ML-этап использует готовые Parquet, не скачивает погоду и не изменяет raw datasets.

```powershell
python -m pip install -r requirements-ml.txt
python train.py
python predict.py
python -m src.run_tests
```

`train.py --audit-only` выполняет аудит и проверку временных folds. `train.py` сохраняет результаты каждого эксперимента и продолжает совместимый запуск из кэша experiments/<fingerprint>. Конфигурация — ml_config.json. Итоговые прогнозы — predictions/final_forecast.parquet и .csv; модели и routing — models/model_registry.json; точный список используемых признаков — models/final_features.json.

Начальный CORE содержит 21 признак. Сравниваются компактные weather-группы, Top10/15/20/30/50 и полный safe-набор только как benchmark. Финальная конфигурация предпочитает компактность при близком walk-forward MAE. Отбор признаков выполняется на первом историческом train, затем замораживается; никакой корреляции с target на всём dataset для отбора нет.

Проверка — четыре последних полных месяца, chronological split по target_time и availability purge до самого раннего forecast issue. Early stopping использует отдельный внутренний исторический интервал, не outer validation. Для ранних февральских forecast issues используются as-of checkpoints: финальная модель со всеми январскими метками не применяется задним числом.

Итоговые метрики мощности и отношения ошибок к baseline: reports/final_ml_report.md, reports/model_leaderboard.csv, reports/power_model_ratios.csv. Компактность: reports/feature_count_experiment.csv, reports/final_feature_selection.md. Это model-selection validation, не независимый февральский test: февральских targets нет. Не интерпретируйте 1 − MAE как accuracy.

Далее — документация исходного погодного этапа; его размеры и тестовые результаты относятся к завершению именно этого этапа.

Pipeline готовит признаки ECMWF/GFS/ICON, оценивает временной сдвиг SCADA, рассчитывает прошлые ошибки и ансамбли, создаёт Parquet. Модель мощности не обучается.

Текущий результат: **64 503 обучающие строки, 2 688 competition-строк, 206 признаков, 24 теста пройдены**. Master содержит 104 256 строк, включая ранние периоды без достаточной погоды. Training после фильтра: 2024-02-16 11:00 — 2026-01-31 23:00 по принятому местному времени UTC+5. Competition: весь февраль 2026.

## Запуск

Проверено на Python 3.12; версии зависимостей зафиксированы.

```powershell
python -m pip install -r requirements.txt
python -m src.input_data
python -m src.dataset_builder --download
python -m src.run_tests
```

Полное воспроизведение без интернета:

```powershell
python -m src.dataset_builder --download --offline
python -m src.run_tests
```

Быстрая пересборка из data/processed/weather_archive.parquet: `python -m src.dataset_builder`. Отдельная загрузка: `python -m src.download_weather`. В текущей среде pyarrow установлен локально в .deps, остальные библиотеки доступны в bundled Python; исходники не зависят от конкретного пути интерпретатора. При обычной установке requirements.txt каталог .deps не нужен.

## Методология Previous Runs

Используется [официальный Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api) с явными моделями ecmwf_ifs025, gfs_global, icon_global. Запросы для координат каждой турбины отдельные. Единицы: м/с, °C, hPa. HRES из прежних проб, реанализ и Historical Forecast API в датасете не используются.

D1 (lead_hours 1–24) берёт *_previous_day1, D2 (25–48) — *_previous_day2. Система запускается ежедневно в forecast_run_hour по принятой локальной шкале. По документации архивные суффиксы означают фиксированные исторические lead-time offsets примерно 24 и 48 часов.

- forecast_issue_time — моделируемый запуск системы.
- archive_nominal_lead_hours — фиксированные 24/48 часов архива.
- archive_reference_time = target_time − archive_nominal_lead_hours — номинальная архивная привязка, **не доказанная публикация и не initialization time**.

Проверяется archive_reference_time <= forecast_issue_time. Для ранних lead внутри D1/D2 погода может быть старее горизонта строки. Набор не является полным снимком одного исторического запуска NWP. Эта методология прямо согласована пользователем.

**Previous Runs API provides forecasts at fixed historical lead-time offsets but does not expose exact historical API publication timestamps for every individual value.**

В каждой строке:
methodology_status=lead_time_archive,
weather_archive_method=open_meteo_previous_runs,
weather_archive_confidence=fixed_lead_time_archive,
timezone_status=inferred либо assumed.

run_time, estimated availability и stale_run оставлены неизвестными. Если позже добавляется конкретный run, валидатор требует estimated availability с dissemination buffer из config (8 часов по умолчанию) и проверяет, что прогноз успел стать доступен до issue. Buffer — консервативная оценка, а не фактическая историческая публикация. В текущих exports run-specific режим не применяется.

## Timezone и наблюдения SCADA

Timezone CSV не задан. Проверены UTC−6 … UTC+6 против архивного D1 wind100m на одинаковых часах для каждого offset, посчитаны correlation, MAE и RMSE, отдельно по годам. Калибровка только по train 2024–2025; февраль не используется. Выбран UTC+5, статус inferred. Это статистическая оценка, не verified.

Для inferred требуется минимум 1000 пар, отрыв корреляции >=0.002, улучшение RMSE >=0.001 относительно второго кандидата, MAE не хуже. При неоднозначности используется config timezone со статусом assumed. В конфигурации UTC — нейтральный fallback, а не утверждение о географии; текущему запуску он не потребовался.

Используется один фиксированный offset. Фаза погодных ошибок, высота датчика и изменения часов SCADA могут влиять на inference. Подробности в timezone_inference.csv и timezone_decision.md. Выбор timezone — train-only оценка метаданных. Для строгого online replay его следует подтвердить заранее или переоценивать внутри каждого backtest fold.

Предполагается, что timestamp SCADA обозначает начало 10-минутного интервала. Почасовая метка — начало часа, target — среднее шести измерений. При менее чем шести значениях любого столбца все три итоговых наблюдения часа становятся NaN. Число измерений сохраняется. Предполагается доступность после конца часа плюс 60 минут. Допущения вынесены в config.yaml. Номинальная мощность неизвестна; перевод в МВт не выполняется.

## Расписание и защита от утечек

issue, target и archive reference сохраняются в UTC; target_local_time — локальная шкала календаря и границ split. Train заканчивается 31 января, competition — весь февраль. Target появляется с разными issue_time для D1 и D2. Ключ: turbine_id + forecast_issue_time + target_time + weather_configuration.

Rolling MAE/RMSE/bias/counts рассчитываются по turbine_id + horizon_bucket за 7/30/90 дней. Ошибка допускается только при observation_available_time < forecast_issue_time. Совпадение с issue исключается. Окно определяется по доступности outcome, минимум 24 ошибки; иначе NaN без future backfill. Для каждой метрики сохранено самое позднее использованное время доступности. Competition observations никогда не влияют на rolling или веса, даже если offline targets будут предоставлены.

Для X обязательно используйте feature_columns.json. Target и eval_actual_* не входят в allowlist. При последующей валидации ML разделяйте по target_time: один target с разными issue не должен оказаться одновременно в train и validation.

## Качество

| Поле | Допустимые значения |
|---|---|
| wind_speed_10m | 0–75 м/с |
| wind_speed_100m | 0–100 м/с |
| wind_direction_10m/100m | 0–360° |
| temperature_2m | −90…65 °C |
| surface_pressure | 300–1100 hPa |
| relative_humidity_2m | 0–100% |
| wind_gusts_10m | 0–150 м/с |

available означает хотя бы одно непустое поле. quality_ok требует валидных wind100m, direction100m, temperature без API error или missing target hour. Available count и usable count различаются. Quality score = число валидных полей / (8 × 3). Partial coverage отмечает частично заполненные модели. Stale-run неизвестен, поскольку время run не раскрыто.

Невалидные значения сохраняются в исходных колонках, но исключаются из ансамблей и оценки ошибок. Пропущенные часы остаются строками с NaN. Временной интерполяции нет. Дубликаты и несогласованные временные метки/массивы вызывают ошибку. Отказ провайдера фиксируется флагами, остальные продолжают работать. Ноль usable providers в competition вызывает ERROR. Ранние train-строки без погоды остаются в master и исключаются из training export с объяснением.

## Ансамбли

Simple ensemble — среднее валидных прогнозов. Weighted ensemble: 1 / (MAE_30d + 0.05) с нормализацией. Если у любой доступной для переменной модели недостаточно истории, используются равные веса и cold-start flag. Недоступная модель получает ноль; при отсутствии всех моделей прогноз NaN.

Основные model_weight относятся к wind100m; температура имеет отдельные веса. Прочие переменные используют веса ветра с перенормировкой по валидным полям; если все веса этих полей нулевые, используются равные. Стратегия весов — отдельная функция.

Направление усредняется через sin/cos и atan2. При противоположных направлениях и нулевой результирующей направление NaN. Circular dispersion = 1 − resultant_length. Обычный std: ddof=0. При одной модели std/range=0, при нуле — NaN.

Сохраняются все исходные прогнозы, simple/weighted ensembles, historical performance, веса, disagreement, sin/cos направлений, календарные признаки и lead_hours. best_weather_model_recent выбирается по прошлому wind MAE; при отсутствии истории — unknown.

## Выходные файлы

| Файл в data/final | Содержание |
|---|---|
| training_dataset.parquet | 64 503 пригодные train-строки, target и признаки |
| competition_features.parquet | 2 688 строк без actual power/weather и производных от будущих наблюдений |
| offline_test_with_targets.parquet | 2 688 строк с evaluation-полями; target за февраль отсутствует в исходных CSV, поэтому NaN |
| training_weather_dataset.parquet и .csv | Все 104 256 строк для аудита; competition actuals отделены в offline export |
| feature_columns.json | Список 206 X-признаков и категориальных полей |
| run_config.json | Конфигурация, timezone decision и configuration hash |

Покрытие основных переменных в training: ECMWF 97.16%, GFS 100%, ICON 99.98%; в competition — 100% у всех трёх. Ранних ветровых прогнозов недостаточно для всего периода SCADA с марта 2023: значения не выдумываются. Master CSV занимает около 296 MB, для работы предпочтителен Parquet.

В data/processed сохраняются архивы провайдеров, объединённый archive, hourly SCADA, forecast_schedule, weather_raw. 78 пакетных ответов закэшированы отдельно по моделям и координатам. Ключ кэша зависит от полного URL. Есть timeout, bounded retries для 429/5xx/ошибок сети, Retry-After, журнал и продолжение после прерывания. retrieved_at — дата сегодняшней загрузки, не historical publication time.

## Проверки и отчёты

run_tests сохраняет фактический результат в reports/tests_report.json. Проверяются мутации будущих наблюдений, изоляция competition, точный cutoff, отсутствие backfill, круговое среднее, cold start, недоступные модели, ключи, split, dissemination delay, кэш и exports. Каждый записанный Parquet прочитан обратно и сравнен с исходной таблицей.

- dataset_report.md и dataset_summary.json: размеры, периоды, coverage, таблица MAE/bias.
- weather_coverage_report.csv: model/variable/D1/D2/turbine и реальные границы непустых данных **в запрошенном интервале**, не всего архива.
- feature_missingness.csv: missing по каждому признаку в master/train/competition.
- ensemble_weight_distribution.csv, dataset_row_counts.csv: веса и строки каждого lead.
- weather_provider_metrics.csv: wind MAE/RMSE/bias и temperature MAE/bias по турбине и горизонту; отдельное сравнение на общих часах.
- training_exclusions.csv: ключи и причины исключения каждой строки из обучающего export.
- point_in_time_validation.md: проверка всех 104 256 строк по согласованной lead-time методологии.
- weather_request_manifest.csv, output_manifest.json: запросы и SHA256 ответов/выходных Parquet.
- reproducibility.md: повторная полностью offline-сборка; все четыре Parquet побайтно совпали с первой сборкой по SHA-256.
- input_data_report.md, timezone_inference.csv, timezone_decision.md: исходные данные и временной сдвиг.

config.yaml записан в JSON-синтаксисе, совместимом с YAML 1.2; при редактировании сохраняйте этот синтаксис. Все ключевые параметры доступны в конфигурации.

archive_decision.md — исторический отчёт о первоначальном blocker, снятом решением пользователя; он не отражает текущий статус. Старые отдельные пробы можно повторить через `python -m src.weather_client --offline`; они записываются в weather_preflight_report.csv и не перезаписывают полный coverage report.
