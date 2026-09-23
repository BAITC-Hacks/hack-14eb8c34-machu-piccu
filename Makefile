PY := .venv/bin/python

.PHONY: setup test replay replay-strict verify agent agent-llm audit figures

setup:            ## окружение (macOS: сначала brew install libomp)
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

test:             ## тесты честности реплея, офлайн
	$(PY) -m pytest -q

replay:           ## сдача за февраль 2026, политика rolling (основная)
	$(PY) -m src.backtest --policy rolling

replay-strict:    ## то же под консервативной политикой
	$(PY) -m src.backtest --policy strict

verify:           ## 122-дневный проверочный реплей с метриками, обе политики
	$(PY) -m src.backtest --start 2025-10-01 --end 2026-01-30 --label verified --policy rolling
	$(PY) -m src.backtest --start 2025-10-01 --end 2026-01-30 --label verified --policy strict

agent:            ## один цикл агента, детерминированный режим
	$(PY) -m src.agent --date 2026-01-31

agent-llm:        ## тот же цикл, но циклом управляет LLM (ключ в .env)
	$(PY) -m src.agent --date 2026-01-31 --reason

audit:            ## сверка транскриптов LLM-режима: ни одного выдуманного числа
	$(PY) -m src.audit_transcripts

figures:          ## графики для README
	$(PY) -m src.report
