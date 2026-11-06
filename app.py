"""FinSaar: Aapke SIP ka saar. A concept feature shown inside a Groww-style Mutual Funds app (Streamlit)."""
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

# Journey moments shown in the controls → which data scenario they use
MOMENTS = {"just": "Just registered", "start": "First instalment", "midway": "Value is up",
           "dip": "Value below invested", "return": "Return visit"}
MOMENT_SCENARIO = {"just": "start", "start": "start", "midway": "midway", "dip": "dip", "return": "dip"}
TERM_ORDER = ["NAV", "XIRR", "Units", "Average buy NAV"]
TERM_QUESTION = {"NAV": "What does NAV mean for me?", "Units": "What do my units mean for me?",
                 "XIRR": "What does XIRR mean for me?", "Average buy NAV": "What is my average buy NAV?"}
FS = ":green[✦]"   # FinSaar mark inside Streamlit button labels


# ---------- what FinSaar offers for this SIP right now ----------

def moment(s: calc.SipSummary) -> dict:
    xirr_txt = calc.signed_pct(s.xirr_pct, 1) if s.xirr_pct is not None else None
    if s.scenario == "start":
        chips = ["What did my first ₹2,000 buy?", "What is NAV?", "Why is XIRR not shown yet?"]
        tiles = {"Returns": "Why are my returns zero?", "XIRR": "Why is XIRR not shown yet?",
                 "Units": f"What do my {s.total_units:.2f} units mean?", "NAV": "What does NAV mean for me?"}
    elif s.is_up:
        chips = ["Why is my value up?", "What does XIRR mean for me?", "Should I invest more?"]
        tiles = {"Returns": "Why is my value up?", "XIRR": f"What does my XIRR of {xirr_txt} mean for me?",
                 "Units": f"What do my {s.total_units:.2f} units mean?", "NAV": "What does NAV mean for me?"}
    else:
        chips = ["Kya mera paisa doob gaya?", "Why are units up but value down?", "What does XIRR mean for me?",
                 "Should I stop and move to a better fund?"]
        tiles = {"Returns": "Kya mera paisa doob gaya?", "XIRR": f"What does my XIRR of {xirr_txt} mean for me?",
                 "Units": "Why are units up but value down?", "NAV": "What does NAV mean for me?"}
    return {"chips": chips, "tiles": tiles}


def sheet_facts(metric: str, s: calc.SipSummary) -> tuple[str, str, list[str]]:
    """'What it is' (plain definition) and 'your number' (calc). The AI only adds 'for you now'."""
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
        follow = ["Kya mera paisa doob gaya?", "Why are units up but value down?"]
    return what, mine, follow


# ---------- state ----------

def init_state():
    ss = st.session_state
    ss.setdefault("moment", "dip")
    ss.setdefault("lang", "Hinglish")
    ss.setdefault("level", "Beginner")
    ss.setdefault("understood", [])
    ss.setdefault("simpler", False)
    ss.setdefault("turns", [])
    ss.setdefault("feedback_done", set())
    ss.setdefault("card_dismissed", False)
    ss.setdefault("q_count", 0)
    ss.setdefault("pending", None)
    ss.setdefault("sheet_cache", {})
    ss.setdefault("screen", "mf")        # mf | fund | chat
    ss.setdefault("tab", "Dashboard")    # Explore | Dashboard | SIPs | Watchlist
    ss.setdefault("sheet", None)         # Returns | XIRR | Units | NAV
    ss.setdefault("visit", 1)
    ss.setdefault("explained", [])       # terms explained earlier (for "Last time: …")
    ss.setdefault("chat_back", "mf")


def scenario() -> str:
    return MOMENT_SCENARIO[st.session_state.moment]


def current_profile() -> dict:
    ss = st.session_state
    return {"level": "beginner" if ss.level == "Beginner" else "basics",
            "language": "hinglish" if ss.lang == "Hinglish" else "english",
            "understood": list(ss.understood), "simpler": ss.simpler}


def go(screen: str):
    st.session_state.screen = screen
    st.session_state.sheet = None


def ask(question: str):
    """Open the FinSaar chat with this question."""
    ss = st.session_state
    if ss.screen != "chat":
        ss.chat_back = ss.screen
    ss.pending = question
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


# ---------- control callbacks ----------

