"""FinSaar: Aapke SIP ka saar. A concept feature shown inside a Groww-style phone app (Streamlit)."""
from __future__ import annotations

import hashlib
import html

import streamlit as st

import calc
import config
import pipeline
import ui_style

st.set_page_config(page_title="FinSaar · Aapke SIP ka saar", page_icon="🌱", layout="wide",
                   initial_sidebar_state="collapsed")

PROFILES = {"Beginner · Hinglish": "beginner-hinglish", "Knows basics · English": "basics-english"}
PROFILE_HELP = {"Beginner · Hinglish": "First SIP, no finance background, prefers Hinglish",
                "Knows basics · English": "Knows what NAV is, prefers English"}
SCENARIOS = {sc["id"]: sc["label"] for sc in calc.scenarios()}
DEFAULT_SCENARIO = calc.load_sip().get("default_scenario", "dip")
TERM_ORDER = ["NAV", "Units", "XIRR", "Average buy NAV"]
TERM_QUESTION = {"NAV": "What does NAV mean for me?", "Units": "What do my units mean for me?",
                 "XIRR": "What does XIRR mean for me?", "Average buy NAV": "What is my average buy NAV?"}
TASK = ("Your SIP is down. Find out whether you've lost money and what your XIRR means. "
        "Then ask whether you should stop.")


# ---------- what FinSaar offers for this SIP right now ----------

def moment(s: calc.SipSummary) -> dict:
    xirr_txt = calc.signed_pct(s.xirr_pct, 1) if s.xirr_pct is not None else None
    if s.scenario == "start":
        chips = ["What did my first ₹2,000 buy?", "What is NAV?", "Why is XIRR not shown yet?"]
        tiles = {"Returns": "Why are my returns zero?", "XIRR": "Why is XIRR not shown yet?", "Units": f"What do my {s.total_units:.2f} units mean?",
                 "NAV": "What does NAV mean for me?"}
        nudge_q = "What did my first ₹2,000 buy?"
    elif s.is_up:
        chips = ["Why is my value up?", "What does XIRR mean for me?", "Should I invest more?"]
        tiles = {"Returns": "Why is my value up?", "XIRR": f"What does my XIRR of {xirr_txt} mean for me?",
                 "Units": f"What do my {s.total_units:.2f} units mean?", "NAV": "What does NAV mean for me?"}
        nudge_q = "Why is my value up?"
    else:
        chips = ["Iska matlab paisa doob gaya?", "Why are units up but value down?", "What does XIRR mean for me?",
                 "Should I stop and move to a better fund?"]
        tiles = {"Returns": "Iska matlab paisa doob gaya?", "XIRR": f"What does my XIRR of {xirr_txt} mean for me?",
                 "Units": "Why are units up but value down?", "NAV": "What does NAV mean for me?"}
        nudge_q = "Iska matlab paisa doob gaya?"
    return {"chips": chips, "tiles": tiles, "nudge_q": nudge_q}


def sheet_facts(metric: str, s: calc.SipSummary) -> tuple[str, str, list[str]]:
    """What the term is (plain definition) and 'your number' (from calc). The AI only adds 'what it means now'."""
    inv, val, n = calc.inr(s.invested), calc.inr(s.current_value), s.n_instalments
    if metric == "XIRR":
        what = "Your yearly rate of return, adjusted for the dates on which you invested each instalment."
        if s.xirr_pct is None:
            mine = "Not shown yet: your money was invested today, so there is no time period to turn into a yearly rate."
            follow = ["What did my first ₹2,000 buy?"]
        else:
            mine = f"{calc.signed_pct(s.xirr_pct, 1)} a year, from {n} instalments of {calc.inr(s.monthly_amount)} ({inv}) now worth {val}."
            follow = [f"Why is it so different from {calc.signed_pct(s.gain_pct, 2)}?", "Will my XIRR stay this low?"]
    elif metric == "Returns":
        what = "How far your investment is above or below what you put in. It stays a paper gain or loss until you redeem."
        if s.is_down or s.is_up:
            mine = (f"{calc.inr(s.gain)} {'below' if s.is_down else 'above'} invested: {val} today against {inv} "
                    f"({calc.signed_pct(s.gain_pct, 2)}).")
        else:
            mine = f"{val} today, the same as the {inv} you invested."
        follow = ["Why are units up but value down?", "Should I stop?"] if s.is_down else ["What does XIRR mean for me?"]
    elif metric == "NAV":
        what = "The price of one unit of the fund. It is worked out at the end of every business day."
        mine = f"{calc.inr(s.current_nav, 2)} today. You bought at an average of {calc.inr(s.avg_nav, 2)} per unit."
        follow = ["Is a lower NAV bad for me?", "Why did I get more units in October?"]
    else:
        what = "What your money bought. Each instalment buys units at that day's NAV, and they stay yours until you redeem."
        mine = f"{s.total_units:.2f} units from {n} instalment{'s' if n > 1 else ''} of {calc.inr(s.monthly_amount)}."
        follow = ["Iska matlab paisa doob gaya?", "Why are units up but value down?"]
    return what, mine, follow


