"""WindAgent: the agentic layer over the forecast pipeline.

The brief asks for a system that runs the whole loop itself -- fetch external
weather, prepare data, run the model, produce an hourly forecast, analyse it,
and recompute when inputs change. This module supplies that, in two modes.

**Autonomous mode** (default, no API key needed) runs the cycle through a
deterministic policy: forecast, analyse, decide on a recompute from explicit
thresholds, publish. It is what the backtest uses, so results are exactly
reproducible.

**Reasoning mode** (`--reason`) gives Claude the same steps as callable tools
and lets it drive: inspect the weather, judge whether the ensemble disagreement
warrants a second look, request a recompute, and write the operator briefing.

Both modes share one rule -- the language model never invents a number. Every
figure it reports comes back from a tool that ran the real model.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
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
  4. check_input_updates  - refetch the weather and see if the answer moved
  5. publish_forecast     - write the forecast out for the control room

Rules that matter:
- Never state a number the tools did not return. You interpret the forecast; \
you do not produce it.
- Ensemble spread is your uncertainty signal. When the weather models disagree \
sharply, say so plainly and lean on the P10-P90 band rather than the point value.
- Check recent performance before trusting the forecast. A model that has been \
running consistently high for a fortnight deserves a caveat.
- Call check_input_updates when spread is high or a large ramp is forecast; \
that is exactly when a refreshed run changes the answer.

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

    block = features.build_block(by_lead, issue, horizon_days=engine.horizon_days)
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
    """Refetch the weather and report how much the forecast moved.

    Use when the ensemble disagrees sharply or a big ramp is expected -- those
    are the cases where a refreshed run genuinely changes the answer.

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
    if fresh is not None and result.get("changed"):
        _LAST_RUN.forecasts[turbine] = fresh.forecasts[turbine]
        _LAST_RUN.analysis[turbine] = fresh.analysis[turbine]
        result["action"] = "forecast replaced with the refreshed run"
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


class WindAgent:
    """Drives forecast cycles, with or without an LLM in the loop."""

    def __init__(self, engine: pipeline.ForecastPipeline | None = None) -> None:
        global _PIPELINE
        self.engine = engine or pipeline.ForecastPipeline(mode="archive")
        _PIPELINE = self.engine

    # -- autonomous policy ------------------------------------------------
    def run_cycle(self, issue_date: str, publish: bool = True) -> CycleResult:
        """Deterministic cycle: forecast, analyse, recompute if warranted."""
        global _LAST_RUN
        run = self.engine.run_cycle(issue_date)
        _LAST_RUN = run

        # The recompute trigger, stated explicitly rather than left to judgement.
        for turbine_key, analysis in list(run.analysis.items()):
            uncertain = analysis["confidence"] == "low" or analysis["ramp_events"]
            if not uncertain:
                continue
            check = self.engine.detect_input_change(turbine_key, pd.Timestamp(issue_date), run)
            fresh = check.pop("run", None)
            if check.get("changed") and fresh is not None:
                run.forecasts[turbine_key] = fresh.forecasts[turbine_key]
                run.analysis[turbine_key] = fresh.analysis[turbine_key]
                run.notes.append(
                    f"{turbine_key}: inputs moved {check['mean_abs_change']:.3f} on average; "
                    "forecast recomputed"
                )
            else:
                run.notes.append(f"{turbine_key}: inputs stable, no recompute needed")

        if publish:
            pipeline.write_outputs(run)
        return CycleResult(run=run, briefing=self._template_briefing(run), reasoning_mode="autonomous")

    @staticmethod
    def _template_briefing(run: pipeline.ForecastRun) -> str:
        lines = [f"Forecast issued {run.issue_time.date()} - next 48 hours", ""]
        for key, a in run.analysis.items():
            lines += [
                f"{config.TURBINES[key].name}:",
                f"  Expected energy   {a['energy_equivalent_full_load_hours']} equivalent full-load hours"
                f" (mean capacity factor {a['mean_capacity_factor']:.0%})",
                f"  Peak {a['max_output']:.0%} at {a['peak_hour_local']}; "
                f"low {a['min_output']:.0%} at {a['trough_hour_local']}",
                f"  Confidence {a['confidence']} (P10-P90 width {a['mean_band_width']:.2f},"
                f" ensemble spread {a['mean_ensemble_spread_ms']} m/s)",
            ]
            if a["ramp_events"]:
                lines.append(f"  {len(a['ramp_events'])} ramp event(s) above 25% of rated within an hour")
            lines.append(f"  Calibration: {a['calibration']}")
            lines.append("")
        lines += run.notes
        return "\n".join(lines)

    # -- LLM-in-the-loop --------------------------------------------------
    def run_cycle_with_reasoning(self, issue_date: str, max_tokens: int = 8000) -> CycleResult:
        """Let Claude drive the same tools and write the operator briefing."""
        global _LAST_RUN
        import anthropic

        client = anthropic.Anthropic()
        tools = [anthropic.beta_tool(fn) for fn in TOOL_FUNCTIONS]

        runner = client.beta.messages.tool_runner(
            model=MODEL_ID,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            tools=tools,
            messages=[{
                "role": "user",
                "content": (
                    f"Produce and publish the 48-hour forecast issued on {issue_date} "
                    f"for both turbines, then brief the control room."
                ),
            }],
        )

        final_text: list[str] = []
        for message in runner:
            for block in message.content:
                if block.type == "text" and block.text.strip():
                    final_text.append(block.text)

        run = _LAST_RUN or self.engine.run_cycle(issue_date)
        return CycleResult(run=run, briefing="\n".join(final_text).strip(), reasoning_mode="llm")


def has_api_credentials() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one WindAgent forecast cycle")
    parser.add_argument("--date", default=config.FIRST_ISSUE_DATE, help="issue date, YYYY-MM-DD")
    parser.add_argument("--mode", choices=["archive", "live"], default="archive",
                        help="'archive' replays a past issue date; 'live' calls the current forecast")
    parser.add_argument("--reason", action="store_true",
                        help="let Claude drive the tools and write the briefing")
    args = parser.parse_args()

    agent = WindAgent(pipeline.ForecastPipeline(mode=args.mode))

    if args.reason:
        if not has_api_credentials():
            print("ANTHROPIC_API_KEY is not set - falling back to autonomous mode.\n")
            result = agent.run_cycle(args.date)
        else:
            result = agent.run_cycle_with_reasoning(args.date)
    else:
        result = agent.run_cycle(args.date)

    print(f"=== WindAgent cycle {args.date} ({result.reasoning_mode}) ===\n")
    print(result.briefing)
    print(f"\nOutputs written to {config.OUTPUT_DIR}")


if __name__ == "__main__":
    main()