def _clear_conversation():
    ss = st.session_state
    ss.turns, ss.feedback_done, ss.pending = [], set(), None
    ss.card_dismissed = False
    ss.sheet = None
    ss.screen = "mf"
    ss.tab = "Dashboard"


def on_moment():
    ss = st.session_state
    ss.moment = ss.w_moment or ss.moment
    _clear_conversation()
    if ss.moment == "return":
        ss.visit = max(ss.visit, 2)
        if not ss.explained:
            ss.explained = ["NAV"]          # the previous visit explained NAV
    else:
        ss.visit = 1


def on_lang():
    st.session_state.lang = st.session_state.w_lang or st.session_state.lang


def on_level():
    st.session_state.level = st.session_state.w_level or st.session_state.level


def on_open_chat():
    ss = st.session_state
    ss.chat_back = ss.screen if ss.screen != "chat" else "mf"
    go("chat")


def on_reset():
    for k in list(st.session_state.keys()):
        del st.session_state[k]


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


def on_simpler(i: int):
    st.session_state.simpler = True
    st.session_state.feedback_done.add(i)
    ask(st.session_state.turns[i].question)


def on_another(i: int):
    st.session_state.feedback_done.add(i)


# ---------- rendering helpers ----------

def numbers_table(s: calc.SipSummary) -> str:
    rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>"
                   for k, v in calc.numbers_summary(s))
    return f'<table class="fs-nums">{rows}</table>'


SEBI_FALLBACK = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13"


def sebi_link() -> str:
    fn = getattr(config, "sebi_link", None)   # survives a hot reload with an older config module
    return fn() if callable(fn) else SEBI_FALLBACK


def status_html(r: pipeline.Result) -> str:
    if r.kind == "fallback-error":
        return '<div class="fs-warn">⚠ AI busy · plain numbers from your SIP data</div>'
    if r.kind == "fallback-unsure":
        return '<div class="fs-warn">⚠ Not sure, so FinSaar won\'t guess · plain numbers shown</div>'
    if r.kind == "limit":
        return '<div class="fs-warn">Question limit reached for this session</div>'
    if r.gate_passed:
        return ('<div class="fs-check">✓ Checked against your SIP data</div>'
                '<div class="fs-src">Source: Your transactions · AMFI investor education</div>')
    return '<div class="fs-warn">⚠ Safe fallback shown</div>'


def links_html(r: pipeline.Result) -> str:
    amfi = f'<a href="{html.escape(config.amfi_link())}" target="_blank">AMFI investor education</a>'
    if r.path == "decline":
        sebi = f'<a href="{html.escape(sebi_link())}" target="_blank">Find a SEBI-registered adviser</a>'
        return f'<div class="fs-links">{sebi} · {amfi}</div>'
    if r.show_numbers:
        return f'<div class="fs-links">Official source: {amfi}</div>'
    return ""


def answer_card(r: pipeline.Result, s: calc.SipSummary, show_question: bool = True):
    if show_question:
        st.markdown(f'<div class="fs-q">{html.escape(r.question)}</div>', unsafe_allow_html=True)
    body = html.escape(r.answer).replace("\n", "<br>")
    pre = '<div class="fs-outside">ⓘ Outside what I can help with</div>' if r.path == "decline" else ""
    extra = numbers_table(s) if r.show_numbers else ""
    st.markdown(f'<div class="fs-ans"><div class="fs-label">✦ FinSaar</div>{pre}<div class="fs-body">{body}</div>'
                f'{extra}{links_html(r)}<div class="fs-rule"></div>{status_html(r)}</div>', unsafe_allow_html=True)
    with st.expander("How this answer was checked"):
        if r.gate:
            for c in r.gate.checks:
                st.markdown(f"{'✅' if c.passed else '❌'} **{c.name}**: {html.escape(c.detail)}")
        for n, a in enumerate(r.attempts, 1):
            if not a["passed"]:
                st.markdown(f"↻ Try {n} was blocked: {html.escape('; '.join(a['reasons']))}")
        st.markdown(f"**Route:** {r.intent} → *{r.path}* ({r.kind})")
        st.markdown(f"**Numbers used:** {', '.join(r.numbers_used) or 'only app-computed numbers'}")
        st.markdown(f"**Sources:** {', '.join(r.sources)}")
        for c in r.chunks:
            st.caption(f"{c.label}: {c.text[:180]}{'…' if len(c.text) > 180 else ''}")


