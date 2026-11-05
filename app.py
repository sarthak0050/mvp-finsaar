"""FinSaar: Aapke SIP ka saar. Streamlit entry point."""
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
SCENARIOS = {sc["id"]: sc["label"] for sc in calc.scenarios()}
DEFAULT_SCENARIO = calc.load_sip().get("default_scenario", "dip")


# ---------- what FinSaar offers at each moment of the journey ----------

def moment(s: calc.SipSummary) -> dict:
    """Nudge, suggested questions and tap-to-explain questions for this moment. All numbers come from calc."""
    first = s.instalments[0]
    xirr_txt = calc.signed_pct(s.xirr_pct, 1) if s.xirr_pct is not None else None
    if s.scenario == "start":
        return {
            "icon": "🎉", "tone": "info",
            "nudge": f"Your first SIP instalment is done. {calc.inr(first.amount)} bought "
                     f"<b>{first.units:.2f} units</b> at NAV {calc.inr(first.nav, 2)}. Want to see what that means?",
            "nudge_q": "What did my first ₹2,000 buy?",
            "chips": ["What did my first ₹2,000 buy?", "What is NAV?", "Why is XIRR not shown yet?",
                      "What happens at my next instalment?"],
            "tiles": {"Returns": "Why are my returns zero?", "XIRR": "Why is XIRR not shown yet?",
                      "Units": f"What do my {s.total_units:.2f} units mean?", "NAV": "What does NAV mean for me?"},
        }
    if s.is_up:
        return {
            "icon": "📈", "tone": "up",
            "nudge": f"Your SIP is <b>{calc.inr(s.gain)} above</b> what you invested. Curious what is behind it?",
            "nudge_q": "Why is my value up?",
            "chips": ["Why is my value up?", "What does XIRR mean for me?", "Why did I get fewer units in July?",
                      "Should I invest more?"],
            "tiles": {"Returns": "Why is my value up?", "XIRR": f"What does my XIRR of {xirr_txt} mean?",
                      "Units": f"What do my {s.total_units:.2f} units mean?", "NAV": "What does NAV mean for me?"},
        }
    return {
        "icon": "💬", "tone": "down",
        "nudge": f"Your SIP is <b>{calc.inr(s.gain)} below</b> what you invested. Want to understand it?",
        "nudge_q": "Iska matlab paisa doob gaya?",
        "chips": ["Iska matlab paisa doob gaya?", "What does XIRR mean for me?",
                  "Why are units up but value down?", "Should I stop?"],
        "tiles": {"Returns": "Iska matlab paisa doob gaya?", "XIRR": f"What does my XIRR of {xirr_txt} mean?",
                  "Units": "Why are units up but value down?", "NAV": "What does NAV mean for me?"},
    }


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
    ss.setdefault("dialog_cache", {})


def current_profile() -> dict:
    p = pipeline.default_profile(PROFILES[st.session_state.profile_label])
    p["understood"] = list(st.session_state.understood)
    p["simpler"] = st.session_state.simpler
    return p


def ask(question: str):
    st.session_state.pending = question
    st.session_state.hint = ""


def canonical_term(t: str) -> str:
    low = t.strip().lower()
    for key, name in [("average", "Average buy NAV"), ("xirr", "XIRR"), ("annuali", "XIRR"), ("absolute", "Absolute return"),
                      ("nav", "NAV"), ("unit", "Units"), ("current value", "Current value"),
                      ("sip", "SIP"), ("redeem", "Redeem")]:
        if key in low:
            return name
    return t.strip().capitalize()


