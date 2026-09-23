"""Audit the reasoning-mode transcripts: did the LLM only report what its tools returned?

Run:  python -m src.audit_transcripts            (exit code 1 if any check fails)

For every transcript in outputs/agent_transcripts/ the audit checks:
  errors     no tool call returned an error;
  energy     the briefing quotes both energy figures run_forecast_cycle returned, per turbine;
  units      no revision or change figure is labelled in m/s (they are fractions of rated power);
  det_match  the cycle's numbers equal the deterministic replay's for the same date
             (outputs/<label>_<policy>_daily_briefings.json), i.e. the LLM changed no number.
"""
from __future__ import annotations

import glob
import json
import re
import sys

from src import config


def _tool_results(transcript: list[dict]):
    for entry in transcript:
        if entry["role"] == "tool":
            for result in entry["results"]:
                yield result["content"]


def _quoted(value: float, text: str) -> bool:
    return any(token in text for token in (f"{value:.2f}", f"{value:.1f}", str(round(value))))


def audit(policy: str = config.DEFAULT_POLICY, label: str = "february_2026") -> int:
    det_path = config.OUTPUT_DIR / f"{label}_{policy}_daily_briefings.json"
    deterministic = {b["issue_date"]: b["analysis"] for b in json.loads(det_path.read_text())} if det_path.exists() else {}
    files = sorted(glob.glob(str(config.OUTPUT_DIR / "agent_transcripts" / f"transcript_*_{policy}.json")))
    if not files:
        print("no transcripts found"); return 1

    failures = 0
    print(f"{'issue_date':11s} {'calls':>5s} {'errors':>6s} {'energy':>6s} {'units':>5s} {'det_match':>9s}  cost_usd")
    for path in files:
        doc = json.loads(open(path).read())
        transcript, briefing, date = doc["transcript"], doc["briefing"], doc["issue_date"]
        calls = sum(len(e.get("tool_calls", [])) for e in transcript if e["role"] == "assistant")
        errors = sum('"error"' in r for r in _tool_results(transcript))
        cycle = next((json.loads(r) for r in _tool_results(transcript) if '"energy_48h_eflh"' in r), None)
        energy_ok = units_ok = det_ok = None
        if cycle:
            energy_ok = all(_quoted(cycle["turbines"][t][k], briefing)
                            for t in cycle["turbines"] for k in ("energy_48h_eflh", "energy_day_ahead_24h_eflh"))
            if date in deterministic:
                det_ok = all(abs(cycle["turbines"][t]["energy_48h_eflh"] - deterministic[date][t]["energy_48h_eflh"]) < 0.005
                             for t in cycle["turbines"])
        units_ok = not re.search(r"(change|revision|revised)[^.\n]{0,60}m/s", briefing, re.I)
        bad = errors > 0 or energy_ok is False or units_ok is False or det_ok is False
        failures += bad
        flag = lambda v: "-" if v is None else ("ok" if v else "FAIL")
        print(f"{date:11s} {calls:5d} {errors:6d} {flag(energy_ok):>6s} {flag(units_ok):>5s} {flag(det_ok):>9s}  {doc['usage']['estimated_cost_usd']:.4f}")
    print(f"\n{len(files)} transcripts, {failures} with failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(audit(*(sys.argv[1:2] or [config.DEFAULT_POLICY])))
