"""FinSaar — "Aapke SIP ka saar". A mobile-first concept app (Streamlit host + custom front end).

The UI lives in ui/finsaar.js + ui/finsaar.css (a Streamlit custom component). Python owns the data:
every number comes from calc.py, every answer goes through pipeline.py (intent rule → RAG → Gemini → gate),
and the Quality tab scores the gate against data/golden_set.csv.
"""
from __future__ import annotations

import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

import calc
import config
import pipeline

st.set_page_config(page_title="FinSaar · Aapke SIP ka saar", page_icon="🌱", layout="wide",
                   initial_sidebar_state="collapsed")

ROOT = Path(__file__).parent
UI = ROOT / "ui"
HISTORY = ROOT / "data" / "eval_history.json"
SEBI_LINK = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13"
TECH = re.compile(r"\b(xirr|nav|cagr|absolute return|expense ratio|annuali[sz]ed|avg nav|average nav)\b", re.I)
WHAT_IS = re.compile(r"\b(what is|what does|what's|meaning|matlab|kya hai|kya hota|explain)\b", re.I)

# Sample funds for Explore / Watchlist (fictional; the held fund's NAV comes from calc)
SAMPLE_FUNDS = [
    {"id": "flexi", "letter": "S", "color": "#1f7a4d", "name": "Sample Flexi Cap Fund", "cat": "Flexi Cap · Direct Growth",
     "type": "equity", "lower": False, "r1y": "+18.4%", "risk": "Very high", "held": True},
    {"id": "bluechip", "letter": "S", "color": "#3b5bdb", "name": "Sample Bluechip Fund", "cat": "Large Cap · Direct Growth",
     "type": "equity", "lower": False, "nav": "₹46.28", "r1y": "+14.8%", "risk": "Very high"},
    {"id": "balanced", "letter": "S", "color": "#e8590c", "name": "Sample Balanced Advantage", "cat": "Hybrid · Direct Growth",
     "type": "hybrid", "lower": True, "nav": "₹31.72", "r1y": "+11.2%", "risk": "Moderately high"},
    {"id": "smallcap", "letter": "S", "color": "#ae3ec9", "name": "Sample Small Cap Fund", "cat": "Small Cap · Direct Growth",
     "type": "equity", "lower": False, "nav": "₹62.14", "r1y": "+22.6%", "risk": "Very high"},
    {"id": "liquid", "letter": "S", "color": "#0c8599", "name": "Sample Liquid Fund", "cat": "Debt · Liquid · Direct Growth",
     "type": "debt", "lower": True, "nav": "₹1,012.40", "r1y": "+6.9%", "risk": "Low to moderate"},
]

GATE_RULES = [
    "gives advice — continue, pause, stop, switch, buy or sell (English or Hinglish)",
    "predicts returns or says a fall will recover",
    "uses fear or urgency (“huge loss”, “act now”)",
    "uses a number that isn’t in your SIP data",
    "lists no source, or a source it didn’t retrieve",
    "runs over the word limit (80 for beginners, 120 for “knows basics”)",
    "answers a decision question without saying the decision is yours",
]
AI_PLACE = ("A first-time SIP investor who sees a dip asks in their own words, often in Hinglish (“Iska matlab paisa doob "
            "gaya?”). AI turns that worry into an explanation built on their own units, NAV and XIRR, answers follow-ups, "
            "and adapts depth and language. A non-AI version can only show the same fixed card to everyone. Code still "
            "calculates every number, and the gate exists because a fluent model can slip into advice or comfort-predictions "
            "(“it will recover”).")


# ---------------- state ----------------

def init_state():
    ss = st.session_state
    ss.setdefault("scenario", "dip")
    ss.setdefault("lang", "Hinglish")
    ss.setdefault("turns", [])
    ss.setdefault("last_q", "")
    ss.setdefault("done_nonce", None)
    ss.setdefault("event_nonce", None)
    ss.setdefault("eval_done_nonce", None)
    ss.setdefault("q_count", 0)
    ss.setdefault("tech_uses", 0)
    ss.setdefault("session_runs", [])


def learned_level() -> str:
    """Level is learned, not chosen: starts at beginner; using terms like XIRR/NAV confidently → knows basics."""
    return "basics" if st.session_state.tech_uses >= 1 else "beginner"


def profile() -> dict:
    ss = st.session_state
    return {"level": learned_level(), "language": "hinglish" if ss.lang == "Hinglish" else "english",
            "understood": [], "simpler": False}