def run_question(q: str, s: calc.SipSummary) -> pipeline.Result:
    """One question through the full pipeline, with the session limit and a last-resort guard."""
    if st.session_state.q_count >= pipeline.LIMIT:
        return pipeline.Result(q, "uncertain", "limit", "limit",
                               f"You've reached the {pipeline.LIMIT}-question limit for this demo session. "
                               "Here are your numbers from your SIP data.", ["Your SIP data"], show_numbers=True)
    st.session_state.q_count += 1
    history = [t.question for t in st.session_state.turns]
    try:
        return pipeline.answer(q, current_profile(), history, scenario=s.scenario)
    except Exception as e:  # never show a stack trace
        return pipeline.Result(q, "uncertain", "answer", "fallback-error",
                               pipeline.templates(s)["error"][current_profile()["language"]],
                               ["Your SIP data"], show_numbers=True, error=type(e).__name__)


def on_scenario():
    if not st.session_state.scenario:
        st.session_state.scenario = DEFAULT_SCENARIO
    st.session_state.turns = []
    st.session_state.feedback_done = set()
    st.session_state.card_dismissed = False
    st.session_state.hint = ""


# ---------- callbacks ----------

def on_chip():
    q = st.session_state.get("chip")
    if q:
        ask(q)
    st.session_state.chip = None


def on_yes(i: int):
    r = st.session_state.turns[i]
    for t in r.terms_explained:
        name = canonical_term(t)
        if name and name not in st.session_state.understood:
            st.session_state.understood.append(name)
    st.session_state.feedback_done.add(i)
    st.session_state.hint = "Great. Ask another question below whenever you like."


def on_simpler(i: int):
    st.session_state.simpler = True
    st.session_state.feedback_done.add(i)
    ask(st.session_state.turns[i].question)


def on_another(i: int):
    st.session_state.feedback_done.add(i)
    st.session_state.hint = "Pick a question below or type your own."


def on_reset_memory():
    st.session_state.understood = []
    st.session_state.simpler = False


# ---------- rendering ----------

def numbers_table(s: calc.SipSummary) -> str:
    rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>"
                   for k, v in calc.numbers_summary(s))
    return f'<table class="fs-nums">{rows}</table>'


def status_line(r: pipeline.Result) -> str:
    if r.kind == "fallback-error":
        return '<div class="fs-warn">⚠ AI unavailable · safe fallback shown · Source: your SIP data</div>'
    if r.kind == "fallback-unsure":
        return '<div class="fs-warn">⚠ AI answer did not pass the checks · safe fallback shown</div>'
    if r.kind == "limit":
        return '<div class="fs-warn">Question limit reached for this session</div>'
    if r.gate_passed:
        extra = " · fixed safe reply" if r.kind == "template" else ""
        return f'<div class="fs-check">✓ Checks passed · Source: your SIP data, AMFI{extra}</div>'
    return '<div class="fs-warn">⚠ Safe fallback shown</div>'


def answer_card(r: pipeline.Result, s: calc.SipSummary, show_question: bool = True):
    if show_question:
        st.markdown(f'<div class="fs-q">{html.escape(r.question)}</div>', unsafe_allow_html=True)
    body = html.escape(r.answer).replace("\n", "<br>")
    extra = ""
    if r.show_numbers:
        extra = numbers_table(s) + (f'<div style="font-size:.75rem;margin-top:4px">Official source: '
                                    f'<a href="{html.escape(config.amfi_link())}" target="_blank">AMFI investor education</a></div>')
    st.markdown(f'<div class="fs-card"><div class="fs-label">✦ FinSaar · AI</div>{body}{extra}'
                f'{status_line(r)}</div>', unsafe_allow_html=True)

    with st.expander("How this answer was checked"):
        if r.gate:
            for c in r.gate.checks:
                st.markdown(f"{'✅' if c.passed else '❌'} **{c.name}**: {html.escape(c.detail)}")
        if len(r.attempts) > 1 or (r.attempts and not r.attempts[-1]["passed"]):
            for n, a in enumerate(r.attempts, 1):
                if not a["passed"]:
                    st.markdown(f"↻ Try {n} was blocked: {html.escape('; '.join(a['reasons']))}")
        st.markdown(f"**Route:** {r.intent} → shown as *{r.path}* ({r.kind})")
        if r.error:
            st.caption("The AI service did not respond in time or hit its limit.")
        st.markdown(f"**Numbers used:** {', '.join(r.numbers_used) or 'only the app-computed numbers above'}")
        st.markdown(f"**Sources:** {', '.join(r.sources)}")
        st.markdown(f"**Retrieved chunks** ({r.retrieval}):")
        for c in r.chunks:
            st.caption(f"{c.label}: {c.text[:220]}{'…' if len(c.text) > 220 else ''}")