def memory_line() -> str:
    ss = st.session_state
    bits = [f"{t} ✓" for t in ss.understood]
    if ss.simpler:
        bits.append("prefers simpler")
    bits.append(ss.lang)
    return "FinSaar remembers: " + " · ".join(bits)


def ret_text(s: calc.SipSummary) -> tuple[str, str]:
    if s.is_down or s.is_up:
        return f"{'−' if s.is_down else '+'}{calc.inr(s.gain)} ({calc.signed_pct(s.gain_pct, 2)})", \
               ("neg" if s.is_down else "pos")
    return "₹0 (0.00%)", ""


def xirr_text(s: calc.SipSummary) -> str:
    return calc.signed_pct(s.xirr_pct, 1) if s.xirr_pct is not None else "--"


def one_day_html(s: calc.SipSummary) -> str:
    od = s.one_day
    if not od:
        return "--"
    cls = "neg" if od[0] < 0 else "pos"
    return f'<span class="{cls}">{"−" if od[0] < 0 else "+"}{calc.inr(od[0], 2)} ({calc.signed_pct(od[1], 2)})</span>'


ICON = {
    "search": '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/></svg>',
    "spin": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="7" stroke-dasharray="3 3"/></svg>',
    "stocks": '<svg viewBox="0 0 24 24"><rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M7 15l3.5-4 3 2.5L17 9"/></svg>',
    "fo": '<svg viewBox="0 0 24 24"><rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M3.5 15.5l6-5.5 4 3.5 7-6"/></svg>',
    "mf": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 4v8l6.2 4.6"/></svg>',
    "loans": '<svg viewBox="0 0 24 24"><rect x="3.5" y="6.5" width="17" height="11" rx="2"/><circle cx="12" cy="12" r="2.3"/></svg>',
}


def status_bar():
    st.markdown('<div class="ph-status"><b>11:36</b><span class="ph-sig">▂▄▆█ <span class="ph-batt">83</span></span></div>',
                unsafe_allow_html=True)


def bottom_nav():
    items = [("stocks", "Stocks"), ("fo", "F&amp;O"), ("mf", "Mutual Funds"), ("loans", "Loans")]
    cells = "".join(f'<div class="{"on" if label == "Mutual Funds" else ""}" {ui_style.DEAD}>{ICON[k]}{label}</div>'
                    for k, label in items)
    st.markdown(f'<div class="gw-nav">{cells}</div>', unsafe_allow_html=True)


# ---------- phone: Mutual Funds (tabs) ----------

def mf_header():
    ss = st.session_state
    st.markdown(f'<div class="gw-head"><span class="gw-mark" {ui_style.DEAD}></span><span class="gw-title">Mutual Funds</span>'
                f'<span class="gw-icons" {ui_style.DEAD}>{ICON["search"]}{ICON["spin"]}<span class="gw-av">A</span></span></div>',
                unsafe_allow_html=True)
    cols = st.container(key="mftabs").columns([1, 1.3, 0.8, 1.15])
    for col, t in zip(cols, ["Explore", "Dashboard", "SIPs", "Watchlist"]):
        with col.container(key=f"tab{'on' if ss.tab == t else 'off'}_{t}"):
            if st.button(t, key=f"tab_{t}", type="tertiary", width="stretch"):
                ss.tab = t
                st.rerun()


def holding_row(label: str, value_html: str, metric: str | None, key: str):
    c1, c2 = st.columns([1.2, 1], vertical_alignment="center")
    c1.markdown(f'<div class="gw-lbl">{label}{" <span class=fsm>✦</span>" if metric else ""}</div>',
                unsafe_allow_html=True)
    if metric:
        with c2.container(key=f"tapv_{key}"):
            if st.button(value_html, key=key, type="tertiary", help="FinSaar explains this number"):
                st.session_state.sheet = metric
                st.rerun()
    else:
        c2.markdown(f'<div class="gw-val">{value_html}</div>', unsafe_allow_html=True)