def summary() -> calc.SipSummary:
    return calc.compute(scenario=st.session_state.scenario)


# ---------------- answers ----------------

def run_question(q: str) -> pipeline.Result:
    ss = st.session_state
    s = summary()
    if TECH.search(q) and not WHAT_IS.search(q):
        ss.tech_uses += 1
    if ss.q_count >= pipeline.LIMIT:
        return pipeline.Result(q, "uncertain", "limit", "limit",
                               f"You've reached the {pipeline.LIMIT}-question limit for this demo session. "
                               "Here are your numbers from your SIP data.", ["Your SIP data"], show_numbers=True)
    ss.q_count += 1
    history = [t.question for t in ss.turns]
    try:
        return pipeline.answer(q, profile(), history, scenario=s.scenario)
    except Exception as e:  # never show a stack trace
        return pipeline.Result(q, "uncertain", "answer", "fallback-error",
                               pipeline.templates(s)["error"][profile()["language"]],
                               ["Your SIP data"], show_numbers=True, error=type(e).__name__)


def messages_payload(s: calc.SipSummary) -> list[dict]:
    out = []
    for r in st.session_state.turns:
        out.append({"role": "user", "text": r.question})
        if r.kind in ("fallback-error", "fallback-unsure", "limit"):
            footer = "warn"
            note = {"fallback-error": "FinSaar’s AI is busy — showing your plain numbers",
                    "fallback-unsure": "Not sure, so FinSaar won’t guess — your plain numbers",
                    "limit": "Question limit reached for this session"}[r.kind]
        else:
            footer, note = ("decline" if r.path == "decline" else "data"), ""
        nums = [list(x) for x in calc.numbers_summary(s)] if r.show_numbers else []
        out.append({"role": "bot", "text": r.answer, "footer": footer, "note": note, "numbers": nums})
    return out


# ---------------- data for the front end ----------------

def fmt_pct(x: float) -> str:
    return f"{'−' if x < 0 else '+'}{abs(x):.2f}%"


