"""WindAgent: the agentic layer over the forecast pipeline.

The brief asks for a system that runs the whole loop itself -- fetch external
weather, prepare data, run the model, produce an hourly forecast, analyse it,
and recompute when inputs change. This module supplies that, in two modes.

**Autonomous mode** (default, no API key needed) runs the cycle through a
deterministic policy: forecast, analyse, measure how much the newest inputs
moved the answer, publish. It is what the backtest uses, so results are
exactly reproducible.

**Reasoning mode** (`--reason`) gives Claude the same steps as callable tools
and lets it drive: inspect the weather, judge whether the ensemble disagreement
warrants a second look, check what the input update changed, and write the
operator briefing. The full tool transcript is saved next to the forecast.

Both modes share one rule -- the language model never invents a number. Every
figure it reports comes back from a tool that ran the real model.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src import config, pipeline

MODEL_ID = "claude-opus-5"

SYSTEM_PROMPT = """\
You are the duty forecaster for a two-turbine wind site in the Shelek corridor, \
Kazakhstan. Each cycle you publish an hourly 48-hour power forecast for the grid \
operator.

Work through the tools available to you:
  1. inspect_weather      - what the numerical weather models are predicting
  2. run_forecast_cycle   - run the trained model and get the hourly forecast
  3. recent_performance   - how the forecast has actually been scoring lately
  4. check_input_updates  - how much the newest weather runs moved the answer
  5. publish_forecast     - write the forecast out for the control room

Rules that matter:
- Never state a number the tools did not return. You interpret the forecast; \
you do not produce it.
- Ensemble spread is your uncertainty signal. When the weather models disagree \
sharply, say so plainly and lean on the P10-P90 band rather than the point value.
- Check recent performance before trusting the forecast. A model that has been \
running consistently high for a fortnight deserves a caveat.
- Always call check_input_updates for each turbine: if the newest runs moved \
the day-ahead forecast materially, say what changed and in which direction.