def finsaar_card(s: calc.SipSummary, m: dict):
    """Entry points 1 and 3: one dismissible card under the holdings card."""
    ss = st.session_state
    if ss.card_dismissed:
        return
    last = ss.explained[-1] if ss.explained else None
    nxt = next((t for t in TERM_ORDER if t not in ss.understood and t not in ss.explained), None)
    if ss.visit > 1 and last and nxt:
        title, cta, q = f"Last time: {last}. {nxt} next?", "Continue learning", TERM_QUESTION[nxt]
    elif s.is_down:
        title, cta, q = f"Your SIP is {calc.inr(s.gain)} below what you invested.", "Understand it", m["tiles"]["Returns"]
    else:
        return
    with st.container(key="fscard"):
        c0, c1, c2 = st.columns([0.9, 5, 0.7], vertical_alignment="top")
        c0.markdown('<div class="fs-icon">✦</div>', unsafe_allow_html=True)
        with c1:
            st.markdown(f'<div class="fs-tag">✦ FinSaar</div><div class="fs-title">{title}</div>', unsafe_allow_html=True)
            if st.button(cta, key="fs_go", type="tertiary"):
                ss.card_dismissed = True
                ask(q)
                st.rerun()
        if c2.button("✕", key="fs_x", type="tertiary", help="Dismiss"):
            ss.card_dismissed = True
            st.rerun()


def fund_row(s: calc.SipSummary):
    ret, tone = ret_text(s)
    n = s.n_instalments
    with st.container(key="fundrow"):
        c0, c1, c2 = st.columns([0.8, 3.2, 1.6], vertical_alignment="center")
        c0.markdown('<span class="gw-tile">S</span>', unsafe_allow_html=True)
        if c1.button(f"**{s.fund}**  \n:gray[SIP · {n} instalment{'s' if n > 1 else ''}]", key="open_fund",
                     width="stretch"):
            go("fund")
            st.rerun()
        c2.markdown(f'<div class="gw-rowval"><span class="{tone}">{calc.inr(s.current_value)}</span> <span class="chev">›</span>'
                    f'<br><small>({calc.inr(s.invested)})</small></div>', unsafe_allow_html=True)


def tab_dashboard(s: calc.SipSummary, m: dict):
    if st.session_state.moment == "just":
        st.markdown(f'<div class="gw-card gw-empty"><div class="gw-cap">HOLDINGS (0)</div><div class="gw-big">₹0</div>'
                    f'<div class="gw-muted">Your first SIP instalment of {calc.inr(s.monthly_amount)} is due on '
                    f'{calc.fmt_date(s.instalments[0].date)}.</div></div>'
                    f'<div class="gw-card gw-promo" {ui_style.DEAD}><b>Invest every month and grow your wealth with SIP</b>'
                    f'<span class="gw-cta">Start a SIP</span></div>', unsafe_allow_html=True)
        return
    ret, tone = ret_text(s)
    with st.container(key="holdcard"):
        st.markdown(f'<div class="gw-cap">HOLDINGS (1)</div><div class="gw-bigrow"><span class="gw-big">'
                    f'{calc.inr(s.current_value)}</span><span class="gw-eye" {ui_style.DEAD}>◉</span></div>'
                    f'<div class="gw-dash"></div>', unsafe_allow_html=True)
        holding_row("1D returns", one_day_html(s), None, "h1d")
        holding_row("Total returns", f":{'red' if tone == 'neg' else 'green' if tone else 'gray'}[{ret}]", "Returns", "h_ret")
        holding_row("Invested", calc.inr(s.invested), None, "hinv")
        holding_row("XIRR (Active)", xirr_text(s), "XIRR", "h_xirr")
    finsaar_card(s, m)
    st.markdown(f'<div class="gw-listhead"><span class="gw-filter" {ui_style.DEAD}>≡</span>'
                f'<span class="gw-dotted" {ui_style.DEAD}>‹› Current (Invested)</span></div>', unsafe_allow_html=True)
    fund_row(s)
    st.markdown(f'<div class="gw-pill-btn" {ui_style.DEAD}>⤓ Import external funds</div>', unsafe_allow_html=True)


