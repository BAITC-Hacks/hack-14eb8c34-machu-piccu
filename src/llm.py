"""The LLM layer of the reasoning mode: one tool-calling loop, two providers.

The forecasting tools in `src.agent` are plain Python functions. What differs
between providers is only how the model is asked to call them, so that part
lives here: an OpenAI backend (Chat Completions function calling) and an
Anthropic backend (the SDK's tool runner). Both return the same transcript
shape and both count tokens, because the reasoning mode costs real money and a
replay of a whole month must stay within a stated budget.

Credentials come from the environment or from a `.env` file in the repository
root (`OPENAI_API_KEY=...` / `ANTHROPIC_API_KEY=...`); the file is git-ignored.
"""
from __future__ import annotations

import inspect
import json
import os
import re
from dataclasses import dataclass, field
from typing import Callable

from src import config

# Approximate list prices, USD per 1M tokens (input, output), used only to keep
# a replay inside its budget and to report what a cycle cost. Unknown models
# fall back to the most expensive known entry so the budget guard errs safe.
PRICES_USD_PER_M: dict[str, tuple[float, float]] = {
    "gpt-4.1": (2.0, 8.0), "gpt-4.1-mini": (0.4, 1.6), "gpt-4.1-nano": (0.1, 0.4),
    "gpt-5": (1.25, 10.0), "gpt-5-mini": (0.25, 2.0), "gpt-5-nano": (0.05, 0.4),
    "gpt-5.1": (1.25, 10.0), "gpt-5.1-mini": (0.25, 2.0),
    "claude-opus-5": (5.0, 25.0), "claude-sonnet-5": (2.0, 10.0), "claude-haiku-4-5": (1.0, 5.0),
}
DEFAULT_OPENAI_MODEL = "gpt-5-mini"
DEFAULT_ANTHROPIC_MODEL = "claude-opus-5"
MAX_STEPS = 12               # tool-calling rounds per cycle; the policy needs ~6
MAX_COMPLETION_TOKENS = 4000


def load_dotenv(path=None) -> None:
    """Read KEY=VALUE lines from `.env` into the environment (without overriding)."""
    path = path or (config.ROOT / ".env")
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def available_provider() -> str | None:
    load_dotenv()
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return "anthropic"
    return None


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    price_in, price_out = PRICES_USD_PER_M.get(model, max(PRICES_USD_PER_M.values()))
    return (prompt_tokens * price_in + completion_tokens * price_out) / 1e6


# --------------------------------------------------------------------------
# Tool schemas from plain Python functions
# --------------------------------------------------------------------------
_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}


def _docstring_parts(fn: Callable) -> tuple[str, dict[str, str]]:
    doc = inspect.getdoc(fn) or ""
    head, _, tail = doc.partition("Args:")
    params: dict[str, str] = {}
    for line in tail.splitlines():
        m = re.match(r"\s*(\w+):\s*(.+)", line)
        if m:
            params[m.group(1)] = m.group(2).strip()
    return head.strip(), params


def openai_tool_schema(fn: Callable) -> dict:
    description, param_docs = _docstring_parts(fn)
    properties, required = {}, []
    for name, p in inspect.signature(fn).parameters.items():
        properties[name] = {
            "type": _TYPES.get(p.annotation, "string"),
            "description": param_docs.get(name, name),
        }
        if p.default is inspect.Parameter.empty:
            required.append(name)
    return {"type": "function", "function": {
        "name": fn.__name__, "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required},
    }}


# --------------------------------------------------------------------------
# Result shape shared by both providers
# --------------------------------------------------------------------------
@dataclass
class LLMRun:
    provider: str
    model: str
    final_text: str
    transcript: list = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    steps: int = 0

    @property
    def cost_usd(self) -> float:
        return estimate_cost_usd(self.model, self.prompt_tokens, self.completion_tokens)

    def usage(self) -> dict:
        return {"provider": self.provider, "model": self.model, "steps": self.steps,
                "prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens,
                "estimated_cost_usd": round(self.cost_usd, 4)}