Finish with a short operator briefing: expected energy, the shape of the day, \
any ramps worth staffing for, and your confidence with the reason for it. \
Write for a dispatcher deciding how much reserve to hold, not for a data \
scientist. No preamble."""

# The tool functions below are module-level so the SDK can derive their schemas.
# They talk to one pipeline instance set up by `WindAgent`.
_PIPELINE: pipeline.ForecastPipeline | None = None
_LAST_RUN: pipeline.ForecastRun | None = None


def _require_pipeline() -> pipeline.ForecastPipeline:
    if _PIPELINE is None:
        raise RuntimeError("Agent pipeline is not initialised")
    return _PIPELINE


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------
def inspect_weather(turbine: str, issue_date: str) -> str:
    """Summarise what the weather models predict for the next 48 hours.

    Args:
        turbine: Which turbine, "t1" or "t2".
        issue_date: Forecast issue date, YYYY-MM-DD. Covers the following two days.
    """
    engine = _require_pipeline()
    issue = pd.Timestamp(issue_date).normalize()
    by_lead = engine.fetch_weather(turbine, issue)
    from src import features

    block = features.build_block(by_lead, issue, horizon_days=engine.horizon_days, policy=engine.policy)
    if block.empty:
        return json.dumps({"error": f"no weather available for {issue_date}"})

    members = {
        name: round(float(block[f"{name}__wind_speed_100m"].mean()), 2)
        for name in config.NWP_MODELS
        if f"{name}__wind_speed_100m" in block
    }
    return json.dumps({
        "turbine": turbine,
        "issue_date": issue_date,
        "policy": engine.policy,
        "nwp_lead_hours": sorted(int(v) for v in block["nwp_lead_hours"].unique()),
        "hours": int(len(block)),
        "mean_wind_speed_100m_ms": round(float(block["wind_speed_100m"].mean()), 2),
        "max_wind_speed_100m_ms": round(float(block["wind_speed_100m"].max()), 2),
        "min_wind_speed_100m_ms": round(float(block["wind_speed_100m"].min()), 2),
        "mean_temperature_c": round(float(block["temperature_2m"].mean()), 1),
        "per_model_mean_wind_ms": members,
        "mean_ensemble_spread_ms": round(float(block["ws100_ens_std"].mean()), 2),
        "max_ensemble_spread_ms": round(float(block["ws100_ens_std"].max()), 2),
    })


def run_forecast_cycle(issue_date: str) -> str:
    """Run the full forecast cycle for both turbines and return the analysis.

    Fetches weather, builds features, runs the trained model, applies the
    online calibration, and analyses the resulting 48-hour hourly forecast.

    Args:
        issue_date: Forecast issue date, YYYY-MM-DD.
    """
    global _LAST_RUN
    engine = _require_pipeline()
    run = engine.run_cycle(issue_date)
    _LAST_RUN = run
    return json.dumps(run.summary(), default=str)


def recent_performance(turbine: str, as_of: str, days: int = 14) -> str:
    """Report how the forecast has actually scored over recent verified hours.

    Args:
        turbine: Which turbine, "t1" or "t2".
        as_of: Only hours strictly before this date are counted, YYYY-MM-DD.
        days: Length of the look-back window in days.
    """
    from src import metrics

    engine = _require_pipeline()
    cutoff = pd.Timestamp(as_of).normalize()
    log = engine.verification_log
    log = log[(log["turbine"] == turbine) & (log["time"] < cutoff)]
    log = log[log["time"] >= cutoff - pd.Timedelta(days=days)].dropna(subset=["power"])

    if log.empty:
        return json.dumps({"turbine": turbine, "verified_hours": 0,
                           "note": "no verified forecasts in this window yet"})

    scores = metrics.point_metrics(log["power"], log["forecast"])
    band = metrics.interval_coverage(log["power"], log["p10"], log["p90"])
    return json.dumps({
        "turbine": turbine, "window_days": days, "verified_hours": int(scores["n"]),
        "mae": round(scores["mae"], 4), "rmse": round(scores["rmse"], 4),
        "bias": round(scores["bias"], 4),
        "bias_direction": "over-forecasting" if scores["bias"] > 0 else "under-forecasting",
        "p10_p90_coverage": round(band["coverage"], 3),
    })


def check_input_updates(turbine: str, issue_date: str) -> str:
    """Measure how much the newest weather input moved the day-ahead forecast.

    In a replay the update is the arrival of today's NWP runs: the day-ahead
    hours were already forecast yesterday at a longer lead, and this compares
    the two. In live mode the operational forecast is refetched and compared.

    Args:
        turbine: Which turbine, "t1" or "t2".
        issue_date: Forecast issue date, YYYY-MM-DD.
    """
    global _LAST_RUN
    engine = _require_pipeline()
    if _LAST_RUN is None:
        return json.dumps({"error": "run_forecast_cycle must be called first"})

    result = engine.detect_input_change(turbine, pd.Timestamp(issue_date).normalize(), _LAST_RUN)
    fresh = result.pop("run", None)
    _LAST_RUN.revisions[turbine] = result
    if fresh is not None and result.get("changed"):
        _LAST_RUN.forecasts[turbine] = fresh.forecasts[turbine]
        _LAST_RUN.analysis[turbine] = fresh.analysis[turbine]
        result["action"] = "forecast replaced with the refreshed run"
    elif engine.mode == "archive" and "mean_abs_change" in result:
        result["action"] = ("day-ahead forecast revised with today's NWP runs" if result["changed"]
                            else "today's NWP runs confirm yesterday's forecast")
    else:
        result["action"] = "inputs unchanged; keeping the existing forecast"
    return json.dumps(result, default=str)


def publish_forecast(issue_date: str) -> str:
    """Write the current forecast to disk as hourly CSV plus a JSON summary.

    Args:
        issue_date: Forecast issue date, YYYY-MM-DD.
    """
    if _LAST_RUN is None:
        return json.dumps({"error": "nothing to publish; run_forecast_cycle first"})
    paths = pipeline.write_outputs(_LAST_RUN)
    return json.dumps({"published": {k: str(v) for k, v in paths.items()},
                       "rows": int(len(_LAST_RUN.combined()))})


TOOL_FUNCTIONS = [
    inspect_weather, run_forecast_cycle, recent_performance,
    check_input_updates, publish_forecast,
]


# --------------------------------------------------------------------------
# Agent
# --------------------------------------------------------------------------
@dataclass
class CycleResult:
    run: pipeline.ForecastRun
    briefing: str
    reasoning_mode: str
    transcript: list | None = None


class WindAgent:
    """Drives forecast cycles, with or without an LLM in the loop."""

    def __init__(self, engine: pipeline.ForecastPipeline | None = None) -> None:
        global _PIPELINE
        self.engine = engine or pipeline.ForecastPipeline(mode="archive")
        _PIPELINE = self.engine

    # -- autonomous policy ------------------------------------------------
    def run_cycle(self, issue_date: str, publish: bool = True) -> CycleResult:
        """Deterministic cycle: forecast, analyse, measure the input update, publish."""
        global _LAST_RUN
        run = self.engine.run_cycle(issue_date)
        _LAST_RUN = run
        issue = pd.Timestamp(issue_date).normalize()

        # Step 7 of the brief, made observable: every cycle measures what the
        # newest inputs changed. In live mode a refreshed run can replace the
        # forecast; in a replay the day's NWP runs are the update itself.
        for turbine_key in list(run.forecasts):
            check = self.engine.detect_input_change(turbine_key, issue, run)
            fresh = check.pop("run", None)
            run.revisions[turbine_key] = check
            if self.engine.mode == "live":
                if check.get("changed") and fresh is not None:
                    run.forecasts[turbine_key] = fresh.forecasts[turbine_key]
                    run.analysis[turbine_key] = fresh.analysis[turbine_key]
                    run.notes.append(f"{turbine_key}: refreshed inputs moved the forecast by "
                                     f"{check['mean_abs_change']:.3f} on average; forecast recomputed")
                else:
                    run.notes.append(f"{turbine_key}: refreshed inputs unchanged; forecast kept")
            elif "mean_abs_change" in check:
                direction = "up" if check["mean_signed_change"] > 0 else "down"
                if check["changed"]:
                    run.notes.append(
                        f"{turbine_key}: today's NWP runs ({check['current_nwp_lead_hours']} h lead) moved the "
                        f"day-ahead forecast {direction} by {check['mean_abs_change']:.3f} of rated on average "
                        f"(max {check['max_abs_change']:.3f}) versus yesterday's {check['previous_nwp_lead_hours']} h "
                        f"lead forecast; revised forecast published"
                    )
                else:
                    run.notes.append(
                        f"{turbine_key}: today's NWP runs confirm yesterday's forecast "
                        f"(mean change {check['mean_abs_change']:.3f} of rated)"
                    )
            else:
                run.notes.append(f"{turbine_key}: {check.get('reason', 'no input-update check')}")

        if publish:
            pipeline.write_outputs(run)
        return CycleResult(run=run, briefing=self._template_briefing(run), reasoning_mode="autonomous")

    @staticmethod
    def _template_briefing(run: pipeline.ForecastRun) -> str:
        issue_local = run.issue_time + pd.Timedelta(days=1 if run.policy == "rolling" else 0)
        lines = [
            f"Forecast cycle {run.issue_time.date()} ({run.policy} policy, issued {issue_local.date()} 00:00 local)"
            f" - local days {(run.issue_time + pd.Timedelta(days=1)).date()} and {(run.issue_time + pd.Timedelta(days=2)).date()}",
            "",
        ]
        for key, a in run.analysis.items():
            lines += [
                f"{config.TURBINES[key].name}:",
                f"  Expected energy   {a['energy_equivalent_full_load_hours']} equivalent full-load hours"
                f" (mean capacity factor {a['mean_capacity_factor']:.0%}); day-ahead {a['day_ahead_energy_eflh']}",
                f"  Peak {a['max_output']:.0%} at {a['peak_hour_local']}; "
                f"low {a['min_output']:.0%} at {a['trough_hour_local']}",
                f"  Confidence {a['confidence']} (P10-P90 width {a['mean_band_width']:.2f},"
                f" ensemble spread {a['mean_ensemble_spread_ms']} m/s, NWP lead {a['nwp_lead_hours']} h)",
            ]
            if a["ramp_events"]:
                lines.append(f"  {len(a['ramp_events'])} ramp event(s) above 25% of rated within an hour")
            lines.append(f"  Calibration: {a['calibration']}")
            lines.append("")
        lines += run.notes
        return "\n".join(lines)

    # -- LLM-in-the-loop --------------------------------------------------
    def run_cycle_with_reasoning(self, issue_date: str, max_tokens: int = 8000) -> CycleResult:
        """Let Claude drive the same tools and write the operator briefing.

        The conversation is mirrored into a transcript (every tool call, its
        arguments and its result) and saved with the forecast, so a reviewer
        without an API key can still read what the agent did and why.
        """
        global _LAST_RUN
        import anthropic

        client = anthropic.Anthropic()
        tools = [anthropic.beta_tool(fn) for fn in TOOL_FUNCTIONS]
        user_prompt = (
            f"Produce and publish the 48-hour forecast issued on {issue_date} "
            f"for both turbines, then brief the control room."
        )

        runner = client.beta.messages.tool_runner(
            model=MODEL_ID,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            tools=tools,
            messages=[{"role": "user", "content": user_prompt}],
        )

        transcript: list[dict] = [{"role": "user", "content": user_prompt}]
        final_text: list[str] = []
        for message in runner:
            blocks = []
            for block in message.content:
                if block.type == "text":
                    blocks.append({"type": "text", "text": block.text})
                    if block.text.strip():
                        final_text.append(block.text)
                elif block.type == "tool_use":
                    blocks.append({"type": "tool_use", "name": block.name, "input": block.input})
            transcript.append({"role": "assistant", "stop_reason": message.stop_reason, "content": blocks})
            tool_response = runner.generate_tool_call_response()
            if tool_response is not None:
                results = []
                for block in tool_response["content"]:
                    content = block.get("content")
                    results.append({"type": "tool_result", "content": content if isinstance(content, str) else str(content)})
                transcript.append({"role": "user", "content": results})

        run = _LAST_RUN or self.engine.run_cycle(issue_date)
        briefing = "\n".join(final_text).strip()
        self._save_transcript(issue_date, run, briefing, transcript)
        return CycleResult(run=run, briefing=briefing, reasoning_mode="llm", transcript=transcript)

    def _save_transcript(self, issue_date: str, run: pipeline.ForecastRun, briefing: str, transcript: list) -> None:
        stamp = pd.Timestamp(issue_date).strftime("%Y%m%d")
        path = config.OUTPUT_DIR / f"agent_transcript_{stamp}_{run.policy}.json"
        path.write_text(json.dumps({
            "issue_date": issue_date,
            "policy": run.policy,
            "mode": self.engine.mode,
            "model": MODEL_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "briefing": briefing,
            "transcript": transcript,
        }, indent=2, ensure_ascii=False, default=str))
        (config.OUTPUT_DIR / f"briefing_{stamp}_{run.policy}.md").write_text(briefing + "\n")


def has_api_credentials() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one WindAgent forecast cycle")
    parser.add_argument("--date", default=config.FIRST_ISSUE_DATE, help="issue date, YYYY-MM-DD")
    parser.add_argument("--mode", choices=["archive", "live"], default="archive",
                        help="'archive' replays a past issue date; 'live' calls the current forecast")
    parser.add_argument("--policy", choices=sorted(config.ASOF_POLICIES), default=config.DEFAULT_POLICY,
                        help="as-of policy for archive replays (see config.ASOF_POLICIES)")
    parser.add_argument("--reason", action="store_true",
                        help="let Claude drive the tools and write the briefing")
    args = parser.parse_args()

    agent = WindAgent(pipeline.ForecastPipeline(mode=args.mode, policy=args.policy))

    if args.reason:
        if not has_api_credentials():
            print("ANTHROPIC_API_KEY is not set - falling back to autonomous mode.\n")
            result = agent.run_cycle(args.date)
        else:
            result = agent.run_cycle_with_reasoning(args.date)
    else:
        result = agent.run_cycle(args.date)

    print(f"=== WindAgent cycle {args.date} ({result.reasoning_mode}, {args.policy}) ===\n")
    print(result.briefing)
    print(f"\nOutputs written to {config.OUTPUT_DIR}")


if __name__ == "__main__":
    main()
