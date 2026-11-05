"""Prompt building and the Gemini call. Returns parsed JSON or raises LLMError."""
from __future__ import annotations

import json

import streamlit as st

import config


class LLMError(Exception):
    """API failure, timeout, quota, or unusable output."""


@st.cache_resource(show_spinner=False)
def _client(api_key: str):
    from google import genai
    from google.genai import types
    return genai.Client(api_key=api_key,
                        http_options=types.HttpOptions(timeout=config.TIMEOUT_SECONDS * 1000))


def get_client():
    key = config.api_key()
    if not key:
        raise LLMError("GEMINI_API_KEY is not set")
    return _client(key)


SYSTEM_PROMPT = """You are FinSaar ("Aapke SIP ka saar"), a calm explainer inside a mutual fund app.
You help a first-time investor understand THEIR OWN SIP numbers. This is a concept prototype with fictional data.

HARD RULES (never break):
1. No investment advice. Never tell the user to continue, pause, stop, buy, sell, switch, hold, or invest more.
   Never recommend any fund or stock. Never write "you should", "you must", "I recommend", "I suggest",
   "stay invested", "keep investing", or Hinglish like "band kar do", "continue karo", "chalu rakho", "karna chahiye".
2. No predictions. Never say or hint that a fall will recover or that NAV/markets will rise or fall.
   Avoid the words "will recover", "will go up", "will grow", "market will" entirely.
3. No fear, FOMO or urgency. No "hurry", "huge loss", "big loss", "act now", "don't miss", "others are", "panic".
   Do not say "don't worry" either; just explain calmly.
4. You NEVER calculate. Use only numbers that appear exactly in the SIP FACTS block. Copy them as written
   (e.g. ₹496, ₹9,504, 412.15 units, −18.5%). Do not add, subtract, divide, or invent any number.
   Do not write years or numbers that are not in SIP FACTS.
5. No made-up facts. Use only SIP FACTS and the KNOWLEDGE chunks. If they do not cover the question,
   say you are not sure and that the official source has more.

OUTPUT: JSON only, matching the schema:
{"answer": str, "numbers_used": [str], "sources": [str], "terms_explained": [str]}
- "sources": the ids of the KNOWLEDGE chunks you used (e.g. "K2") and/or "Your SIP data". At least one.
- "numbers_used": each number from SIP FACTS that appears in the answer, as written.
- "terms_explained": finance terms you defined in this answer (e.g. "NAV", "units", "XIRR").
"""

DECLINE_ADDON = """
THIS IS A DECISION / RECOMMENDATION QUESTION. Do not answer it with a decision.
- ONLY if it asks which fund or stock to pick or switch to: say clearly "I can't recommend any fund or stock"
  (Hinglish: "Main koi fund ya stock recommend nahi kar sakta") and name no fund.
- Otherwise briefly explain, in neutral general terms from the KNOWLEDGE chunks, what pause, skip,
  change amount and stop each do, and note the units already held remain in the fund.
- Do not say which option is better. End with exactly: "The decision is yours."
  (Hinglish: "Faisla aapka hai (the decision is yours).")
"""


def _profile_text(profile: dict) -> str:
    level = profile.get("level", "beginner")
    lang = profile.get("language", "hinglish")
    limit = 80 if level == "beginner" else 120
    if profile.get("simpler"):
        limit = min(limit, 60)
    lines = [
        f"- Level: {'first-time investor, no finance background' if level == 'beginner' else 'knows the basics of mutual funds'}",
        f"- Language: {'Hinglish (Hindi + English mix) written in Roman script only, no Devanagari' if lang == 'hinglish' else 'simple English'}",
        f"- Stage: first {profile.get('n_instalments', 5)} months of their first SIP; value is below the amount invested",
        f"- Word limit: at most {limit} words. Short sentences.",
    ]
    understood = profile.get("understood") or []
    if understood:
        lines.append(f"- Already understands: {', '.join(understood)}. Use these terms WITHOUT re-defining them.")
    lines.append("- Explain any other finance term in plain words the first time you use it.")
    if profile.get("simpler"):
        lines.append("- They asked for SIMPLER answers: one idea at a time, everyday words, an everyday example, "
                     "fewer numbers (only the 1-2 most relevant).")
    return "\n".join(lines)


