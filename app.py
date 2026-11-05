"""FinSaar: Aapke SIP ka saar. Streamlit entry point."""
from __future__ import annotations

import html

import streamlit as st

import calc
import config
import pipeline
import ui_style

st.set_page_config(page_title="FinSaar · Aapke SIP ka saar", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

PROFILES = {"Beginner · Hinglish": "beginner-hinglish", "Knows basics · English": "basics-english"}
CHIPS = ["Iska matlab paisa doob gaya?", "What does XIRR mean for me?",
         "Why are units up but value down?", "Should I stop?"]
TILE_QUESTIONS = {"XIRR": "What does XIRR mean for me?", "Units": "What do my units mean for me?",
                  "NAV": "What does NAV mean for me?"}


# ---------- state ----------

def init_state():
    ss = st.session_state
    ss.setdefault("profile_label", "Beginner · Hinglish")
    ss.setdefault("understood", [])
    ss.setdefault("simpler", False)
    ss.setdefault("turns", [])
    ss.setdefault("feedback_done", set())
    ss.setdefault("panel_open", False)
    ss.setdefault("card_dismissed", False)
    ss.setdefault("q_count", 0)
    ss.setdefault("pending", None)
    ss.setdefault("hint", "")


def current_profile() -> dict:
    p = pipeline.default_profile(PROFILES[st.session_state.profile_label])
    p["understood"] = list(st.session_state.understood)
    p["simpler"] = st.session_state.simpler
    return p


def ask(question: str):
    st.session_state.pending = question
    st.session_state.panel_open = True
    st.session_state.hint = ""


def canonical_term(t: str) -> str:
    low = t.strip().lower()
    for key, name in [("average", "Average buy NAV"), ("xirr", "XIRR"), ("absolute", "Absolute return"),
                      ("nav", "NAV"), ("unit", "Units"), ("current value", "Current value"),
                      ("sip", "SIP"), ("redeem", "Redeem")]:
        if key in low:
            return name
    return t.strip().capitalize()


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


def render_answer(i: int, r: pipeline.Result, s: calc.SipSummary, is_last: bool):
    st.markdown(f'<div class="fs-q">{html.escape(r.question)}</div>', unsafe_allow_html=True)
    body = html.escape(r.answer).replace("\n", "<br>")
    extra = ""
    if r.show_numbers:
        extra = numbers_table(s) + (f'<div style="font-size:.72rem;margin-top:4px">Official source: '
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

    if is_last and i not in st.session_state.feedback_done and r.kind != "limit":
        c1, c2, c3 = st.container(key=f"fb{i}").columns(3)
        c1.button("Yes, clear", key=f"yes{i}", on_click=on_yes, args=(i,), type="primary")
        c2.button("Explain simpler", key=f"simp{i}", on_click=on_simpler, args=(i,))
        c3.button("Ask another", key=f"more{i}", on_click=on_another, args=(i,))


def memory_line() -> str:
    bits = [f"{t} ✓" for t in st.session_state.understood]
    if st.session_state.simpler:
        bits.append("prefers simpler answers")
    return "FinSaar remembers: " + (" · ".join(bits) if bits else "nothing yet")


def sip_screen():
    init_state()
    s = calc.compute()

    top_l, top_r = st.columns([3, 2], vertical_alignment="center")
    with top_l:
        with st.expander("🧪 Try this task (for mentors)", expanded=not st.session_state.turns):
            st.markdown('<div class="task">Your SIP is down. Find out <b>whether you\'ve lost money</b>, and '
                        '<b>what your XIRR means</b>. Then ask <b>whether you should stop</b>.</div>',
                        unsafe_allow_html=True)
    with top_r:
        st.segmented_control("Investor profile (switch to see personalisation)", list(PROFILES),
                             key="profile_label", selection_mode="single")
    if not st.session_state.profile_label:
        st.session_state.profile_label = "Beginner · Hinglish"

    left, right = st.columns([5, 6], gap="large")

    # ---------- left: the SIP screen ----------
    with left:
        st.markdown('<div class="section-title">My SIP</div>'
                    f'<div class="fund-head">{html.escape(s.fund)}</div>'
                    f'<div class="fund-sub">{html.escape(s.category)} · SIP {calc.inr(s.monthly_amount)}/month · '
                    f'{s.n_instalments} instalments</div>', unsafe_allow_html=True)
        gain_cls = "neg" if s.gain < 0 else ""
        sign = "−" if s.gain < 0 else "+"
        st.markdown(
            f'<div class="value-card"><div class="lbl">Current value</div><div class="big">{calc.inr(s.current_value)}</div>'
            f'<div class="row"><span>Invested</span><b>{calc.inr(s.invested)}</b></div>'
            f'<div class="row"><span>Total returns</span><b class="{gain_cls}">{sign}{calc.inr(s.gain)} '
            f'({calc.signed_pct(s.gain_pct, 2)})</b></div></div>', unsafe_allow_html=True)

        tiles = [("XIRR", calc.signed_pct(s.xirr_pct, 1)), ("Units", f"{s.total_units:.2f}"),
                 ("NAV", f"{calc.inr(s.current_nav, 2)}")]
        cols = st.container(key="tilebtn").columns(3)
        for col, (name, val) in zip(cols, tiles):
            col.markdown(f'<div class="tile"><div class="lbl">{name}</div><div class="v">{val}</div></div>',
                         unsafe_allow_html=True)
            col.button("What does this mean for me?", key=f"tile_{name}", on_click=ask,
                       args=(TILE_QUESTIONS[name],), help=f"Ask FinSaar about your {name}")

        if s.is_down and not st.session_state.panel_open and not st.session_state.card_dismissed:
            st.markdown(f'<div class="fs-card"><div class="fs-label">✦ FinSaar</div>Your SIP is '
                        f'<b>{calc.inr(s.gain)}</b> below what you invested. Want to understand it?</div>',
                        unsafe_allow_html=True)
            c1, c2, _ = st.container(key="nudge").columns([1, 1, 1])
            if c1.button("Explain this", type="primary"):
                st.session_state.panel_open = True
                st.rerun()
            if c2.button("Maybe later"):
                st.session_state.card_dismissed = True
                st.rerun()

    # ---------- right: the FinSaar panel ----------
    with right:
        st.markdown('<div class="section-title">✦ FinSaar · Aapke SIP ka saar</div>', unsafe_allow_html=True)
        if not st.session_state.panel_open:
            st.markdown('<div class="fs-empty">FinSaar explains your own SIP numbers in English or Hinglish. '
                        'Click <b>Explain this</b> or <b>What does this mean for me?</b> on the left to start.</div>',
                        unsafe_allow_html=True)
            st.write("")
            if st.button("✦ Ask FinSaar about this SIP", key="open_panel"):
                st.session_state.panel_open = True
                st.rerun()
            return

        if st.session_state.pending:
            q = st.session_state.pending
            st.session_state.pending = None
            if st.session_state.q_count >= pipeline.LIMIT:
                r = pipeline.Result(q, "uncertain", "limit", "limit",
                                    f"You've reached the {pipeline.LIMIT}-question limit for this demo session. "
                                    "Here are your numbers from your SIP data.", ["Your SIP data"], show_numbers=True)
            else:
                with st.spinner("FinSaar is reading your SIP…"):
                    history = [t.question for t in st.session_state.turns]
                    try:
                        r = pipeline.answer(q, current_profile(), history)
                    except Exception as e:  # last-resort guard: never show a stack trace
                        r = pipeline.Result(q, "uncertain", "answer", "fallback-error",
                                            pipeline.templates(s)["error"][current_profile()["language"]],
                                            ["Your SIP data"], show_numbers=True, error=type(e).__name__)
                st.session_state.q_count += 1
            st.session_state.turns.append(r)

        turns = st.session_state.turns
        for i, r in enumerate(turns):
            render_answer(i, r, s, is_last=(i == len(turns) - 1))

        if st.session_state.hint:
            st.caption(st.session_state.hint)

        st.pills("Try asking", CHIPS, key="chip", on_change=on_chip, selection_mode="single")
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
        c1, c2 = st.container(key="membox").columns([3, 1], vertical_alignment="center")
        c1.caption(f"Questions: {st.session_state.q_count}/{pipeline.LIMIT}")
        c2.button("Reset memory", on_click=on_reset_memory, key="reset_mem")


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