# ---------- state ----------

def init_state():
    ss = st.session_state
    ss.setdefault("profile_label", "Beginner · Hinglish")
    ss.setdefault("scenario", DEFAULT_SCENARIO)
    ss.setdefault("understood", [])
    ss.setdefault("simpler", False)
    ss.setdefault("turns", [])
    ss.setdefault("feedback_done", set())
    ss.setdefault("card_dismissed", False)
    ss.setdefault("q_count", 0)
    ss.setdefault("pending", None)
    ss.setdefault("hint", "")
    ss.setdefault("sheet_cache", {})
    ss.setdefault("screen", "mf")        # mf | fund | chat
    ss.setdefault("tab", "Dashboard")    # Explore | Dashboard | SIPs | Watchlist
    ss.setdefault("sheet", None)         # XIRR | NAV | Units | ✦ question
    ss.setdefault("visit", 1)
    ss.setdefault("explained", [])       # terms explained in earlier answers (for "Last time: …")
    ss.setdefault("chat_back", "mf")


def current_profile() -> dict:
    p = pipeline.default_profile(PROFILES[st.session_state.profile_label])
    p["understood"] = list(st.session_state.understood)
    p["simpler"] = st.session_state.simpler
    return p


def go(screen: str):
    st.session_state.screen = screen
    st.session_state.sheet = None


def ask(question: str):
    """Open the FinSaar chat with this question."""
    ss = st.session_state
    if ss.screen != "chat":
        ss.chat_back = ss.screen
    ss.pending = question
    ss.hint = ""
    go("chat")


def canonical_term(t: str) -> str:
    low = t.strip().lower()
    for key, name in [("average", "Average buy NAV"), ("xirr", "XIRR"), ("annuali", "XIRR"),
                      ("absolute", "Absolute return"), ("nav", "NAV"), ("unit", "Units"),
                      ("current value", "Current value"), ("sip", "SIP"), ("redeem", "Redeem")]:
        if key in low:
            return name
    return t.strip().capitalize()


def remember_explained(r: pipeline.Result):
    for t in r.terms_explained:
        name = canonical_term(t)
        if name in TERM_ORDER:
            ex = st.session_state.explained
            if name in ex:
                ex.remove(name)
            ex.append(name)


def run_question(q: str, s: calc.SipSummary) -> pipeline.Result:
    """One question through the full pipeline, with the session limit and a last-resort guard."""
    if st.session_state.q_count >= pipeline.LIMIT:
        return pipeline.Result(q, "uncertain", "limit", "limit",
                               f"You've reached the {pipeline.LIMIT}-question limit for this demo session. "
                               "Here are your numbers from your SIP data.", ["Your SIP data"], show_numbers=True)
    st.session_state.q_count += 1
    history = [t.question for t in st.session_state.turns]
    try:
        r = pipeline.answer(q, current_profile(), history, scenario=s.scenario)
    except Exception as e:  # never show a stack trace
        r = pipeline.Result(q, "uncertain", "answer", "fallback-error",
                            pipeline.templates(s)["error"][current_profile()["language"]],
                            ["Your SIP data"], show_numbers=True, error=type(e).__name__)
    remember_explained(r)
    return r


# ---------- control-panel callbacks ----------

def on_profile():
    st.session_state.profile_label = st.session_state.w_profile or st.session_state.profile_label


