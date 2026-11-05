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
        tiles = {"XIRR": "Why is XIRR not shown yet?", "Units": f"What do my {s.total_units:.2f} units mean?",
                 "NAV": "What does NAV mean for me?"}
        nudge_q = "What did my first ₹2,000 buy?"
    elif s.is_up:
        chips = ["Why is my value up?", "What does XIRR mean for me?", "Should I invest more?"]
        tiles = {"XIRR": f"What does my XIRR of {xirr_txt} mean for me?",
                 "Units": f"What do my {s.total_units:.2f} units mean?", "NAV": "What does NAV mean for me?"}
        nudge_q = "Why is my value up?"
    else:
        chips = ["Iska matlab paisa doob gaya?", "Why are units up but value down?", "What does XIRR mean for me?",
                 "Should I stop and move to a better fund?"]
        tiles = {"XIRR": f"What does my XIRR of {xirr_txt} mean for me?",
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
    ss.setdefault("screen", "home")      # home | fund | chat
    ss.setdefault("sheet", None)         # XIRR | NAV | Units | ✦ question
    ss.setdefault("visit", 1)
    ss.setdefault("explained", [])       # terms explained in earlier answers (for "Last time: …")
    ss.setdefault("chat_back", "fund")


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
    ss.screen = "home"


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
        return f"{'−' if s.is_down else '+'}{calc.inr(s.gain)} ({calc.signed_pct(s.gain_pct, 2)})", \
               ("neg" if s.is_down else "pos")
    return "₹0 (0.00%)", ""


def status_bar():
    st.markdown('<div class="ph-status"><b>9:41</b><span>▂▄▆ 📶 🔋</span></div>', unsafe_allow_html=True)


def bottom_nav(active: str = "Home"):
    items = [("🏠", "Home"), ("📈", "Stocks"), ("🪙", "Mutual Funds"), ("👤", "Profile")]
    cells = "".join(f'<div class="{"on" if label == active else ""}" {ui_style.DEAD}><span>{icon}</span>{label}</div>'
                    for icon, label in items)
    st.markdown(f'<div class="ph-nav">{cells}</div>', unsafe_allow_html=True)


# ---------- phone screens ----------

def screen_home(s: calc.SipSummary, m: dict):
    ss = st.session_state
    st.markdown(f'<div class="ph-head"><span class="wordmark" {ui_style.DEAD}><span class="h-mark"></span>Groww</span>'
                f'<span class="ph-icons" {ui_style.DEAD}>🔍 🔔</span></div>'
                f'<div class="ph-tabs"><span {ui_style.DEAD}>Stocks</span><span class="on" {ui_style.DEAD}>Mutual Funds</span>'
                f'<span {ui_style.DEAD}>F&amp;O</span></div>'
                f'<div class="h-sub"><span {ui_style.DEAD}>Explore</span><span class="on" {ui_style.DEAD}>Dashboard</span>'
                f'<span {ui_style.DEAD}>SIPs</span><span {ui_style.DEAD}>Watchlist</span></div>', unsafe_allow_html=True)
    ret, tone = ret_text(s)
    xirr = calc.signed_pct(s.xirr_pct, 1) if s.xirr_pct is not None else "—"
    st.markdown(f'<div class="d-sum"><div class="lbl">Current value</div><div class="big">{calc.inr(s.current_value)}</div>'
                f'<div class="grid"><div><span class="lbl">Invested</span><b>{calc.inr(s.invested)}</b></div>'
                f'<div><span class="lbl">Returns</span><b class="{tone}">{ret}</b></div>'
                f'<div><span class="lbl">XIRR</span><b class="{tone}">{xirr}</b></div></div></div>',
                unsafe_allow_html=True)

    # Entry point 3: when you come back (in-app only)
    last = ss.explained[-1] if ss.explained else None
    nxt = next((t for t in TERM_ORDER if t not in ss.understood and t not in ss.explained), None)
    if ss.visit > 1 and last and nxt and not ss.card_dismissed:
        st.markdown(f'<div class="fs-card"><div class="fs-label">✦ FinSaar · welcome back</div>'
                    f'Last time: <b>{last}</b>. <b>{nxt}</b> next?</div>', unsafe_allow_html=True)
        c1, c2, _ = st.container(key="nudge").columns([1.1, 1, 0.6])
        if c1.button("Continue", type="primary", key="back_go"):
            ss.card_dismissed = True
            ask(TERM_QUESTION[nxt])
            st.rerun()
        if c2.button("Not now", key="back_later"):
            ss.card_dismissed = True
            st.rerun()
    # Entry point 1: value below invested (code decides when this appears)
    elif s.is_down and not ss.card_dismissed:
        st.markdown(f'<div class="fs-card"><div class="fs-label">✦ FinSaar</div>Your SIP is <b>{calc.inr(s.gain)} '
                    f'below</b> what you invested. Want to understand it?</div>', unsafe_allow_html=True)
        c1, c2, _ = st.container(key="nudge").columns([1.1, 1, 0.6])
        if c1.button("Explain this", type="primary", key="home_go"):
            ss.card_dismissed = True
            ask(m["nudge_q"])
            st.rerun()
        if c2.button("Maybe later", key="home_later"):
            ss.card_dismissed = True
            st.rerun()

    st.markdown('<div class="d-sec">Your SIPs (1)</div>', unsafe_allow_html=True)
    label = (f"**{s.fund}**  \nSIP {calc.inr(s.monthly_amount)}/month · {s.n_instalments} instalment"
             f"{'s' if s.n_instalments > 1 else ''}  \nCurrent {calc.inr(s.current_value)} · {ret}")
    with st.container(key="holdrow"):
        if st.button(label, key="open_fund", width="stretch"):
            go("fund")
            st.rerun()
    st.markdown(f'<div class="d-sec">Popular funds</div><div class="d-dead" {ui_style.DEAD}><b>Sample Index Fund '
                f'(fictional)</b>Equity · Index</div>', unsafe_allow_html=True)
    bottom_nav("Mutual Funds")


def screen_fund(s: calc.SipSummary, m: dict):
    ss = st.session_state
    with st.container(key="backbtn"):
        b1, b2 = st.columns([1, 6], vertical_alignment="center")
        if b1.button("←", key="fund_back", help="Back"):
            go("home")
            st.rerun()
        b2.markdown(f'<div class="ph-title">{html.escape(s.fund)}</div>'
                    f'<div class="g-tags"><span>Equity</span><span>Flexi Cap</span><span>Direct · Growth</span></div>',
                    unsafe_allow_html=True)
    ret, tone = ret_text(s)
    st.markdown(f'<div class="g-hold"><div><div class="lbl">Current value</div><div class="big">{calc.inr(s.current_value)}</div>'
                f'<div class="lbl" style="margin-top:4px">Returns <b class="{tone}">{ret}</b></div></div>'
                f'<div class="g-hold-r"><div class="lbl">Invested</div><div class="mid">{calc.inr(s.invested)}</div></div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="g-hint">✦ Tap a number: what does this mean for me?</div>', unsafe_allow_html=True)
    tone_c = {"neg": ":red", "pos": ":green"}.get(tone, "")
    xv = calc.signed_pct(s.xirr_pct, 1) if s.xirr_pct is not None else "—"
    tiles = [("XIRR", f"{tone_c}[**{xv}**]" if tone_c and s.xirr_pct is not None else f"**{xv}**"),
             ("Units", f"**{s.total_units:.2f}**"), ("NAV", f"**{calc.inr(s.current_nav, 2)}**")]
    cols = st.container(key="tilebtn").columns(3)
    for col, (name, v) in zip(cols, tiles):
        if col.button(f"{name} :green[✦]  \n{v}", key=f"tile_{name}", width="stretch"):
            ss.sheet = name
            st.rerun()

    # "Your SIP this month": built only from the investor's own data (no market comparison)
    last = s.instalments[-1]
    most = max(s.instalments, key=lambda i: i.units)
    extra = " (your most units so far)" if last is most and s.n_instalments > 1 else ""
    st.markdown(f'<div class="fs-card"><div class="fs-label">✦ FinSaar · your SIP this month</div>'
                f'Your {calc.fmt_date(last.date)} instalment of {calc.inr(last.amount)} bought <b>{last.units:.2f} units</b> '
                f'at NAV {last.nav:.2f}{extra}. Today\'s NAV is {calc.inr(s.current_nav, 2)}.'
                f'<div class="fs-src">From your SIP data · explains, doesn\'t advise</div></div>', unsafe_allow_html=True)
    c1, _ = st.container(key="nudge").columns([1.4, 1])
    if c1.button("Ask FinSaar about this", type="primary", key="fund_ask"):
        ask(m["nudge_q"])
        st.rerun()

    st.markdown(f'<div class="ph-actions"><span {ui_style.DEAD}>Change amount</span><span {ui_style.DEAD}>Skip</span>'
                f'<span {ui_style.DEAD}>Pause</span><span {ui_style.DEAD}>Cancel SIP</span></div>', unsafe_allow_html=True)

    nxt = calc.fmt_date(s.next_instalment) if s.next_instalment else "—"
    st.markdown(f'<div class="g-card"><div class="g-card-h">SIP details <span class="g-pill">Active</span></div>'
                f'<div class="g-row"><span>Monthly amount</span><b>{calc.inr(s.monthly_amount)}</b></div>'
                f'<div class="g-row"><span>Next instalment</span><b>{nxt}</b></div>'
                f'<div class="g-row"><span>Average buy NAV</span><b>{calc.inr(s.avg_nav, 2)}</b></div></div>'
                f'<div class="d-sec">Transactions</div>', unsafe_allow_html=True)
    tx = st.container(key="txlist")
    for idx, inst in enumerate(reversed(s.instalments)):
        real = len(s.instalments) - 1 - idx
        prev = s.instalments[real - 1] if real > 0 else None
        if prev is None:
            note, q = "First buy", f"What did my first {calc.inr(inst.amount)} buy?"
        elif inst.units > prev.units:
            note, q = "More units?", f"Why did my {calc.fmt_date(inst.date)} instalment buy more units?"
        else:
            note, q = "Fewer units?", f"Why did my {calc.fmt_date(inst.date)} instalment buy fewer units?"
        c1, c2 = tx.columns([3, 1.3], vertical_alignment="center")
        c1.markdown(f'<div class="g-tx"><div><b>{calc.fmt_date(inst.date)}</b><div class="sub">NAV {inst.nav:.2f}</div></div>'
                    f'<div class="amt">{calc.inr(inst.amount)}<div class="sub">{inst.units:.2f} units</div></div></div>',
                    unsafe_allow_html=True)
        if c2.button(f":green[✦] {note}", key=f"tx_{real}", width="stretch"):
            ss.sheet = "Q:" + q
            st.rerun()
    bottom_nav("Mutual Funds")


def bottom_sheet(s: calc.SipSummary, m: dict):
    """Entry point 2: tap a number → 'What does this mean for me?' sheet, inside the phone."""
    ss = st.session_state
    key = ss.sheet
    sheet = st.container(key="sheet")
    with sheet:
        c1, c2 = st.columns([6, 1], vertical_alignment="center")
        c2.button("✕", key="sheet_close", on_click=lambda: st.session_state.update(sheet=None))
        if key.startswith("Q:"):
            question, metric = key[2:], None
            c1.markdown(f'<div class="sh-title">✦ FinSaar explains</div>', unsafe_allow_html=True)
        else:
            metric = key
            question = m["tiles"][metric]
            what, mine, follow = sheet_facts(metric, s)
            val = {"XIRR": calc.signed_pct(s.xirr_pct, 1) if s.xirr_pct is not None else "—",
                   "NAV": calc.inr(s.current_nav, 2), "Units": f"{s.total_units:.2f}"}[metric]
            c1.markdown(f'<div class="sh-title">{metric} <span class="sh-val">{val}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sh-sec">WHAT IT IS</div><div class="sh-txt">{what}</div>'
                        f'<div class="sh-sec">YOUR NUMBER</div><div class="sh-txt">{mine}</div>', unsafe_allow_html=True)
        ck = f"{s.scenario}|{question}|{ss.profile_label}|{ss.simpler}"
        kh = hashlib.md5(ck.encode()).hexdigest()[:10]
        if ck not in ss.sheet_cache:
            with st.spinner("FinSaar is reading your SIP…"):
                r = run_question(question, s)
            ss.sheet_cache[ck] = r
            ss.turns.append(r)
            ss.feedback_done.add(len(ss.turns) - 1)
        r = ss.sheet_cache[ck]
        if metric:
            st.markdown('<div class="sh-sec">WHAT IT MEANS FOR YOU NOW</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="sh-txt"><b>{html.escape(question)}</b></div>', unsafe_allow_html=True)
        answer_card(r, s, show_question=False)
        b1, b2, b3 = st.container(key=f"fbsheet{kh}").columns(3)
        if b1.button("Yes, clear", key=f"sy{kh}", type="primary"):
            for t in r.terms_explained:
                name = canonical_term(t)
                if name and name not in ss.understood:
                    ss.understood.append(name)
            ss.sheet = None
            st.rerun()
        if b2.button("Explain simpler", key=f"ss{kh}", disabled=ss.simpler):
            ss.simpler = True
            st.rerun()
        if b3.button("Ask more", key=f"sm{kh}"):
            ss.chat_back = ss.screen
            go("chat")
            st.rerun()
        if metric:
            follow = sheet_facts(metric, s)[2]
            st.markdown('<div class="sh-sec">ASK A FOLLOW-UP</div>', unsafe_allow_html=True)
            fcols = st.container(key="sheetchips")
            for n, fq in enumerate(follow):
                if fcols.button(fq, key=f"sf{kh}{n}"):
                    ask(fq)
                    st.rerun()


def screen_chat(s: calc.SipSummary, m: dict):
    ss = st.session_state
    with st.container(key="backbtn"):
        b1, b2 = st.columns([1, 6], vertical_alignment="center")
        if b1.button("←", key="chat_back_btn", help="Back"):
            go(ss.chat_back if ss.chat_back in ("home", "fund") else "fund")
            st.rerun()
        b2.markdown(f'<div class="ph-title">✦ FinSaar</div><div class="ph-sub">{html.escape(s.fund)} · explains your '
                    f'SIP, doesn\'t advise</div>', unsafe_allow_html=True)

    if ss.pending:
        q = ss.pending
        ss.pending = None
        with st.spinner("FinSaar is reading your SIP…"):
            ss.turns.append(run_question(q, s))

    if not ss.turns:
        st.markdown('<div class="fs-card"><div class="fs-label">✦ FinSaar</div>Namaste! I explain <b>your own SIP '
                    'numbers</b> in English or Hinglish. Ask anything. I never tell you what to do with your money; '
                    'the decision is always yours.</div>', unsafe_allow_html=True)
    for i, r in enumerate(ss.turns):
        answer_card(r, s)
        if i == len(ss.turns) - 1 and i not in ss.feedback_done and r.kind != "limit":
            st.markdown('<div class="fs-help">Did this help?</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.container(key=f"fb{i}").columns(3)
            c1.button("Yes, clear", key=f"yes{i}", on_click=on_yes, args=(i,), type="primary")
            c2.button("Explain simpler", key=f"simp{i}", on_click=on_simpler, args=(i,))
            c3.button("Ask another", key=f"more{i}", on_click=on_another, args=(i,))
    if ss.hint:
        st.caption(ss.hint)
    st.pills("Try asking", m["chips"], key="chip", on_change=on_chip, selection_mode="single")
    with st.form("ask_form", clear_on_submit=True, border=False):
        c1, c2 = st.container(key="askbox").columns([4, 1])
        text = c1.text_input("Ask about your SIP", placeholder="Ask about your SIP…", label_visibility="collapsed",
                             max_chars=300)
        if c2.form_submit_button("➤", width="stretch") and text.strip():
            ask(text.strip())
            st.rerun()
    st.markdown(f'<div class="memory">{html.escape(memory_line())}<br><span>Learning lasts for this session; '
                f'cross-session learning is planned.</span></div>', unsafe_allow_html=True)


# ---------- side panels (outside the phone) ----------

def controls_panel():
    ss = st.session_state
    st.markdown('<div class="pc-h">Prototype controls</div>', unsafe_allow_html=True)
    ss.w_profile = ss.profile_label
    st.radio("Demo investor", list(PROFILES), key="w_profile", on_change=on_profile,
             captions=[PROFILE_HELP[p] for p in PROFILES])
    ss.w_scenario = ss.scenario
    st.selectbox("Journey moment · for testing only", list(SCENARIOS), format_func=SCENARIOS.get,
                 key="w_scenario", on_change=on_scenario)
    st.caption("The real flow is ③ The dip. ① and ② are for testing: the same SIP earlier, where the FinSaar "
               "card stays hidden because the value is not below invested.")
    c1, c2 = st.columns(2)
    c1.button("Simulate next visit", on_click=on_next_visit, width="stretch",
              help="Clears the chat but keeps what FinSaar learned, to show 'Last time: NAV. XIRR next?'")
    c2.button("Reset session", on_click=on_reset, width="stretch")
    st.markdown(f'<div class="pc-task"><b>🧪 Try this task</b><br>{TASK}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.page_link(HOW_PAGE, label="Guide", icon="📖")
    c2.page_link(EVAL_PAGE, label="Eval results", icon="✅")
    st.caption(f"Questions used: {ss.q_count}/{pipeline.LIMIT} · visit {ss.visit}")


NOTES = {
    "home": ("Entry point 1 · when value falls below invested",
             ["**Code decides** when the card appears: only when current value is below invested.",
              "A **card, not a pop-up** or push alert. Dismissible with *Maybe later*.",
              "After *Simulate next visit*, it becomes **entry point 3**: *Last time: NAV. XIRR next?*"]),
    "fund": ("Entry point 2 · tap a number",
             ["Tap **XIRR, Units or NAV** for *What does this mean for me?*",
              "*What it is* and *your number* come from **code and AMFI**; the AI only explains *what it means "
              "for you now*.",
              "The ✦ on each transaction explains **that** instalment from your own data (RAG).",
              "Change amount / Skip / Pause / Cancel are display-only."]),
    "chat": ("Entry point 4 · any question, English or Hinglish",
             ["Every answer passes the **eval gate**: numbers match code, no advice, no prediction, no fear, "
              "grounded sources, short. Open *How this answer was checked*.",
              "Ask *Should I stop and move to a better fund?* to see the **decline path**.",
              "**Yes, clear** / **Explain simpler** teach FinSaar within the session."]),
}


def notes_panel(screen: str):
    title, bullets = NOTES.get(screen, NOTES["home"])
    st.markdown(f'<div class="pc-h">How it works</div><div class="nt-h">{title}</div>', unsafe_allow_html=True)
    st.markdown("\n".join(f"- {b}" for b in bullets))
    st.markdown('<div class="nt-h" style="margin-top:14px">Behind every answer</div>', unsafe_allow_html=True)
    st.markdown("- **RAG:** reads your own SIP (instalments, units, NAV) + AMFI definitions.\n"
                "- **Personalised:** level, language and stage shape the answer.\n"
                "- **Learns:** remembers understood terms and *simpler* (this session).\n"
                "- **Code calculates; AI explains.** It never advises or predicts.")


# ---------- the app page ----------

def app_page():
    init_state()
    ss = st.session_state
    s = calc.compute(scenario=ss.scenario)
    m = moment(s)
    left, mid, right = st.columns([3.1, 4.4, 3.1], gap="medium")
    with left.container(key="ctrlpanel"):
        controls_panel()
    with mid:
        phone = st.container(key="phone", height=760)
        with phone:
            status_bar()
            try:
                if ss.screen == "chat":
                    screen_chat(s, m)
                elif ss.screen == "fund":
                    screen_fund(s, m)
                else:
                    screen_home(s, m)
            except Exception:  # never show a traceback inside the phone
                st.markdown(f'<div class="fs-card"><div class="fs-label">✦ FinSaar</div>Something went wrong on our '
                            f'side, so here are your plain numbers. Tap <b>Reset session</b> on the left to start '
                            f'again.{numbers_table(s)}</div>', unsafe_allow_html=True)
            if ss.sheet and ss.screen in ("fund", "home"):
                try:
                    bottom_sheet(s, m)
                except Exception:
                    ss.sheet = None
                    st.markdown(f'<div class="fs-card">Something went wrong, so here are your plain numbers.'
                                f'{numbers_table(s)}</div>', unsafe_allow_html=True)
    with right.container(key="notespanel"):
        notes_panel(ss.screen)


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