def build_prompt(question: str, path: str, profile: dict, facts: str, chunks: list,
                 feedback: list[str] | None = None, history: list[str] | None = None) -> str:
    kb = "\n\n".join(f"[{c.id}] {c.title}\n{c.text}" for c in chunks)
    parts = [
        "INVESTOR PROFILE\n" + _profile_text(profile),
        "SIP FACTS (Your SIP data, computed by the app; the only numbers you may use)\n" + facts,
        "KNOWLEDGE\n" + kb,
    ]
    if history:
        parts.append("EARLIER QUESTIONS IN THIS SESSION\n" + "\n".join(f"- {h}" for h in history[-3:]))
    if path == "decline":
        parts.append(DECLINE_ADDON.strip())
    if feedback:
        parts.append("YOUR PREVIOUS ATTEMPT FAILED THESE QUALITY CHECKS. Fix them:\n" +
                     "\n".join(f"- {f}" for f in feedback))
    parts.append(f"QUESTION\n{question}")
    lang = profile.get("language", "hinglish")
    parts.append("REPLY LANGUAGE: " + ("Hinglish in Roman script (e.g. 'Aapke 412.15 units aapke hi hain'), even if "
                                       "the question is in English." if lang == "hinglish" else
                                       "simple English, even if the question is in Hinglish."))
    return "\n\n".join(parts)


RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "answer": {"type": "STRING"},
        "numbers_used": {"type": "ARRAY", "items": {"type": "STRING"}},
        "sources": {"type": "ARRAY", "items": {"type": "STRING"}},
        "terms_explained": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["answer", "numbers_used", "sources", "terms_explained"],
}


TRANSIENT = ("503", "504", "429", "UNAVAILABLE", "DEADLINE", "RESOURCE_EXHAUSTED", "Timeout", "timed out")


def call_json(system: str, prompt: str, schema: dict, temperature: float = 0.3) -> dict:
    from google.genai import types
    models = [config.model_name()]
    fb = config.fallback_model()
    if fb and fb not in models:
        models.append(fb)
    text, last_err = None, None
    for model in models:
        try:
            resp = get_client().models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=temperature,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            text = resp.text or ""
            break
        except LLMError:
            raise
        except Exception as e:  # timeout, quota (429), overload (503), network, safety block...
            last_err = e
            if not any(t in f"{type(e).__name__} {e}" for t in TRANSIENT):
                break
    if text is None:
        raise LLMError(f"{type(last_err).__name__}: {str(last_err)[:200]}") from last_err
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError("model did not return valid JSON") from e
    if not isinstance(data, dict):
        raise LLMError("model returned non-object JSON")
    return data


def generate(question: str, path: str, profile: dict, facts: str, chunks: list,
             feedback: list[str] | None = None, history: list[str] | None = None) -> dict:
    data = call_json(SYSTEM_PROMPT, build_prompt(question, path, profile, facts, chunks, feedback, history),
                     RESPONSE_SCHEMA)
    return {
        "answer": str(data.get("answer", "")).strip(),
        "numbers_used": [str(x) for x in data.get("numbers_used", []) or []],
        "sources": [str(x) for x in data.get("sources", []) or []],
        "terms_explained": [str(x) for x in data.get("terms_explained", []) or []],
    }


JUDGE_SYSTEM = """You grade an AI answer for a golden-set evaluation. Be strict but fair.
For each MUST_INCLUDE item: true if the answer clearly conveys that fact or idea (any language, paraphrase ok;
numbers must match). For each MUST_NOT_INCLUDE item: true if the answer contains or implies it
("any fund name" means any real or made-up fund/stock name other than the user's own fictional fund).
Return JSON only."""

JUDGE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "must_include": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "item": {"type": "STRING"}, "present": {"type": "BOOLEAN"}}, "required": ["item", "present"]}},
        "must_not_include": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "item": {"type": "STRING"}, "present": {"type": "BOOLEAN"}}, "required": ["item", "present"]}},
    },
    "required": ["must_include", "must_not_include"],
}


def judge(question: str, answer: str, must_include: list[str], must_not: list[str]) -> dict:
    prompt = (f"QUESTION: {question}\n\nANSWER:\n{answer}\n\n"
              f"MUST_INCLUDE: {json.dumps(must_include, ensure_ascii=False)}\n"
              f"MUST_NOT_INCLUDE: {json.dumps(must_not, ensure_ascii=False)}")
    data = call_json(JUDGE_SYSTEM, prompt, JUDGE_SCHEMA, temperature=0.0)
    inc = {d.get("item", ""): bool(d.get("present")) for d in data.get("must_include", [])}
    exc = {d.get("item", ""): bool(d.get("present")) for d in data.get("must_not_include", [])}
    return {"include": [inc.get(i, False) for i in must_include], "exclude": [exc.get(i, False) for i in must_not]}