def _clear_conversation():
    ss = st.session_state
    ss.turns, ss.feedback_done, ss.hint, ss.pending = [], set(), "", None
    ss.card_dismissed = False
    ss.sheet = None
    ss.screen = "mf"
    ss.tab = "Dashboard"


def on_scenario():
    st.session_state.scenario = st.session_state.w_scenario or st.session_state.scenario
    _clear_conversation()


def on_next_visit():
    """Come back later: the conversation is gone, what FinSaar learned stays (within this session)."""
    _clear_conversation()
    st.session_state.visit += 1


def on_reset():
    keep = {"profile_label"}
    for k in list(st.session_state.keys()):
        if k not in keep:
            del st.session_state[k]


# ---------- answer callbacks ----------

def on_chip():
    q = st.session_state.get("chip")
    st.session_state.chip = None
    if q:
        ask(q)


def on_yes(i: int):
    r = st.session_state.turns[i]
    for t in r.terms_explained:
        name = canonical_term(t)
        if name and name not in st.session_state.understood:
            st.session_state.understood.append(name)
    st.session_state.feedback_done.add(i)
    st.session_state.hint = "Great. Ask another question whenever you like."


def on_simpler(i: int):
    st.session_state.simpler = True
    st.session_state.feedback_done.add(i)
    ask(st.session_state.turns[i].question)


def on_another(i: int):
    st.session_state.feedback_done.add(i)
    st.session_state.hint = "Pick a question below or type your own."


# ---------- rendering helpers ----------

def numbers_table(s: calc.SipSummary) -> str:
    rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>"
                   for k, v in calc.numbers_summary(s))
    return f'<table class="fs-nums">{rows}</table>'


def status_line(r: pipeline.Result) -> str:
    if r.kind == "fallback-error":
        return '<div class="fs-warn">⚠ AI busy · safe fallback shown · Source: your SIP data</div>'
    if r.kind == "fallback-unsure":
        return '<div class="fs-warn">⚠ Not sure, so FinSaar won\'t guess · plain numbers shown</div>'
    if r.kind == "limit":
        return '<div class="fs-warn">Question limit reached for this session</div>'
    if r.gate_passed:
        return '<div class="fs-check">✓ Checked: numbers match your data · no advice · Source: your SIP, AMFI</div>'
    return '<div class="fs-warn">⚠ Safe fallback shown</div>'


SEBI_FALLBACK = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13"


def sebi_link() -> str:
    # getattr: survives a hot reload where an older config module is still loaded
    fn = getattr(config, "sebi_link", None)
    return fn() if callable(fn) else SEBI_FALLBACK


def links_html(r: pipeline.Result) -> str:
    amfi = f'<a href="{html.escape(config.amfi_link())}" target="_blank">AMFI investor education</a>'
    if r.path == "decline":
        sebi = f'<a href="{html.escape(sebi_link())}" target="_blank">Find a SEBI-registered adviser</a>'
        return f'<div class="fs-links">{sebi} · {amfi}</div>'
    if r.show_numbers:
        return f'<div class="fs-links">Official source: {amfi}</div>'
    return ""


def answer_card(r: pipeline.Result, s: calc.SipSummary, show_question: bool = True, key: str = ""):
    if show_question:
        st.markdown(f'<div class="fs-q">{html.escape(r.question)}</div>', unsafe_allow_html=True)
    body = html.escape(r.answer).replace("\n", "<br>")
    pre = ('<div class="fs-outside">ⓘ Outside what I can help with</div>' if r.path == "decline" else "")
    extra = numbers_table(s) if r.show_numbers else ""
    st.markdown(f'<div class="fs-card"><div class="fs-label">✦ FinSaar · AI</div>{pre}{body}{extra}'
                f'{links_html(r)}{status_line(r)}</div>', unsafe_allow_html=True)
    with st.expander("How this answer was checked"):
        if r.gate:
            for c in r.gate.checks:
                st.markdown(f"{'✅' if c.passed else '❌'} **{c.name}**: {html.escape(c.detail)}")
        if len(r.attempts) > 1 or (r.attempts and not r.attempts[-1]["passed"]):
            for n, a in enumerate(r.attempts, 1):
                if not a["passed"]:
                    st.markdown(f"↻ Try {n} was blocked: {html.escape('; '.join(a['reasons']))}")
        st.markdown(f"**Route:** {r.intent} → shown as *{r.path}* ({r.kind})")
        st.markdown(f"**Numbers used:** {', '.join(r.numbers_used) or 'only the app-computed numbers above'}")
        st.markdown(f"**Sources:** {', '.join(r.sources)}")
        st.markdown(f"**Retrieved chunks** ({r.retrieval}):")
        for c in r.chunks:
            st.caption(f"{c.label}: {c.text[:200]}{'…' if len(c.text) > 200 else ''}")