def tab_sips(s: calc.SipSummary):
    nxt = s.instalments[0].date if st.session_state.moment == "just" else s.next_instalment
    st.markdown(f'<div class="gw-card"><div class="gw-cap">MONTHLY SIP AMOUNT</div>'
                f'<div class="gw-big">{calc.inr(s.monthly_amount)}</div></div>'
                f'<div class="gw-sechead"><b>Active SIPs (1)</b><span class="gw-dotted" {ui_style.DEAD}>Sort by: Due date</span></div>',
                unsafe_allow_html=True)
    with st.container(key="siprow"):
        c0, c1, c2 = st.columns([0.8, 3.2, 1], vertical_alignment="center")
        c0.markdown('<span class="gw-tile">S</span>', unsafe_allow_html=True)
        if c1.button(f"{s.fund}  \n:gray[{calc.inr(s.monthly_amount)}]", key="open_fund_sip", width="stretch",
                     disabled=st.session_state.moment == "just"):
            go("fund")
            st.rerun()
        if nxt:
            c2.markdown(f'<div class="gw-date"><b>{nxt.day:02d}</b><br>{nxt.strftime("%b")}</div>', unsafe_allow_html=True)


FICTIONAL = [("SL", "Sample Large Cap Fund (fictional)", "Equity · Large Cap", "#5367ff"),
             ("SI", "Sample Index Fund (fictional)", "Equity · Index", "#00b386"),
             ("SD", "Sample Debt Fund (fictional)", "Debt · Short duration", "#f2994a"),
             ("SM", "Sample Mid Cap Fund (fictional)", "Equity · Mid Cap", "#1d6f42")]


def tab_explore():
    cards = "".join(f'<div class="gw-fcard" {ui_style.DEAD}><span class="gw-tile" style="background:{c}">{i}</span>'
                    f'<div>{n}</div><div class="gw-muted">{cat}</div></div>' for i, n, cat, c in FICTIONAL)
    st.markdown(f'<div class="gw-sechead"><b>Popular Funds</b><span class="gw-muted" {ui_style.DEAD}>View all ›</span></div>'
                f'<div class="gw-grid">{cards}</div>', unsafe_allow_html=True)


def tab_watchlist():
    rows = "".join(f'<div class="gw-wrow" {ui_style.DEAD}><span class="gw-tile" style="background:{c}">{i}</span>'
                   f'<div><div>{n}</div><div class="gw-muted">{cat}</div></div></div>' for i, n, cat, c in FICTIONAL[:3])
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


# ---------- phone: Fund details ----------

def detail_row(label: str, value: str, metric: str | None, key: str, tone: str = ""):
    with st.container(key=f"drow_{key}"):
        c1, c2 = st.columns([1.3, 1.3], vertical_alignment="center")
        c1.markdown(f'<div class="fd-lbl">{label}</div>', unsafe_allow_html=True)
        if metric:
            if c2.button(f"{FS} {value}  ›", key=key, type="tertiary", help="FinSaar explains this number"):
                st.session_state.sheet = metric
                st.rerun()
        else:
            c2.markdown(f'<div class="fd-val">{value}</div>', unsafe_allow_html=True)


def screen_fund(s: calc.SipSummary, m: dict):
    ss = st.session_state
    with st.container(key="fdhead"):
        b1, b2, b3 = st.columns([1, 6, 1], vertical_alignment="center")
        if b1.button("‹", key="fund_back", type="tertiary", help="Back"):
            go("mf")
            st.rerun()
        b2.markdown('<div class="fd-title">Fund details</div>', unsafe_allow_html=True)
        b3.markdown(f'<div class="fd-more" {ui_style.DEAD}>⋮</div>', unsafe_allow_html=True)
    with st.container(key="askbanner"):
        if st.button(f"{FS} **Ask FinSaar**  \n:gray[About your SIP]", key="ask_banner", width="stretch"):
            ss.chat_back = "fund"
            go("chat")
            st.rerun()
    ret, tone = ret_text(s)
    st.markdown(f'<div class="fd-sec">Your investment</div><div class="fd-fund"><span class="gw-tile">S</span>'
                f'<div><b>{html.escape(s.fund)}</b><div class="gw-muted">Current {calc.inr(s.current_value)} · '
                f'Invested {calc.inr(s.invested)}</div></div></div>', unsafe_allow_html=True)
    detail_row("Total returns", ret.split(" (")[0], "Returns", "d_ret")
    detail_row("XIRR", xirr_text(s), "XIRR", "d_xirr")
    detail_row("Units", f"{s.total_units:.2f}", "Units", "d_units")
    detail_row("Average NAV", calc.inr(s.avg_nav, 2), None, "d_avg")
    detail_row("Current NAV", calc.inr(s.current_nav, 2), "NAV", "d_nav")
    nxt = s.next_instalment
    with st.container(key="yoursip"):
        c1, c2 = st.columns([3, 1.2], vertical_alignment="center")
        c1.markdown(f'<div class="gw-cap">YOUR SIP</div><div class="fd-sip">{calc.inr(s.monthly_amount)} monthly</div>'
                    f'<div class="gw-muted">Next instalment · {nxt.day} {nxt.strftime("%b")}</div>' if nxt else "",
                    unsafe_allow_html=True)
        if c2.button("View SIP", key="view_sip", type="tertiary"):
            ss.tab = "SIPs"
            go("mf")
            st.rerun()
    rows = "".join(f'<div class="gw-tx"><div>{i.date.day} {i.date.strftime("%b")} · {calc.inr(i.amount)} · '
                   f'{i.units:.2f} units<div class="gw-muted">NAV {i.nav:.2f}</div></div>'
                   f'<span class="gw-done">Completed</span></div>' for i in reversed(s.instalments))
    st.markdown(f'<div class="fd-sec">Transactions</div>{rows}', unsafe_allow_html=True)