def build_payload() -> dict:
    ss = st.session_state
    s = summary()
    down, up = s.is_down, s.is_up
    tone = "neg" if down else "pos" if up else ""
    sign = "−" if down else "+" if up else ""
    od = s.one_day
    one_day = f"{'−' if od[0] < 0 else '+'}{calc.inr(od[0], 2)} ({abs(od[1]):.2f}%)" if od else "--"
    one_tone = ("neg" if od[0] < 0 else "pos") if od else ""
    trigger = down or bool(od and abs(od[1]) >= 1.0)
    xirr = calc.signed_pct(s.xirr_pct, 1) if s.xirr_pct is not None else "Not available"
    xirr_tone = ("neg" if s.xirr_pct < 0 else "pos") if s.xirr_pct is not None else ""
    nxt = s.next_instalment
    first = s.instalments[0].date
    vals = {
        "fund": s.fund, "fund_short": s.fund.replace(" (fictional)", ""), "value": calc.inr(s.current_value),
        "invested": calc.inr(s.invested), "ret_abs": f"{sign}{calc.inr(s.gain)}" if (down or up) else "₹0",
        "ret_pct": fmt_pct(s.gain_pct) if (down or up) else "0.00%", "ret_tone": tone, "xirr": xirr, "xirr_tone": xirr_tone,
        "units": f"{s.total_units:.2f}", "avg_nav": calc.inr(s.avg_nav, 2), "nav": calc.inr(s.current_nav, 2),
        "one_day": one_day, "one_tone": one_tone, "monthly": calc.inr(s.monthly_amount), "n": s.n_instalments,
        "next_short": f"{nxt.day:02d} {nxt.strftime('%b')}" if nxt else "--",
        "started": f"{first.day:02d} {first.strftime('%b %Y')}",
    }
    tx = [{"short": f"{i.date.day:02d} {i.date.strftime('%b')}", "amount": calc.inr(i.amount), "units": f"{i.units:.2f}",
           "nav": f"{i.nav:.2f}"} for i in reversed(s.instalments)]
    gap = "below" if s.nav_drop > 0 else "above"
    metrics = {
        "value": {"title": "Current value", "based": "Your units · today’s NAV", "ask": "What does my current value mean?",
                  "text": f"What your units are worth at today’s NAV: units × NAV. Yours is {vals['value']} "
                          f"({vals['units']} units × {vals['nav']}). It moves every day with the NAV."},
        "oneday": {"title": "1D returns", "based": "Today’s and yesterday’s NAV", "ask": "Why did my value change today?",
                   "text": f"How much your value moved since yesterday’s NAV: {one_day}. It shows one day’s change only."},
        "invested": {"title": "Invested amount", "based": "Your SIP transaction history", "ask": "How much have I invested?",
                     "text": f"This is the total amount recorded as paid into your SIP so far: {vals['invested']} "
                             f"({s.n_instalments} instalments of {vals['monthly']})."},
        "returns": {"title": "Total returns", "based": "Your visible portfolio data", "ask": "Kya mera paisa doob gaya?",
                    "text": f"This compares your current value with the amount invested: {vals['ret_abs']} ({vals['ret_pct']}). "
                            "It does not predict what happens next."},
        "xirr": {"title": "XIRR", "based": "Investor education context · your SIP dates", "ask": "XIRR itna alag kyun hai?",
                 "text": (f"XIRR is a yearly (annualised) return that considers when each instalment went in. Yours is {xirr}. "
                          "In the first months, a small change can look large as a yearly rate.") if s.xirr_pct is not None else
                         "XIRR isn’t shown yet — there isn’t enough time since your first instalment to turn into a yearly rate."},
        "units": {"title": "Units", "based": "Your SIP transaction history", "ask": "Why are units up but value down?",
                  "text": f"What your instalments bought: {vals['units']} units. A NAV change moves their price, not how many you own."},
        "avgnav": {"title": "Average NAV", "based": "Your transactions", "ask": "What is my average buy NAV?",
                   "text": f"Your average price per unit: invested ÷ units = {vals['avg_nav']}. Today’s NAV is {vals['nav']}, "
                           f"{calc.inr(abs(s.nav_drop), 2)} {gap} it."},
        "nav": {"title": "Current NAV", "based": "Fund NAV · sample data", "ask": "What does NAV mean for me?",
                "text": f"Today’s price of one unit, set at the end of each business day: {vals['nav']}."},
    }
    fund_metrics = {
        "nav": {"title": "Current NAV", "based": "Sample fund data", "ask": "What does NAV mean?",
                "text": "Today’s price of one unit of this fund: {nav}. It is set at the end of each business day."},
        "risk": {"title": "Risk level", "based": "Sample fund data", "ask": "What does a fund’s risk level mean?",
                 "text": "The fund’s risk label: {risk}. A higher level means its value can swing more, up or down."},
        "r1y": {"title": "1Y return (past)", "based": "Sample fund data", "ask": "What does 1Y return mean?",
                "text": "What the fund returned over the last year: {r1y}. Past returns don’t indicate future returns."},
    }
    understand = {
        "items": [
            ["What changed", f"Today’s NAV is {vals['nav']}; your average buy NAV is {vals['avg_nav']}."],
            ["What you still own", f"You still hold {vals['units']} units. A NAV change moves their price, not how many you have."],
            ["What the number means", f"At today’s NAV your units are worth {vals['value']} on {vals['invested']} invested. "
                                      "This changes when NAV changes, and becomes final only if units are redeemed."],
            ["Your choices", "Continue, pause, skip or stop are options for any SIP. FinSaar won’t pick one for you; "
                             "the decision is yours."],
        ],
        "chips": ["Iska matlab paisa doob gaya?", "Why are my units going up but value going down?", "Should I stop my SIP?"],
    }
    funds = []
    for f in SAMPLE_FUNDS:
        g = dict(f)
        if g.get("held"):
            g["nav"] = vals["nav"]
        funds.append(g)
    chips = (["Iska matlab paisa doob gaya?", "XIRR ko simple mein samjhao", "Should I stop and move to a better fund?"]
             if down else ["What does XIRR mean for me?", "Why is my value up?", "Should I invest more?"])
    return {
        "scenario": ss.scenario, "lang": ss.lang, "s": vals, "tx": tx, "trigger": trigger,
        "dip_line": f"{vals['value']} today on {vals['invested']} invested ({vals['ret_pct']}). NAV changes every day; "
                    f"your {vals['units']} units stay the same.",
        "why_text": "FinSaar shows this when today's value is under the amount invested, or NAV moves 1% or more in a day. "
                    "It's an explanation, not a signal to act.",
        "metrics": metrics, "fund_metrics": fund_metrics, "understand": understand, "funds": funds, "held_id": "flexi",
        "messages": messages_payload(s), "last_q": ss.last_q, "chips": chips, "done_nonce": ss.done_nonce,
        "eval_done_nonce": ss.eval_done_nonce,
        "links": {"amfi": config.amfi_link(), "sebi": SEBI_LINK},
        "eval": eval_payload(),
    }