def memory_line() -> str:
    bits = [f"{t} ✓" for t in st.session_state.understood]
    if st.session_state.simpler:
        bits.append("prefers simpler")
    bits.append("Hinglish" if PROFILES[st.session_state.profile_label].endswith("hinglish") else "English")
    return "FinSaar remembers: " + " · ".join(bits)


def ret_text(s: calc.SipSummary) -> tuple[str, str]:
    if s.is_down or s.is_up:
        return f"{'−' if s.is_down else '+'}{calc.inr(s.gain)} ({calc.signed_pct(s.gain_pct, 2).lstrip('+−')})", \
               ("neg" if s.is_down else "pos")
    return "₹0 (0.00%)", ""


def xirr_text(s: calc.SipSummary) -> str:
    return calc.signed_pct(s.xirr_pct, 1) if s.xirr_pct is not None else "--"


def status_bar():
    st.markdown('<div class="ph-status"><b>9:41</b><span>▂▄▆ 📶 🔋</span></div>', unsafe_allow_html=True)


def bottom_nav():
    sv = lambda d: f'<svg viewBox="0 0 24 24">{d}</svg>'
    items = [(sv('<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M6 15l4-4 3 3 5-6"/>'), "Stocks"),
             (sv('<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 16l6-6 4 4 8-8"/>'), "F&amp;O"),
             (sv('<circle cx="12" cy="12" r="8"/><path d="M12 4v8l6 5"/>'), "Mutual Funds"),
             (sv('<rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/>'), "Loans")]
    cells = "".join(f'<div class="{"on" if label == "Mutual Funds" else ""}" {ui_style.DEAD}><span>{icon}</span>{label}</div>'
                    for icon, label in items)
    st.markdown(f'<div class="gw-nav">{cells}</div>', unsafe_allow_html=True)


def tap_label(label: str, key: str, sheet: str):
    """A Groww-style dotted-underline label that opens the FinSaar sheet for that number."""
    if st.button(f"{label} :green[✦]", key=key, type="tertiary", help="What does this mean for me?"):
        st.session_state.sheet = sheet
        st.rerun()


def kv_row(label_html: str, value_html: str, tap: tuple[str, str] | None = None, key: str = ""):
    c1, c2 = st.columns([1.25, 1], vertical_alignment="center")
    if tap:
        with c1:
            tap_label(tap[0], key, tap[1])
    else:
        c1.markdown(f'<div class="gw-lbl">{label_html}</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="gw-val">{value_html}</div>', unsafe_allow_html=True)


# ---------- phone screens ----------

def mf_header():
    ss = st.session_state
    st.markdown(f'<div class="gw-head"><span class="gw-mark" {ui_style.DEAD}></span><span class="gw-title">Mutual Funds</span>'
                f'<span class="gw-icons" {ui_style.DEAD}><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#44475b" stroke-width="1.8"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg><span class="gw-av">A</span></span></div>', unsafe_allow_html=True)
    cols = st.container(key="mftabs").columns(4)
    for col, t in zip(cols, ["Explore", "Dashboard", "SIPs", "Watchlist"]):
        if col.button(t, key=f"tab_{t}", type="primary" if ss.tab == t else "tertiary", width="stretch"):
            ss.tab = t
            st.rerun()


