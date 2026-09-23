"""Optional local LLM explanation layer (spec sections 34-36).

Turns the already-structured, deterministic recommendation (context + NBA + template
explanation) into more natural-language phrasing via a local Ollama model. The LLM is
used purely for phrasing -- it never sees raw telemetry and never makes the
safety/priority decision itself (spec section 34: Raw telemetry -> ML/Rules -> Structured
findings -> Context Engine -> LLM -> human-readable explanation, never telemetry -> LLM ->
safety decision).

Falls back cleanly to the Phase 5 template explanation if Ollama is unreachable, slow, or
errors -- the system must keep functioning without it (spec section 36).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:1.5b"
REQUEST_TIMEOUT_SECONDS = 6.0

_PROMPT_TEMPLATE = """You are an assistant that rewrites a machine-generated operator alert into one \
short, natural-language paragraph (2-3 sentences) for a construction equipment operator. \
Do not invent facts, numbers, or causes beyond what is given. Do not add safety claims \
beyond what is stated. Be direct and plain-spoken.

Detection: {detection}
Evidence: {evidence}
Recommended action: {recommendation}
Priority: {priority}
Confidence: {confidence}%

Rewrite this as one short paragraph an operator would read on a dashboard:"""


def is_available(timeout: float = 1.5) -> bool:
    try:
        req = urllib.request.Request(OLLAMA_URL.replace("/api/generate", "/api/tags"))
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def generate_natural_language(explanation: dict, model: str = DEFAULT_MODEL) -> str | None:
    """Returns an LLM-phrased version of `explanation`, or None on any failure (caller
    should fall back to `explain.format_as_text`)."""
    prompt = _PROMPT_TEMPLATE.format(
        detection=explanation["detection"],
        evidence=explanation["evidence"],
        recommendation=explanation["recommendation"],
        priority=explanation["priority"],
        confidence=round(explanation["confidence"] * 100),
    )
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            text = body.get("response", "").strip()
            return text or None
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError, KeyError):
        return None


def explain_with_fallback(explanation: dict, model: str = DEFAULT_MODEL) -> dict:
    """Returns a copy of `explanation` with `narrative` set to the LLM phrasing when
    available, or the deterministic template text otherwise. Never raises."""
    from app.context.explain import format_as_text

    result = dict(explanation)
    llm_text = generate_natural_language(explanation, model=model) if is_available() else None

    if llm_text:
        result["narrative"] = llm_text
        result["source"] = "llm"
    else:
        result["narrative"] = format_as_text(explanation)
        result["source"] = "template"

    return result