def render_answer(i: int, r: pipeline.Result, s: calc.SipSummary, is_last: bool):
    answer_card(r, s)
    if is_last and i not in st.session_state.feedback_done and r.kind != "limit":
        c1, c2, c3 = st.container(key=f"fb{i}").columns(3)
        c1.button("Yes, clear", key=f"yes{i}", on_click=on_yes, args=(i,), type="primary")
        c2.button("Explain simpler", key=f"simp{i}", on_click=on_simpler, args=(i,))
        c3.button("Ask another", key=f"more{i}", on_click=on_another, args=(i,))


# ---------- tap a number → "FinSaar explains" sheet ----------

def _dialog_yes(r: pipeline.Result):
    for t in r.terms_explained:
        name = canonical_term(t)
        if name and name not in st.session_state.understood:
            st.session_state.understood.append(name)


def _dialog_simpler():
    st.session_state.simpler = True


@st.dialog("✦ FinSaar explains", width="large")
def explain_dialog(question: str):
    s = calc.compute(scenario=st.session_state.scenario)
    ck = f"{s.scenario}|{question}|{st.session_state.profile_label}|{st.session_state.simpler}"
    kh = hashlib.md5(ck.encode()).hexdigest()[:10]
    cache = st.session_state.dialog_cache
    if ck not in cache:
        with st.spinner("FinSaar is reading your SIP…"):
            r = run_question(question, s)
        cache[ck] = r
        st.session_state.turns.append(r)                       # also appears in the chat history
        st.session_state.feedback_done.add(len(st.session_state.turns) - 1)
    r = cache[ck]
    st.markdown(f"**{html.escape(question)}**")
    answer_card(r, s, show_question=False)
    c1, c2, c3 = st.container(key=f"fbdlg{kh}").columns(3)
    if c1.button("Yes, clear", key=f"dy{kh}", type="primary"):
        _dialog_yes(r)
        st.rerun()
    c2.button("Explain simpler", key=f"ds{kh}", on_click=_dialog_simpler, disabled=st.session_state.simpler)
    if c3.button("Ask more in chat", key=f"dm{kh}"):
        st.session_state.hint = "Ask a follow-up below."
        st.rerun()


def memory_line() -> str:
    bits = [f"{t} ✓" for t in st.session_state.understood]
    if st.session_state.simpler:
        bits.append("prefers simpler answers")
    return "FinSaar remembers: " + (" · ".join(bits) if bits else "nothing yet")


# ---------- the MVP page ----------