# ---------- phone: bottom sheet ----------

def bottom_sheet(s: calc.SipSummary, m: dict):
    """Entry point 2: tap a ✦ number → 'What does this mean for me?' sheet, inside the phone."""
    ss = st.session_state
    metric = ss.sheet
    question = m["tiles"][metric]
    what, mine, follow = sheet_facts(metric, s)
    ret, tone = ret_text(s)
    val = {"XIRR": xirr_text(s), "NAV": calc.inr(s.current_nav, 2), "Units": f"{s.total_units:.2f}",
           "Returns": ret}[metric]
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
        ck = f"{s.scenario}|{question}|{ss.lang}|{ss.level}|{ss.simpler}"
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
        if b1.button("Yes, clear", key=f"sy{kh}"):
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


# ---------- phone: FinSaar chat ----------

def screen_chat(s: calc.SipSummary, m: dict):
    ss = st.session_state
    with st.container(key="fdhead"):
        b1, b2, b3 = st.columns([1, 6, 1], vertical_alignment="center")
        if b1.button("‹", key="chat_back_btn", type="tertiary", help="Back"):
            go(ss.chat_back if ss.chat_back in ("mf", "fund") else "mf")
            st.rerun()
        b2.markdown('<div class="fd-title"><span class="fsm">✦</span> FinSaar</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ch-fund"><b>{html.escape(s.fund)}</b><div class="gw-muted">{calc.inr(s.current_value)} current · '
                f'{calc.inr(s.invested)} invested</div></div>', unsafe_allow_html=True)
    greet = ("Namaste. Main aapke SIP ke numbers ko simple shabdon mein samjha sakta hoon. Kya samajhna chahenge?"
             if ss.lang == "Hinglish" else
             "Hi. I can explain your SIP numbers in simple words. What would you like to understand?")
    st.markdown(f'<div class="fs-ans"><div class="fs-label">✦ FinSaar</div><div class="fs-body">{greet}</div></div>',
                unsafe_allow_html=True)
    if ss.pending:
        q = ss.pending
        ss.pending = None
        with st.spinner("FinSaar is reading your SIP…"):
            ss.turns.append(run_question(q, s))
    for i, r in enumerate(ss.turns):
        answer_card(r, s)
        if i == len(ss.turns) - 1 and i not in ss.feedback_done and r.kind != "limit":
            c1, c2, c3 = st.container(key=f"fb{i}").columns(3)
            c1.button("Yes, clear", key=f"yes{i}", on_click=on_yes, args=(i,))
            c2.button("Simpler", key=f"simp{i}", on_click=on_simpler, args=(i,))
            c3.button("Ask another", key=f"more{i}", on_click=on_another, args=(i,))
    if ss.understood or ss.simpler:
        st.markdown(f'<div class="memory">{html.escape(memory_line())} · <i>cross-session learning planned</i></div>',
                    unsafe_allow_html=True)
    st.pills("Suggested", m["chips"], key="chip", on_change=on_chip, selection_mode="single",
             label_visibility="collapsed")
    with st.form("ask_form", clear_on_submit=True, border=False):
        c1, c2 = st.container(key="askbox").columns([5, 1], vertical_alignment="center")
        text = c1.text_input("Ask about your SIP", placeholder="Ask anything about your SIP…",
                             label_visibility="collapsed", max_chars=300)
        if c2.form_submit_button("↑") and text.strip():
            ask(text.strip())
            st.rerun()


