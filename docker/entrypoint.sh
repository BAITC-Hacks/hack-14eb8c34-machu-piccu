#!/bin/sh
# Usage: docker run --rm windagent <command>
#   check      tests + the February 2026 replay (default)
#   test       14 offline honesty tests
#   replay     February 2026 deliverable, policy rolling (add "strict" for the conservative one)
#   verify     122-day scored replay, both policies
#   agent      one deterministic agent cycle for 2026-01-31 (or a date given as 2nd argument)
#   agent-llm  the same cycle driven by an LLM; needs -e OPENAI_API_KEY=... (or ANTHROPIC_API_KEY)
#   audit      audit of the 28 saved LLM transcripts
#   dashboard  Streamlit dashboard on port 8501 (run with -p 8501:8501)
#   shell      interactive shell
set -e
cmd="${1:-check}"; shift 2>/dev/null || true
case "$cmd" in
  check)     python -m pytest -q && python -m src.backtest --policy rolling ;;
  test)      python -m pytest -q ;;
  replay)    python -m src.backtest --policy "${1:-rolling}" ;;
  verify)    python -m src.backtest --start 2025-10-01 --end 2026-01-30 --label verified --policy rolling
             python -m src.backtest --start 2025-10-01 --end 2026-01-30 --label verified --policy strict ;;
  agent)     python -m src.agent --date "${1:-2026-01-31}" ;;
  agent-llm) python -m src.agent --date "${1:-2026-01-31}" --reason ;;
  audit)     python -m src.audit_transcripts ;;
  dashboard) python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --browser.gatherUsageStats false ;;
  shell)     exec sh ;;
  *)         exec "$cmd" "$@" ;;
esac