def sip_screen():
    init_state()
    s = calc.compute(scenario=st.session_state.scenario)
    m = moment(s)
    to_explain = None

    top_l, top_r = st.columns([3, 2], vertical_alignment="bottom")
    with top_l:
        st.segmented_control("Investor journey (see FinSaar at each moment)", list(SCENARIOS),
                             format_func=SCENARIOS.get, key="scenario", on_change=on_scenario)
    with top_r:
        st.segmented_control("Investor profile", list(PROFILES), key="profile_label")
    if not st.session_state.profile_label:
        st.session_state.profile_label = "Beginner · Hinglish"
    with st.expander("🧪 Mentor task", expanded=False):
        st.markdown('<div class="task">On <b>③ The dip</b>: find out <b>whether you\'ve lost money</b> and '
                    '<b>what your XIRR means</b>. Then ask <b>whether you should stop</b>. '
                    'Also try ① and ② to see FinSaar at the start and in between.</div>', unsafe_allow_html=True)

    left, right = st.columns([11, 10], gap="large")

    # ---------------- left: the investing app ----------------
    with left:
        st.markdown(
            f'<div class="g-appbar"><span class="g-back">←</span><span class="g-logo">SF</span>'
            f'<div><div class="g-fund">{html.escape(s.fund)}</div>'
            f'<div class="g-tags"><span>Equity</span><span>Flexi Cap</span><span>Direct · Growth</span></div></div></div>',
            unsafe_allow_html=True)

        st.markdown(
            f'<div class="g-hold"><div class="g-hold-l"><div class="lbl">Current value</div>'
            f'<div class="big">{calc.inr(s.current_value)}</div></div>'
            f'<div class="g-hold-r"><div class="lbl">Invested</div><div class="mid">{calc.inr(s.invested)}</div></div>'
            f'</div>', unsafe_allow_html=True)

        if s.is_down or s.is_up:
            ret = f"{'−' if s.is_down else '+'}{calc.inr(s.gain)} ({calc.signed_pct(s.gain_pct, 2)})"
        else:
            ret = "₹0 (0.00%)"
        tone = "neg" if s.is_down else "pos" if s.is_up else ""
        tiles = [("Returns", ret, tone), ("XIRR", calc.signed_pct(s.xirr_pct, 1) if s.xirr_pct is not None else "—", tone),
                 ("Units", f"{s.total_units:.2f}", ""), ("NAV", calc.inr(s.current_nav, 2), "")]
        st.markdown('<div class="g-hint">✦ Tap any number to see FinSaar explain it</div>', unsafe_allow_html=True)
        cols = st.container(key="tilebtn").columns(4)
        for col, (name, val, tn) in zip(cols, tiles):
            colour = {"neg": ":red", "pos": ":green"}.get(tn, "")
            v = f"{colour}[**{val}**]" if colour else f"**{val}**"
            if col.button(f"{name} :green[✦]  \n{v}", key=f"tile_{name}", width="stretch",
                          help=f"FinSaar explains: {m['tiles'][name]}"):
                to_explain = m["tiles"][name]

        # FinSaar nudge for this moment
        if not st.session_state.card_dismissed:
            st.markdown(f'<div class="fs-card nudge-{m["tone"]}"><div class="fs-label">✦ FinSaar</div>'
                        f'{m["icon"]} {m["nudge"]}</div>', unsafe_allow_html=True)
            c1, c2, _ = st.container(key="nudge").columns([1, 1, 1])
            if c1.button("Explain this", type="primary", key="nudge_go"):
                st.session_state.card_dismissed = True
                ask(m["nudge_q"])
                st.rerun()
            if c2.button("Maybe later", key="nudge_later"):
                st.session_state.card_dismissed = True
                st.rerun()

        # SIP details card
        nxt = calc.fmt_date(s.next_instalment) if s.next_instalment else "—"
        st.markdown(
            f'<div class="g-card"><div class="g-card-h">SIP details <span class="g-pill">Active</span></div>'
            f'<div class="g-row"><span>Monthly amount</span><b>{calc.inr(s.monthly_amount)}</b></div>'
            f'<div class="g-row"><span>Instalments done</span><b>{s.n_instalments}</b></div>'
            f'<div class="g-row"><span>Next instalment</span><b>{nxt}</b></div>'
            f'<div class="g-row"><span>Average buy NAV</span><b>{calc.inr(s.avg_nav, 2)}</b></div></div>',
            unsafe_allow_html=True)

        # Transactions, with FinSaar in between
        st.markdown('<div class="g-card-h" style="margin-top:.8rem">Transactions</div>', unsafe_allow_html=True)
        tx = st.container(key="txlist")
        prev = None
        for idx, inst in enumerate(reversed(s.instalments)):
            real = len(s.instalments) - 1 - idx
            prev = s.instalments[real - 1] if real > 0 else None
            if prev is None:
                note, q = "First buy", f"What did my first {calc.inr(inst.amount)} buy?"
            elif inst.units > prev.units:
                note, q = "Why more units?", f"Why did my {calc.fmt_date(inst.date)} instalment buy more units?"
            else:
                note, q = "Why fewer units?", f"Why did my {calc.fmt_date(inst.date)} instalment buy fewer units?"
            c1, c2 = tx.columns([3, 1], vertical_alignment="center")
            c1.markdown(
                f'<div class="g-tx"><div><b>SIP instalment</b><div class="sub">{calc.fmt_date(inst.date)} · '
                f'NAV {inst.nav:.2f}</div></div><div class="amt">{calc.inr(inst.amount)}'
                f'<div class="sub">{inst.units:.2f} units</div></div></div>', unsafe_allow_html=True)
            if c2.button(f":green[✦] {note}", key=f"tx_{real}", width="stretch", help=f"FinSaar explains: {q}"):
                to_explain = q

    # ---------------- right: FinSaar chat ----------------
    with right:
        st.markdown('<div class="section-title">✦ FinSaar · Aapke SIP ka saar</div>', unsafe_allow_html=True)

        if st.session_state.pending:
            q = st.session_state.pending
            st.session_state.pending = None
            with st.spinner("FinSaar is reading your SIP…"):
                st.session_state.turns.append(run_question(q, s))

        turns = st.session_state.turns
        if not turns:
            st.markdown('<div class="fs-card"><div class="fs-label">✦ FinSaar</div>Namaste! I explain <b>your own '
                        'SIP numbers</b> in English or Hinglish. Tap any number on the left, or ask below. '
                        'I never tell you what to do with your money; the decision is always yours.</div>',
                        unsafe_allow_html=True)
        for i, r in enumerate(turns):
            render_answer(i, r, s, is_last=(i == len(turns) - 1))

        if st.session_state.hint:
            st.caption(st.session_state.hint)

        st.pills("Try asking", m["chips"], key="chip", on_change=on_chip, selection_mode="single")
        with st.form("ask_form", clear_on_submit=True, border=False):
            c1, c2 = st.container(key="askbox").columns([5, 1])
            text = c1.text_input("Ask anything about your SIP", placeholder="Type in English or Hinglish…",
                                 label_visibility="collapsed", max_chars=300)
            if c2.form_submit_button("Ask", width="stretch") and text.strip():
                ask(text.strip())
                st.rerun()

        st.markdown(f'<div class="memory">{html.escape(memory_line())}<br><span style="color:#888">Learning lasts '
                    f'for this session only; learning across sessions is planned.</span></div>',
                    unsafe_allow_html=True)
        c1, c2 = st.container(key="membox").columns([2, 1], vertical_alignment="center")
        c1.caption(f"Questions: {st.session_state.q_count}/{pipeline.LIMIT}")
        c2.button("Reset memory", on_click=on_reset_memory, key="reset_mem")

    if to_explain:
        explain_dialog(to_explain)


# ---------- navigation (no sidebar: How to use → FinSaar MVP, plus Eval) ----------
import how_to_use  # noqa: E402

MVP_PAGE = st.Page(sip_screen, title="② FinSaar MVP", url_path="mvp")
HOW_PAGE = st.Page(lambda: how_to_use.render(MVP_PAGE), title="① How to use", url_path="how-to-use", default=True)
EVAL_PAGE = st.Page("eval_page.py", title="Eval results", url_path="eval")
PAGES = [HOW_PAGE, MVP_PAGE, EVAL_PAGE]

ui_style.apply()
pg = st.navigation(PAGES, position="hidden")
nav = st.container(key="topnav")
for col, page in zip(nav.columns(len(PAGES)), PAGES):
    col.page_link(page, label=page.title)
pg.run()