# ---------- side panels (outside the phone) ----------

def left_panel():
    ss = st.session_state
    st.markdown('<div class="lp-cap">CONCEPT MVP</div><div class="lp-title">FinSaar</div>'
                '<div class="lp-sub">Your SIP speaks in numbers. FinSaar helps you make sense of them in your terms.</div>'
                '<div class="lp-cap" style="margin-top:22px">JOURNEY MOMENT</div>', unsafe_allow_html=True)
    ss.w_moment = ss.moment
    with st.container(key="momentlist"):
        st.radio("Journey moment", list(MOMENTS), format_func=MOMENTS.get, key="w_moment", on_change=on_moment,
                 label_visibility="collapsed")
    st.markdown('<div class="lp-cap">EXPLANATION LANGUAGE</div>', unsafe_allow_html=True)
    ss.w_lang = ss.lang
    st.segmented_control("Language", ["English", "Hinglish"], key="w_lang", on_change=on_lang,
                         label_visibility="collapsed", width="stretch")
    st.markdown('<div class="lp-cap">LEVEL</div>', unsafe_allow_html=True)
    ss.w_level = ss.level
    st.segmented_control("Level", ["Beginner", "Knows basics"], key="w_level", on_change=on_level,
                         label_visibility="collapsed", width="stretch")
    with st.container(key="openchat"):
        st.button("✦  Open FinSaar chat (testing)", on_click=on_open_chat, width="stretch", type="primary")
    c1, c2, c3 = st.columns(3)
    c1.page_link(HOW_PAGE, label="Guide")
    c2.page_link(EVAL_PAGE, label="Eval")
    c3.button("Reset", on_click=on_reset, type="tertiary")
    st.markdown(f'<div class="lp-task"><b>Try this task</b><br>Your SIP is down. Find out whether you\'ve lost money '
                f'and what your XIRR means. Then ask whether you should stop.</div>', unsafe_allow_html=True)


def right_panel():
    ss = st.session_state
    active = 3 if ss.screen == "chat" else 2 if (ss.sheet or ss.screen == "fund") else 1
    steps = [("01", "Contextual entry", "Trigger only at the dip"),
             ("02", "Own SIP numbers", "Tap ✦ metrics for sheets"),
             ("03", "Grounded Q&amp;A", "English or Hinglish")]
    items = "".join(f'<div class="rp-step {"on" if i + 1 == active else ""}"><span class="rp-n">{n}</span>'
                    f'<div><b>{t}</b><div>{d}</div></div></div>' for i, (n, t, d) in enumerate(steps))
    st.markdown(f'<div class="lp-cap">HOW IT WORKS</div><div class="rp-title">One feature,<br>three surfaces</div>'
                f'{items}<div class="rp-guard"><b>Built-in guardrails</b><div>✓ No advice</div><div>✓ No predictions</div>'
                f'<div>✓ Numbers from code</div><div>✓ Sources shown</div><div>✓ Every answer checked before it shows</div></div>'
                f'<div class="rp-note">Questions used: {ss.q_count}/{pipeline.LIMIT}</div>', unsafe_allow_html=True)


# ---------- the app page ----------

def app_page():
    init_state()
    ss = st.session_state
    if ss.screen not in ("mf", "fund", "chat"):
        ss.screen = "mf"
    s = calc.compute(scenario=scenario())
    m = moment(s)
    if ss.moment == "just" and ss.screen != "mf":
        ss.screen = "mf"
    left, mid, right = st.columns([3, 4.2, 3], gap="large")
    with left.container(key="ctrlpanel"):
        left_panel()
    with mid:
        phone = st.container(key="phone", height=800)
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
                st.markdown(f'<div class="fs-ans"><div class="fs-label">✦ FinSaar</div>Something went wrong on our '
                            f'side, so here are your plain numbers. Tap <b>Reset</b> to start again.'
                            f'{numbers_table(s)}</div>', unsafe_allow_html=True)
        st.markdown('<div class="ph-foot"><span class="dot"></span> Interactive prototype · Tap ✦ numbers</div>',
                    unsafe_allow_html=True)
    with right.container(key="notespanel"):
        right_panel()


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