def finsaar_inline(s: calc.SipSummary, m: dict):
    """Entry points 1 and 3: one quiet line under the holdings card, dismissible."""
    ss = st.session_state
    last = ss.explained[-1] if ss.explained else None
    nxt = next((t for t in TERM_ORDER if t not in ss.understood and t not in ss.explained), None)
    if ss.card_dismissed:
        return
    if ss.visit > 1 and last and nxt:
        text, cta, q = f"Last time: <b>{last}</b>. {nxt} next?", "Continue", TERM_QUESTION[nxt]
    elif s.is_down:
        text, cta, q = f"Your SIP is <b>{calc.inr(s.gain)} below</b> what you invested. Want to understand it?", \
                       "Explain this", m["nudge_q"]
    else:
        return
    with st.container(key="fsline"):
        st.markdown(f'<div class="fs-line"><span class="fs-dot">✦</span><span>{text}</span></div>', unsafe_allow_html=True)
        c1, c2, _ = st.columns([1.2, 1, 1])
        if c1.button(cta, key="fs_go", type="primary"):
            ss.card_dismissed = True
            ask(q)
            st.rerun()
        if c2.button("Not now", key="fs_later", type="tertiary"):
            ss.card_dismissed = True
            st.rerun()


def tab_dashboard(s: calc.SipSummary, m: dict):
    ret, tone = ret_text(s)
    od = s.one_day
    od_txt = (f'<span class="{"neg" if od[0] < 0 else "pos"}">{"−" if od[0] < 0 else "+"}{calc.inr(od[0], 2)} '
              f'({abs(od[1]):.2f}%)</span>') if od else "--"
    with st.container(key="holdcard"):
        st.markdown(f'<div class="gw-cap">HOLDINGS (1)</div><div class="gw-big">{calc.inr(s.current_value)}</div>'
                    f'<div class="gw-dash"></div>', unsafe_allow_html=True)
        kv_row("1D returns", od_txt)
        kv_row("", f'<span class="{tone}">{ret}</span>', tap=("Total returns", "Returns"), key="t_ret")
        kv_row("Invested", calc.inr(s.invested))
        kv_row("", f'<span class="{tone if s.xirr_pct is not None else ""}">{xirr_text(s)}</span>',
               tap=("XIRR (Active)", "XIRR"), key="t_xirr")
    finsaar_inline(s, m)
    st.markdown('<div class="gw-listhead"><span class="gw-filter" ' + ui_style.DEAD + '>☰</span>'
                '<span class="gw-dotted">Current (Invested)</span></div>', unsafe_allow_html=True)
    tone_c = {"neg": "neg", "pos": "pos"}.get(tone, "")
    with st.container(key="fundrow"):
        c1, c2 = st.columns([3, 1.1], vertical_alignment="center")
        if c1.button(f"{s.fund}  \n:gray[SIP]", key="open_fund", width="stretch"):
            go("fund")
            st.rerun()
        c2.markdown(f'<div class="gw-rowval"><span class="{tone_c}">{calc.inr(s.current_value)}</span>'
                    f'<br><small>({calc.inr(s.invested)})</small></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gw-pill-btn" {ui_style.DEAD}>⤓ Import external funds</div>', unsafe_allow_html=True)


def tab_sips(s: calc.SipSummary):
    nxt = s.next_instalment
    st.markdown(f'<div class="gw-card"><div class="gw-cap">MONTHLY SIP AMOUNT</div>'
                f'<div class="gw-big">{calc.inr(s.monthly_amount)}</div></div>'
                f'<div class="gw-sechead"><b>Active SIPs (1)</b><span class="gw-dotted" {ui_style.DEAD}>Sort by: Due date</span></div>',
                unsafe_allow_html=True)
    with st.container(key="siprow"):
        c0, c1, c2 = st.columns([0.7, 3, 0.9], vertical_alignment="center")
        c0.markdown('<span class="gw-tile" style="background:#1d6f42">SF</span>', unsafe_allow_html=True)
        if c1.button(f"{s.fund}  \n:gray[{calc.inr(s.monthly_amount)}]", key="open_fund_sip", width="stretch"):
            go("fund")
            st.rerun()
        if nxt:
            c2.markdown(f'<div class="gw-date"><b>{nxt.day:02d}</b><br>{nxt.strftime("%b")}</div>', unsafe_allow_html=True)