# ---------------- quality / eval ----------------

def load_golden() -> list[dict]:
    with open(ROOT / "data" / "golden_set.csv", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_history() -> list[dict]:
    try:
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    except Exception:
        return []


def eval_payload() -> dict:
    runs = st.session_state.session_runs + load_history()
    runs = sorted(runs, key=lambda r: r.get("ts", 0), reverse=True)
    n = len(runs)
    for i, r in enumerate(runs):
        r["label"] = f"Run {n - i}"
    golden = [{"id": g["id"], "question": g["question"], "profile": g["profile"], "source": g.get("source", ""),
               "expected": g["expected_path"]} for g in load_golden()]
    return {"runs": runs, "golden": golden, "gate_rules": GATE_RULES, "ai_place": AI_PLACE,
            "passcode_required": bool(config.get("EVAL_PASSCODE"))}


def run_golden_set() -> dict:
    import eval_page
    model = config.model_name()
    rows = []
    for g in eval_page.load_golden():
        try:
            r = eval_page.score_row(g, model)
        except Exception as e:
            r = {"id": g["id"], "passed": False, "gate_passed": False, "must_include_ok": False,
                 "must_not_include_ok": False, "path_ok": False, "reasons": f"error: {type(e).__name__}", "answer": ""}
        rows.append({"id": r["id"], "passed": bool(r["passed"]), "gate": bool(r["gate_passed"]),
                     "include": bool(r["must_include_ok"]), "exclude": bool(r["must_not_include_ok"]),
                     "path": bool(r["path_ok"]), "answer": r.get("answer", ""), "reasons": r.get("reasons", "")})
        time.sleep(1.0)
    now = datetime.now(timezone.utc)
    run = {"id": now.strftime("%Y%m%d%H%M%S"), "ts": now.timestamp(), "model": model,
           "at": now.strftime("%d %b %Y %H:%M UTC"), "passed": sum(r["passed"] for r in rows), "total": len(rows), "rows": rows}
    try:  # best effort: keep a history file (ephemeral on Streamlit Cloud)
        hist = load_history()
        HISTORY.write_text(json.dumps([run] + hist, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        st.session_state.session_runs.insert(0, run)
    return run


# ---------------- page ----------------

st.markdown("""<style>
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stSidebar"],
[data-testid="stStatusWidget"] { display: none !important; }
.stApp { background: #f3f6f4 !important; }
.block-container { padding: 0 !important; max-width: none !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
</style>""", unsafe_allow_html=True)

init_state()
APP = st.components.v2.component(
    "finsaar_app",
    html="",
    css=(UI / "finsaar.css").read_text(encoding="utf-8"),
    js=(UI / "finsaar.js").read_text(encoding="utf-8"),
)
result = APP(data=build_payload(), key="finsaar", on_ask_change=lambda: None, on_event_change=lambda: None)

ss = st.session_state
ask = getattr(result, "ask", None)
event = getattr(result, "event", None)
if ask and ask.get("nonce") != ss.done_nonce:
    q = str(ask.get("q", "")).strip()[:300]
    if q:
        ss.turns.append(run_question(q))
        ss.last_q = q
    ss.done_nonce = ask.get("nonce")
    st.rerun()
if event and event.get("nonce") != ss.event_nonce:
    ss.event_nonce = event.get("nonce")
    kind = event.get("type")
    if kind == "lang" and event.get("value") in ("English", "Hinglish"):
        ss.lang = event["value"]
    elif kind == "scenario" and event.get("value") in ("regular", "dip"):
        ss.scenario = event["value"]
    elif kind == "newchat":
        ss.turns = []
    elif kind == "reset":
        for k in ("turns", "last_q", "tech_uses", "q_count"):
            ss.pop(k, None)
        init_state()
    elif kind == "runeval":
        code = config.get("EVAL_PASSCODE")
        if not code or event.get("passcode") == code:
            run_golden_set()
        ss.eval_done_nonce = event.get("nonce")
    st.rerun()
