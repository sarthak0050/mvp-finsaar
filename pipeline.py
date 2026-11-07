"""One answer, end to end: intent rule -> retrieve -> generate -> gate -> retry -> fallback.
Shared by the app and the eval page so both test exactly the same path."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import calc
import config
import gate
import llm
import rag

# ---------- 1. intent rules (before any AI) ----------

DECLINE_PATTERNS = [
    r"\bshould (i|we)\b", r"\bshall i\b", r"\bwhat should\b", r"\bkya (karu|karun|karoon|karein|karen)\b",
    r"\b(karna|karni) chahiye\b", r"\bchahiye kya\b", r"\b(band|stop|pause|continue|rok)\s*(kar|kr)?\s*(du|dun|doon|u|un|oon|de|den|dein)\b",
    r"\bwhich fund\b", r"\bbest fund\b", r"\bbetter fund\b", r"\b(kaunsa|konsa|kaun sa|kon sa) fund\b", r"\bswitch\b",
    r"\brecommend", r"\bsuggest", r"\bgood time to\b", r"\bsahi (rahega|hai kya)\b", r"\bworth (continuing|it)\b",
    r"\b(sell|redeem|withdraw)\b", r"\b(buy|invest) more\b(?!\s+units)", r"\bnikaal\b", r"\bbech\b",
]
PREDICT_PATTERNS = [
    r"\bwill (it|my|the|this|nav|market|markets|value|sip|fund)\b", r"\brecover", r"\bnext (year|month|week)\b",
    r"\bfuture\b", r"\bpredict", r"\bforecast", r"\bhow much will\b", r"\bgoing to (rise|fall|go|recover|grow)\b",
    r"\bkab tak\b", r"\bwap(a|aa)s aa", r"\bbadhega\b", r"\bgirega\b", r"\b(upar|neeche|niche|wap(a|aa)s)\s+(jayega|jaayega|aayega|aa jayega)\b", r"\bkitna ho (jayega|jaega)\b", r"\baage kya\b",
]
FUND_PATTERNS = [r"\bwhich fund\b", r"\bbest fund\b", r"\bbetter fund\b", r"\b(kaunsa|konsa|kaun sa|kon sa) fund\b", r"\bswitch\b",
                 r"\brecommend", r"\bstock\b"]


def classify(question: str) -> str:
    q = question.lower()
    if any(re.search(p, q) for p in DECLINE_PATTERNS):
        return "decline"
    if any(re.search(p, q) for p in PREDICT_PATTERNS):
        return "uncertain"
    return "answer"


def _is_fund_q(question: str) -> bool:
    return any(re.search(p, question.lower()) for p in FUND_PATTERNS)


# ---------- templates (deterministic, also gated) ----------

def templates(s: calc.SipSummary) -> dict:
    u, inv, val = f"{s.total_units:.2f}", calc.inr(s.invested), calc.inr(s.current_value)
    return {
        "decline": {
            "english": (f"I can't tell you what to do with your SIP, but here is what each option means. "
                        f"Pause: no instalments for a set time, then the SIP restarts. Skip: only the next "
                        f"instalment is missed. Change amount: future instalments use a new amount. Stop: no new "
                        f"instalments. In every case, the {u} units you already hold stay yours until you redeem "
                        f"them. The decision is yours."),
            "hinglish": (f"Main yeh nahi bata sakta ki SIP ke saath kya karein, par har option ka matlab yeh hai. "
                         f"Pause: kuch time instalment nahi kategi, phir SIP khud shuru hogi. Skip: sirf agli "
                         f"instalment nahi kategi. Change amount: aage ki instalments naye amount se. Stop: aage "
                         f"koi nayi instalment nahi. Har case mein aapke {u} units aapke hi rehte hain, jab tak aap "
                         f"redeem na karein. Faisla aapka hai (the decision is yours)."),
        },
        "fund": {
            "english": (f"I can't recommend any fund or stock, or say whether to change funds. FinSaar only "
                        f"explains your own SIP. Today your {u} units are worth {val} against {inv} invested. "
                        f"For advice on your situation, you can speak to a SEBI-registered investment adviser. "
                        f"The decision is yours."),
            "hinglish": (f"Main koi fund ya stock recommend nahi kar sakta (I can't recommend any fund). FinSaar "
                         f"sirf aapki apni SIP samjhata hai. Aaj aapke {u} units ki value {val} hai, aur invested "
                         f"{inv}. Apni situation ke liye SEBI-registered investment adviser se baat kar sakte hain. "
                         f"Faisla aapka hai (the decision is yours)."),
        },
        "predict": {
            "english": ("I can't predict future NAV, value or market moves. No one can know them in advance, "
                        "so I won't guess. Here is where your SIP stands today, from your own data."),
            "hinglish": ("Main future NAV, value ya market predict nahi kar sakta (I can't predict). Yeh pehle se "
                         "koi nahi jaanta, isliye main guess nahi karunga. Aaj aapki SIP kahan hai, yeh aapke "
                         "apne data se:"),
        },
        "unsure": {
            "english": "I'm not sure about this one, so I won't guess. Here are your plain numbers, and the official source has more.",
            "hinglish": "Is sawaal par main sure nahi hoon, isliye guess nahi karunga. Yeh rahe aapke seedhe numbers, aur official source mein aur jaankari hai.",
        },
        "error": {
            "english": "FinSaar's AI is busy right now, so here are your numbers straight from your SIP data. Please try again in a minute.",
            "hinglish": "FinSaar ka AI abhi busy hai, isliye yeh rahe aapke numbers seedhe aapke SIP data se. Ek minute baad phir try karein.",
        },
    }


# ---------- result ----------

@dataclass
class Result:
    question: str
    path: str                 # answer | decline | uncertain  (what the user ended up seeing)
    intent: str               # what the rule decided
    kind: str                 # ai | template | fallback-unsure | fallback-error | limit
    answer: str
    sources: list[str] = field(default_factory=list)
    numbers_used: list[str] = field(default_factory=list)
    terms_explained: list[str] = field(default_factory=list)
    gate: gate.GateResult | None = None
    attempts: list[dict] = field(default_factory=list)   # each AI try + its gate reasons
    chunks: list = field(default_factory=list)
    retrieval: str = ""
    show_numbers: bool = False
    error: str = ""

    @property
    def gate_passed(self) -> bool:
        return bool(self.gate and self.gate.passed)


def stage_text(s: calc.SipSummary) -> str:
    n = s.n_instalments
    when = "just made the very first instalment" if n == 1 else f"{n} monthly instalments into their first SIP"
    return f"{when}; value is {s.status_word} the amount invested"


def answer(question: str, profile: dict, history: list[str] | None = None, scenario: str | None = None) -> Result:
    s = calc.compute(scenario=scenario)
    profile = {**profile, "stage": stage_text(s)}
    facts = calc.facts_block(s)
    nums = calc.allowed_numbers(s)
    lang = profile.get("language", "hinglish")
    level = profile.get("level", "beginner")
    T = templates(s)
    intent = classify(question)

    chunks, method = rag.retrieve(question, k=3)
    if intent == "decline":
        k8 = [c for c in rag.load_chunks() if c.id in ("K8", "K9")]
        chunks = (k8 + [c for c in chunks if c.id not in ("K8", "K9")])[:3]
    allowed_src = [rag.SIP_SOURCE] + [c.label for c in chunks]

    def gated(text: str, sources: list[str], path: str) -> gate.GateResult:
        return gate.run_gate(text, sources, nums, allowed_src, level, path)

    def template_result(key: str, path: str, kind: str, show_numbers: bool, err: str = "", attempts=None) -> Result:
        text = T[key][lang]
        srcs = [rag.SIP_SOURCE] + ([c.label for c in chunks if c.id in ("K8", "K9")] if path == "decline" else [])
        return Result(question, path, intent, kind, text, srcs, [], [], gated(text, srcs, path),
                      attempts or [], chunks, method, show_numbers, err)

    # prediction questions: deterministic, never sent to the model
    if intent == "uncertain":
        return template_result("predict", "uncertain", "template", True)

    attempts, feedback = [], None
    for _ in range(2):
        try:
            out = llm.generate(question, intent, profile, facts, chunks, feedback, history)
        except llm.LLMError as e:
            if intent == "decline":
                return template_result("fund" if _is_fund_q(question) else "decline", "decline",
                                       "fallback-error", False, str(e), attempts)
            return template_result("error", "uncertain", "fallback-error", True, str(e), attempts)
        g = gated(out["answer"], out["sources"], intent)
        attempts.append({"answer": out["answer"], "passed": g.passed, "reasons": g.reasons})
        if g.passed:
            return Result(question, intent, intent, "ai", out["answer"], out["sources"], out["numbers_used"],
                          out["terms_explained"], g, attempts, chunks, method)
        feedback = g.reasons

    if intent == "decline":
        return template_result("fund" if _is_fund_q(question) else "decline", "decline", "template", False,
                               attempts=attempts)
    return template_result("unsure", "uncertain", "fallback-unsure", True, attempts=attempts)


def default_profile(key: str = "beginner-hinglish") -> dict:
    level, lang = ("beginner", "hinglish") if key.startswith("beginner") else ("basics", "english")
    return {"level": level, "language": lang, "understood": [], "simpler": False}


LIMIT = config.SESSION_QUESTION_LIMIT