def tab_explore():
    cards = "".join(f'<div class="gw-fcard" {ui_style.DEAD}><span class="gw-tile" style="background:{c}">{i}</span>'
                    f'<div>{n}</div><div class="gw-muted">{cat}</div></div>'
                    for i, n, cat, c in [("SL", "Sample Large Cap Fund (fictional)", "Equity · Large Cap", "#5367ff"),
                                         ("SI", "Sample Index Fund (fictional)", "Equity · Index", "#00b386"),
                                         ("SD", "Sample Debt Fund (fictional)", "Debt · Short duration", "#f2994a"),
                                         ("SF", "Sample Flexi Cap Fund (fictional)", "Equity · Flexi Cap", "#1d6f42")])
    st.markdown(f'<div class="gw-sechead"><b>Popular Funds</b><span class="gw-muted" {ui_style.DEAD}>View all ›</span></div>'
                f'<div class="gw-grid">{cards}</div>', unsafe_allow_html=True)


def tab_watchlist():
    rows = "".join(f'<div class="gw-wrow" {ui_style.DEAD}><span class="gw-tile" style="background:{c}">{i}</span>'
                   f'<div><div>{n}</div><div class="gw-muted">{cat}</div></div></div>'
                   for i, n, cat, c in [("SL", "Sample Large Cap Fund (fictional)", "Equity · Large Cap", "#5367ff"),
                                        ("SI", "Sample Index Fund (fictional)", "Equity · Index", "#00b386")])
    st.markdown(f'<div class="gw-sechead"><span class="gw-muted">Mutual Funds</span></div>{rows}'
                f'<div class="gw-sechead"><span class="gw-link" {ui_style.DEAD}>Add funds</span>'
                f'<span class="gw-link" {ui_style.DEAD}>Edit watchlist</span></div>', unsafe_allow_html=True)


def screen_mf(s: calc.SipSummary, m: dict):
    mf_header()
    tab = st.session_state.tab
    if tab == "Dashboard":
        tab_dashboard(s, m)
    elif tab == "SIPs":
        tab_sips(s)
    elif tab == "Explore":
        tab_explore()
    else:
        tab_watchlist()
    bottom_nav()


def screen_fund(s: calc.SipSummary, m: dict):
    ss = st.session_state
    with st.container(key="backbtn"):
        b1, b2 = st.columns([1, 7], vertical_alignment="center")
        if b1.button("←", key="fund_back", type="tertiary"):
            go("mf")
            st.rerun()
        b2.markdown(f'<div class="gw-fhead"><span class="gw-tile" style="background:#1d6f42">SF</span>'
                    f'<span>{html.escape(s.fund)}</span></div>', unsafe_allow_html=True)
    ret, tone = ret_text(s)
    with st.container(key="holdcard"):
        st.markdown(f'<div class="gw-cap">CURRENT VALUE</div><div class="gw-big">{calc.inr(s.current_value)}</div>'
                    f'<div class="gw-dash"></div>', unsafe_allow_html=True)
        kv_row("Invested", calc.inr(s.invested))
        kv_row("", f'<span class="{tone}">{ret}</span>', tap=("Total returns", "Returns"), key="f_ret")
        kv_row("", f'<span class="{tone if s.xirr_pct is not None else ""}">{xirr_text(s)}</span>',
               tap=("XIRR", "XIRR"), key="f_xirr")
        kv_row("", f"{s.total_units:.2f}", tap=("Units", "Units"), key="f_units")
        kv_row("Avg. NAV", calc.inr(s.avg_nav, 2))
        kv_row("", calc.inr(s.current_nav, 2), tap=("Current NAV", "NAV"), key="f_nav")
    nxt = calc.fmt_date(s.next_instalment) if s.next_instalment else "--"
    st.markdown(f'<div class="gw-card gw-sip"><div><div class="gw-muted">SIP · Monthly</div><b>{calc.inr(s.monthly_amount)}</b></div>'
                f'<div style="text-align:right"><div class="gw-muted">Next instalment</div><b>{nxt}</b></div></div>'
                f'<div class="gw-manage" {ui_style.DEAD}>Manage SIP <span>›</span></div>'
                f'<div class="gw-sechead"><b>Transactions</b></div>', unsafe_allow_html=True)
    rows = "".join(f'<div class="gw-tx"><div>{calc.fmt_date(i.date)}<div class="gw-muted">SIP · {i.units:.2f} units at '
                   f'{i.nav:.2f}</div></div><div>{calc.inr(i.amount)}</div></div>' for i in reversed(s.instalments))
    st.markdown(rows, unsafe_allow_html=True)
    with st.container(key="fspill"):
        if st.button("✦ Ask FinSaar", key="pill_ask", type="primary"):
            ss.chat_back = "fund"
            go("chat")
            st.rerun()


