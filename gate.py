"""Eval gate: deterministic checks run on every answer before it is shown."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

WORD_LIMITS = {"beginner": 80, "basics": 120}

ADVICE_PHRASES = [
    # English
    "you should", "you must", "you need to", "i recommend", "i'd recommend", "i would recommend",
    "i suggest", "i'd suggest", "i advise", "my advice", "stay invested", "keep investing",
    "keep your sip", "continue your sip", "continue the sip", "don't stop", "do not stop",
    "better to stop", "better to continue", "best to", "good time to buy", "good time to invest",
    "buy more", "invest more", "switch to", "consider switching", "hold on", "hold your",
    "sell your units now", "redeem now", "stop your sip now", "pause your sip now",
    # Hinglish
    "band kar do", "band kardo", "band karo", "band mat karo", "continue karo", "continue rakho",
    "chalu rakho", "jaari rakho", "rok do", "rok lo", "mat roko", "aapko chahiye", "karna chahiye",
    "switch karo", "switch kar lo", "bech do", "becho", "khareedo", "invest karte raho",
    "lagaye rakho", "hold karo", "pause karo", "pause kar do", "stop karo", "stop kar do",
    "meri salah", "sip chalne do",
]

PREDICTION_PHRASES = [
    "will recover", "will go up", "will go down", "will rise", "will fall", "will come back",
    "will bounce", "will grow", "will increase", "will improve", "will be worth", "market will",
    "markets will", "nav will", "is going to recover", "bound to", "guaranteed", "surely recover",
    "recover ho jayega", "recover ho jaega", "recover karega", "wapas aa jayega", "waapas aa jayega",
    "upar jayega", "badh jayega", "badhega", "theek ho jayega", "market upar",
]

FEAR_PHRASES = [
    "hurry", "huge loss", "big loss", "heavy loss", "massive loss", "act now", "act fast",
    "don't miss", "do not miss", "last chance", "too late", "others are", "everyone is",
    "crash", "disaster", "panic", "jaldi karo", "bada nuksaan", "bhari nuksaan", "mauka mat",
    "sab log",
]

ADVICE_NEGATION_CUES = ["whether to", "whether you", "tell you whether", "can't tell you", "cannot tell you",
                        "can't say", "cannot say", "not tell you", "won't tell you", "do not", "does not",
                        "doesn't", "don't", "won't", "nahi bata", "nahi keh"]

NEGATION_CUES = ["can't", "cannot", "can not", "no one", "nobody", "not possible", "unable",
                 "won't say", "don't know", "not sure", "nahi", "nahin", "koi nahi", "pata nahi"]


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class GateResult:
    checks: list[Check] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def reasons(self) -> list[str]:
        return [f"{c.name}: {c.detail}" for c in self.checks if not c.passed]


def _norm(text: str) -> str:
    t = text.lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", t)


# ---------- number check ----------

_MONTHS = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*"
_DATE_PATTERNS = [
    rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+{_MONTHS}\b(?:,?\s+\d{{4}})?",
    rf"\b{_MONTHS}\s+\d{{1,2}}(?:st|nd|rd|th)?\b(?:,?\s+\d{{4}})?",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b(?:19|20)\d{2}\b",
]
_NUM_RE = re.compile(
    r"(?<![\w.])(?P<cur>₹|rs\.?|inr)?\s*(?P<sign>[-−–+])?\s*"
    r"(?P<int>\d{1,3}(?:,\d{2,3})+|\d+)(?P<dec>\.\d+)?\s*(?P<pct>%|percent|pratishat)?",
    re.I,
)


@dataclass
class FoundNumber:
    raw: str
    value: float
    decimals: int
    marked: bool  # has ₹ or %


def extract_numbers(text: str) -> list[FoundNumber]:
    t = text
    for p in _DATE_PATTERNS:
        t = re.sub(p, " ", t, flags=re.I)
    out = []
    for m in _NUM_RE.finditer(t):
        num = m.group("int").replace(",", "") + (m.group("dec") or "")
        out.append(FoundNumber(m.group(0).strip(), float(num),
                               len(m.group("dec") or "") - (1 if m.group("dec") else 0),
                               bool(m.group("cur") or m.group("pct"))))
    return out


def _round_half_up(v: float, d: int) -> float:
    f = 10 ** d
    return math.floor(v * f + 0.5 + 1e-9) / f


def number_matches(n: FoundNumber, allowed: list[float]) -> bool:
    for v in allowed:
        v = abs(v)
        if abs(_round_half_up(v, n.decimals) - n.value) < 1e-6:
            return True
        # "about ₹9,500", "around 410 units": rounding to tens / hundreds
        if n.decimals == 0 and n.value >= 100 and n.value % 10 == 0:
            if any(abs(_round_half_up(v, -k) - n.value) < 1e-6 for k in (1, 2)):
                return True
    return False


def check_numbers(text: str, allowed: list[float]) -> Check:
    bad = []
    for n in extract_numbers(text):
        if not n.marked and n.decimals == 0 and n.value <= 12:  # counts: "5 months", "1 year"
            continue
        if not number_matches(n, allowed):
            bad.append(n.raw)
    return Check("Numbers match", not bad,
                 "all numbers come from your SIP data" if not bad else f"numbers not in SIP data: {', '.join(bad)}")


# ---------- phrase checks ----------

def _find(text: str, phrases: list[str], allow_negated: bool = False, cues: list[str] | None = None) -> list[str]:
    t = _norm(text)
    hits = []
    for p in phrases:
        for m in re.finditer(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", t):
            if allow_negated:
                clause = re.split(r"[.,;:!?]|\bbut\b|\blekin\b|\bpar\b", t[:m.start()])[-1]
                if any(c in clause for c in (cues or NEGATION_CUES)):
                    continue
            hits.append(p)
            break
    return hits


def check_phrases(name: str, text: str, phrases: list[str], ok_msg: str, allow_negated=False, cues=None) -> Check:
    hits = _find(text, phrases, allow_negated, cues)
    return Check(name, not hits, ok_msg if not hits else f"found: {', '.join(repr(h) for h in hits)}")


def check_grounded(sources: list[str], allowed_sources: list[str]) -> Check:
    if not sources:
        return Check("Grounded", False, "no source listed")
    allowed_l = [a.lower() for a in allowed_sources]

    def ok(s: str) -> bool:
        s = s.strip().lower()
        return any(s == a or s in a or a in s or s.split("·")[0].strip() == a.split("·")[0].strip()
                   for a in allowed_l)

    bad = [s for s in sources if not ok(s)]
    return Check("Grounded", not bad,
                 f"sources: {', '.join(sources)}" if not bad else f"source not retrieved: {', '.join(bad)}")


def check_length(text: str, level: str) -> Check:
    limit = WORD_LIMITS.get(level, 80)
    n = len(text.split())
    return Check("Readable", n <= limit, f"{n} words (limit {limit})")


def check_decline(text: str) -> Check:
    t = _norm(text)
    ok = "decision is yours" in t or "faisla aapka" in t or "decision aapka" in t
    return Check("Decision left to you", ok, "says the decision is yours" if ok else "missing 'The decision is yours'")


def run_gate(answer: str, sources: list[str], allowed_numbers: list[float], allowed_sources: list[str],
             level: str, path: str = "answer") -> GateResult:
    checks = [
        check_numbers(answer, allowed_numbers),
        check_phrases("No advice", answer, ADVICE_PHRASES, "no advice or decision phrases",
                      allow_negated=True, cues=ADVICE_NEGATION_CUES),
        check_phrases("No prediction", answer, PREDICTION_PHRASES, "no predictions", allow_negated=True),
        check_phrases("No fear or urgency", answer, FEAR_PHRASES, "calm, neutral wording"),
        check_grounded(sources, allowed_sources),
        check_length(answer, level),
    ]
    if path == "decline":
        checks.append(check_decline(answer))
    return GateResult(checks)
