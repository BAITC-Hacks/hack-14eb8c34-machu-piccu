# Проверка воспроизводимости

Проверено 2026-09-23. После успешной первой сборки выполнено полное повторение:

```powershell
python -m src.dataset_builder --download --offline
python -m src.run_tests
```

Повторная сборка завершилась с кодом 0. Все 78 погодных ответов прочитаны из локального кэша без сетевых запросов. SHA-256 всех четырёх выходных Parquet совпали с первой сборкой побайтно:

| Файл | SHA-256 |
|---|---|
| training_dataset.parquet | 01bb7bc09d9dd1c374f5ed72a36fda47405eacc286f730d622ae879516e67828 |
| competition_features.parquet | 0b779578b5f1fa302ea185cb7711ff646eb05415af6e08e523b5f0c279a5a52c |
| offline_test_with_targets.parquet | 916928adb15493f912e1272e01dbabeeba9e0597357a8790049bbfc411ddbe87 |
| training_weather_dataset.parquet | 38787af8551b724b1283cbd06573d6dd050cf856f2946cdb9721f81da63ee319 |

Размеры и хэши также сохранены в output_manifest.json. Все 24 теста пройдены: 0 failures, 0 errors, 0 skipped. Каждый Parquet прочитан обратно и проверен на соответствие исходной таблице.

Эта проверка относится к текущим исходным CSV, конфигурации, кэшу и зафиксированным версиям зависимостей. Она не гарантирует неизменность ответов сервиса при новой сетевой загрузке или побайтное совпадение при других версиях библиотек.

## Методологическое ограничение

Previous Runs API provides forecasts at fixed historical lead-time offsets but does not expose exact historical API publication timestamps for every individual value.

Использование previous_day1/previous_day2 проверяется по документированной fixed lead-time семантике, не по недоступным точным timestamp публикации. Это согласованное ограничение, а не blocker.