def bottom_sheet(s: calc.SipSummary, m: dict):
    """Entry point 2: tap a number → 'What does this mean for me?' sheet, inside the phone."""
    ss = st.session_state
    metric = ss.sheet
    question = m["tiles"][metric]
    what, mine, follow = sheet_facts(metric, s)
    val = {"XIRR": xirr_text(s), "NAV": calc.inr(s.current_nav, 2), "Units": f"{s.total_units:.2f}",
           "Returns": ret_text(s)[0]}[metric]
    title = {"Returns": "Total returns", "NAV": "Current NAV"}.get(metric, metric)
    with st.container(key="sheet"):
        c1, c2 = st.columns([6, 1], vertical_alignment="center")
        c1.markdown(f'<div class="sh-grab"></div><div class="sh-title">{title} <span class="sh-val">{val}</span></div>',
                    unsafe_allow_html=True)
        if c2.button("✕", key="sheet_close", type="tertiary"):
            ss.sheet = None
            st.rerun()
        st.markdown(f'<div class="sh-sec">What it is</div><div class="sh-txt">{what}</div>'
                    f'<div class="sh-sec">Your number</div><div class="sh-txt">{mine}</div>'
                    f'<div class="sh-sec">For you now</div>', unsafe_allow_html=True)
        ck = f"{s.scenario}|{question}|{ss.profile_label}|{ss.simpler}"
        kh = hashlib.md5(ck.encode()).hexdigest()[:10]
        if ck not in ss.sheet_cache:
            with st.spinner("FinSaar is reading your SIP…"):
                r = run_question(question, s)
            ss.sheet_cache[ck] = r
            ss.turns.append(r)
            ss.feedback_done.add(len(ss.turns) - 1)
        r = ss.sheet_cache[ck]
        answer_card(r, s, show_question=False)
        b1, b2, b3 = st.container(key=f"fbsheet{kh}").columns(3)
        if b1.button("Yes, clear", key=f"sy{kh}", type="primary"):
            for t in r.terms_explained:
                name = canonical_term(t)
                if name and name not in ss.understood:
                    ss.understood.append(name)
            ss.sheet = None
            st.rerun()
        if b2.button("Simpler", key=f"ss{kh}", disabled=ss.simpler):
            ss.simpler = True
            st.rerun()
        if b3.button("Ask more", key=f"sm{kh}"):
            ss.chat_back = ss.screen
            go("chat")
            st.rerun()
        with st.container(key="sheetchips"):
            for n, fq in enumerate(follow):
                if st.button(fq, key=f"sf{kh}{n}"):
                    ask(fq)
                    st.rerun()


def screen_chat(s: calc.SipSummary, m: dict):
    ss = st.session_state
    with st.container(key="backbtn"):
        b1, b2 = st.columns([1, 7], vertical_alignment="center")
        if b1.button("←", key="chat_back_btn", type="tertiary"):
            go(ss.chat_back if ss.chat_back in ("mf", "fund") else "mf")
            st.rerun()
        b2.markdown('<div class="gw-fhead"><span class="fs-dot big">✦</span><span>FinSaar</span></div>',
                    unsafe_allow_html=True)
    if ss.pending:
        q = ss.pending
        ss.pending = None
        with st.spinner("FinSaar is reading your SIP…"):
            ss.turns.append(run_question(q, s))
    if not ss.turns:
        st.markdown('<div class="fs-card"><div class="fs-label">✦ FinSaar</div>Ask me anything about your SIP, in '
                    'English or Hinglish. I explain; the decision is always yours.</div>', unsafe_allow_html=True)
    for i, r in enumerate(ss.turns):
        answer_card(r, s)
        if i == len(ss.turns) - 1 and i not in ss.feedback_done and r.kind != "limit":
            c1, c2, c3 = st.container(key=f"fb{i}").columns(3)
            c1.button("Yes, clear", key=f"yes{i}", on_click=on_yes, args=(i,), type="primary")
            c2.button("Simpler", key=f"simp{i}", on_click=on_simpler, args=(i,))
            c3.button("Ask another", key=f"more{i}", on_click=on_another, args=(i,))
    if ss.understood or ss.simpler:
        st.markdown(f'<div class="memory">{html.escape(memory_line())}</div>', unsafe_allow_html=True)
    st.pills("Suggested", m["chips"], key="chip", on_change=on_chip, selection_mode="single",
             label_visibility="collapsed")
    with st.form("ask_form", clear_on_submit=True, border=False):
        c1, c2 = st.container(key="askbox").columns([5, 1])
        text = c1.text_input("Ask about your SIP", placeholder="Ask about your SIP…", label_visibility="collapsed",
                             max_chars=300)
        if c2.form_submit_button("➤", width="stretch") and text.strip():
            ask(text.strip())
            st.rerun()


