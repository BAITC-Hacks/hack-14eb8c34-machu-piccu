# Проверка point in time

{
  "status": "PASS_UNDER_DOCUMENTED_LEAD_TIME_SEMANTICS",
  "rows_checked": 104256,
  "exact_publication_timestamps_verified": false,
  "limitation": "Previous Runs API provides forecasts at fixed historical lead-time offsets but does not expose exact historical API publication timestamps for every individual value."
}

Проверены порядок issue/target, lead, D1/D2, nominal reference, ключи, граница split, последний доступный outcome для каждой rolling-метрики и feature allowlist.

Тесты мутаций будущих данных и edge cases: tests_report.json.
