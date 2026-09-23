# Для ИИ-агента проверяющего

Единственный документ проекта: `README.md`. Всё воспроизводится офлайн из репозитория.

```bash
brew install libomp                      # только macOS
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q            # 14 тестов честности реплея, ~5 с
.venv/bin/python -m src.backtest --policy rolling   # сдача за февраль 2026, ~1 мин, без сети
.venv/bin/python -m src.agent --date 2026-01-31     # один цикл агента с разбором
```

Ожидаемый результат: `outputs/february_2026_rolling_submission_local.csv`, 1 344 строки, и
строка `Submission: ... per turbine {'t1': 672, 't2': 672}`. Ключи API нужны только для
`--reason` (LLM-режим); транскрипты 28 февральских циклов уже лежат в `outputs/agent_transcripts/`,
их сверка: `.venv/bin/python -m src.audit_transcripts`.
