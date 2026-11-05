"""Guide page: the problem, how FinSaar works inside the app, and where AI adds value. Ends with a Next button."""
import streamlit as st

import calc
import config


def render(next_page):
    s = calc.compute()

    st.markdown("### Your SIP speaks in numbers; FinSaar helps you make sense of them in your terms.")
    st.markdown(
        "First-time MF investors judge their SIP only by profit or loss. Other financial parameters (XIRR, units, "
        "NAV, etc.) mean little to them, as they lack the knowledge to interpret them and assess performance. When "
        "returns drop, they look outside the app for answers. This gap and uncertainty can make them question "
        "continuing, increasing the risk of pausing or stopping within 12 months."
    )
    st.caption("FinSaar (\"saar\" = essence · Aapke SIP ka saar) is a concept feature inside a Groww-style app. "
               "It is not another chatbot: it sits on the investor's own SIP, at a moment they are already unsure, "
               "and explains their own numbers. It builds understanding; it never nudges anyone to stay.")

    st.markdown("#### Try it in 4 steps")
    steps = [
        ("Open the app", f"Press <b>Next</b>. The phone shows the investor's SIP, {calc.inr(s.gain)} below what "
                         "they invested, with a <b>FinSaar card</b>. Tap <b>Explain this</b>."),
        ("Tap a number", "Open the fund and tap <b>XIRR, Units or NAV</b>. A sheet shows what it is, your number, "
                         "and what it means for you now."),
        ("Ask anything", "In the FinSaar chat, ask in English or Hinglish. Then <b>Yes, clear</b>, <b>Explain "
                         "simpler</b> or <b>Ask another</b>. Try <i>Should I stop?</i>"),
        ("Switch and come back", "On the left, switch the <b>demo investor</b>, or press <b>Simulate next visit</b> "
                                 "to see <i>Last time: NAV. XIRR next?</i>"),
    ]
    cols = st.columns(4)
    for n, (col, (title, body)) in enumerate(zip(cols, steps), 1):
        col.markdown(f'<div class="step"><span class="n">{n}</span><b class="t">{title}</b><br>{body}</div>',
                     unsafe_allow_html=True)

    st.info("**Try this task:** Your SIP is down. Find out whether you've lost money and what your XIRR means. "
            "Then ask whether you should stop.")

    st.markdown("#### Where FinSaar shows up (entry points)")
    st.markdown(
        "1. **When value falls below invested:** a card on the SIP screen. Dismissible; never a pop-up or push alert.\n"
        "2. **On a number:** tap XIRR, NAV or units → *What does this mean for me?*\n"
        "3. **When you come back:** *Last time: NAV. XIRR next?* (in-app only).\n"
        "4. **Then any question,** in English or Hinglish. A dip note gives one fixed explanation; FinSaar starts "
        "with yours."
    )

    st.markdown("#### Where AI adds value")
    a, b = st.columns(2)
    with a:
        st.markdown("**Code calculates**")
        st.markdown("- Invested, value, units, NAV history, XIRR\n- When the FinSaar card appears")
        st.markdown("**AI handles**")
        st.markdown("- Messy or Hinglish questions\n- Picking the relevant SIP data and definitions\n"
                    "- Explaining the numbers together\n- Adapting to level and language\n- Follow-ups")
    with b:
        st.markdown("**AI does not**")
        st.markdown("- Recommend funds or stocks\n- Predict returns or say a fall will recover\n"
                    "- Say continue, pause or stop\n- Use fear, FOMO or urgency\n- Invent data")
        st.markdown("**What a non-AI version misses**")
        st.markdown("A fixed dip note or FAQ gives everyone the same text. It can't take questions in their own "
                    "words or Hinglish, can't answer follow-ups, can't change depth, and can't remember what they "
                    "understood, so they still Google.")

    st.markdown("#### Every answer is checked")
    st.markdown("- **✓ Checked** means the answer passed every check before you saw it: numbers match your data, "
                "no advice, no prediction, no fear or urgency, sources listed, short enough.\n"
                "- Otherwise FinSaar retries once, then shows a **safe fallback** (plain numbers and the official "
                "source, or the neutral options for decision questions).\n"
                "- Open **How this answer was checked** under any answer, or the **Eval results** page for the "
                "golden-set score.")

    st.caption(f"Memory lasts for this session (cross-session learning is planned) · {config.SESSION_QUESTION_LIMIT} "
               "questions per session · nothing you type is stored · all data is fictional · concept prototype, not "
               "investment advice, not affiliated with Groww. Journey moments ① and ② in the controls are for "
               "testing only.")

    st.write("")
    c1, _ = st.columns([1, 2])
    if c1.button("Next: Open the app →", type="primary", key="next_btn"):
        st.switch_page(next_page)