# --------------------------------------------------------------------------
# OpenAI backend
# --------------------------------------------------------------------------
def run_openai(system: str, user_prompt: str, functions: list[Callable], model: str | None = None,
               max_steps: int = MAX_STEPS) -> LLMRun:
    """Function-calling loop on the Chat Completions API until the model stops calling tools."""
    from openai import OpenAI

    load_dotenv()
    model = model or os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    client = OpenAI()
    tools = [openai_tool_schema(fn) for fn in functions]
    registry = {fn.__name__: fn for fn in functions}
    messages: list[dict] = [{"role": "system", "content": system}, {"role": "user", "content": user_prompt}]
    run = LLMRun(provider="openai", model=model, final_text="",
                 transcript=[{"role": "user", "content": user_prompt}])

    extra: dict = {}
    if model.startswith(("gpt-5", "o")):
        extra["reasoning_effort"] = os.environ.get("OPENAI_REASONING_EFFORT", "low")

    for _ in range(max_steps):
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, tools=tools, tool_choice="auto",
                max_completion_tokens=MAX_COMPLETION_TOKENS, **extra,
            )
        except Exception as exc:  # noqa: BLE001 - retry once without optional params
            if extra:
                extra = {}
                response = client.chat.completions.create(
                    model=model, messages=messages, tools=tools, tool_choice="auto",
                    max_completion_tokens=MAX_COMPLETION_TOKENS,
                )
            else:
                raise exc
        run.steps += 1
        if response.usage:
            run.prompt_tokens += response.usage.prompt_tokens or 0
            run.completion_tokens += response.usage.completion_tokens or 0

        message = response.choices[0].message
        calls = message.tool_calls or []
        entry = {"role": "assistant", "content": message.content or ""}
        if calls:
            entry["tool_calls"] = [{"name": c.function.name, "input": json.loads(c.function.arguments or "{}")} for c in calls]
        run.transcript.append(entry)
        assistant_msg: dict = {"role": "assistant", "content": message.content}
        if calls:
            assistant_msg["tool_calls"] = [c.model_dump() for c in calls]
        messages.append(assistant_msg)

        if not calls:
            run.final_text = (message.content or "").strip()
            break

        results = []
        for call in calls:
            fn = registry.get(call.function.name)
            try:
                args = json.loads(call.function.arguments or "{}")
                result = fn(**args) if fn else json.dumps({"error": f"unknown tool {call.function.name}"})
            except Exception as exc:  # noqa: BLE001 - the model should see tool failures
                result = json.dumps({"error": f"{type(exc).__name__}: {exc}"})
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})
            results.append({"name": call.function.name, "content": str(result)})
        run.transcript.append({"role": "tool", "results": results})
    else:
        run.final_text = "(the agent ran out of tool-calling steps before writing its briefing)"
    return run


# --------------------------------------------------------------------------
# Anthropic backend
# --------------------------------------------------------------------------
def run_anthropic(system: str, user_prompt: str, functions: list[Callable], model: str | None = None,
                  max_tokens: int = 8000) -> LLMRun:
    """The SDK's tool runner drives the loop; the transcript is mirrored as it goes."""
    import anthropic

    load_dotenv()
    model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
    client = anthropic.Anthropic()
    tools = [anthropic.beta_tool(fn) for fn in functions]
    runner = client.beta.messages.tool_runner(
        model=model, max_tokens=max_tokens, system=system, thinking={"type": "adaptive"},
        tools=tools, messages=[{"role": "user", "content": user_prompt}],
    )
    run = LLMRun(provider="anthropic", model=model, final_text="",
                 transcript=[{"role": "user", "content": user_prompt}])
    final_text: list[str] = []
    for message in runner:
        run.steps += 1
        if getattr(message, "usage", None):
            run.prompt_tokens += message.usage.input_tokens or 0
            run.completion_tokens += message.usage.output_tokens or 0
        entry: dict = {"role": "assistant", "content": "", "tool_calls": []}
        for block in message.content:
            if block.type == "text":
                entry["content"] += block.text
                if block.text.strip():
                    final_text.append(block.text)
            elif block.type == "tool_use":
                entry["tool_calls"].append({"name": block.name, "input": block.input})
        if not entry["tool_calls"]:
            entry.pop("tool_calls")
        run.transcript.append(entry)
        tool_response = runner.generate_tool_call_response()
        if tool_response is not None:
            results = []
            for block in tool_response["content"]:
                content = block.get("content")
                results.append({"name": "", "content": content if isinstance(content, str) else str(content)})
            run.transcript.append({"role": "tool", "results": results})
    run.final_text = "\n".join(final_text).strip()
    return run


def run(provider: str, system: str, user_prompt: str, functions: list[Callable], model: str | None = None) -> LLMRun:
    if provider == "openai":
        return run_openai(system, user_prompt, functions, model=model)
    if provider == "anthropic":
        return run_anthropic(system, user_prompt, functions, model=model)
    raise ValueError(f"unknown LLM provider {provider!r}")