# ---------- controls (outside the phone, for mentors) ----------

def controls_panel():
    ss = st.session_state
    st.markdown('<div class="pc-h">Prototype controls</div>', unsafe_allow_html=True)
    ss.w_profile = ss.profile_label
    st.radio("Demo investor", list(PROFILES), key="w_profile", on_change=on_profile,
             captions=[PROFILE_HELP[p] for p in PROFILES])
    ss.w_scenario = ss.scenario
    st.selectbox("Journey moment · for testing only", list(SCENARIOS), format_func=SCENARIOS.get,
                 key="w_scenario", on_change=on_scenario)
    c1, c2 = st.columns(2)
    c1.button("Next visit", on_click=on_next_visit, width="stretch",
              help="Clears the chat, keeps what FinSaar learned: shows 'Last time: … next?'")
    c2.button("Reset", on_click=on_reset, width="stretch")
    st.markdown(f'<div class="pc-task"><b>🧪 Try this task</b><br>{TASK}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.page_link(HOW_PAGE, label="Guide", icon="📖")
    c2.page_link(EVAL_PAGE, label="Eval", icon="✅")
    st.caption(f"Questions used: {ss.q_count}/{pipeline.LIMIT}")


# ---------- the app page ----------

def app_page():
    init_state()
    ss = st.session_state
    if ss.screen not in ("mf", "fund", "chat"):
        ss.screen = "mf"
    s = calc.compute(scenario=ss.scenario)
    m = moment(s)
    left, mid, _ = st.columns([3, 4.4, 2.2], gap="medium")
    with left.container(key="ctrlpanel"):
        controls_panel()
    with mid:
        phone = st.container(key="phone", height=780)
        with phone:
            status_bar()
            try:
                if ss.screen == "chat":
                    screen_chat(s, m)
                elif ss.screen == "fund":
                    screen_fund(s, m)
                else:
                    screen_mf(s, m)
                if ss.sheet and ss.screen in ("fund", "mf"):
                    bottom_sheet(s, m)
            except Exception:  # never show a traceback inside the phone
                ss.sheet = None
                st.markdown(f'<div class="fs-card"><div class="fs-label">✦ FinSaar</div>Something went wrong on our '
                            f'side, so here are your plain numbers. Tap <b>Reset</b> on the left to start again.'
                            f'{numbers_table(s)}</div>', unsafe_allow_html=True)


# ---------- navigation: Guide → app, plus Eval ----------
import how_to_use  # noqa: E402


def how_page():
    ui_style.brand_header()
    how_to_use.render(APP_PAGE)


def eval_wrapper():
    ui_style.brand_header()
    st.page_link(APP_PAGE, label="← Back to the app", icon="📱")
    import eval_page
    eval_page.page()


HOW_PAGE = st.Page(how_page, title="Guide", url_path="guide", default=True)
APP_PAGE = st.Page(app_page, title="FinSaar in Groww", url_path="app")
EVAL_PAGE = st.Page(eval_wrapper, title="Eval results", url_path="eval")

ui_style.apply()
pg = st.navigation([HOW_PAGE, APP_PAGE, EVAL_PAGE], position="hidden")
pg.run()
