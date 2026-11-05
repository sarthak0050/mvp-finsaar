"""'How to use' page: the landing page. Ends with a Next button into the MVP."""
import streamlit as st

import calc
import config


def render(next_page):
    s = calc.compute()

    st.markdown("### How to use FinSaar")
    st.markdown(
        f"FinSaar explains **your own SIP numbers** in simple English or Hinglish when your SIP value falls below "
        f"what you invested. In this demo, a fictional SIP of {calc.inr(s.monthly_amount)}/month is "
        f"**{calc.inr(s.gain)} below** the amount invested. You can ask FinSaar anything about it."
    )

    st.markdown("#### Try it in 4 steps")
    steps = [
        ("Start on Investments", "You land on a Groww-style <b>Investments</b> dashboard. The <b>NEW FEATURE · "
                                 "FinSaar</b> card offers to explain your SIP. Click <b>Understand my SIP →</b>."),
        ("Tap any number", "On the fund page, tap <b>Returns, XIRR, Units or NAV</b> and a <b>FinSaar explains</b> sheet opens right "
                           "there. In <b>Transactions</b>, tap <b>✦ Why more units?</b> on any instalment."),
        ("Ask anything", "Use the FinSaar chat on the right: tap a suggested question or type your own, in English "
                         "or Hinglish. Then <b>Yes, clear</b>, <b>Explain simpler</b> or <b>Ask another</b>."),
        ("Try every moment", "In the grey mentor bar on top, pick the <b>journey moment</b> (① first instalment, "
                             "② month 3, ③ the dip) and the <b>profile</b> (Beginner · Hinglish / Knows basics · "
                             "English) and see FinSaar change."),
    ]
    cols = st.columns(4)
    for n, (col, (title, body)) in enumerate(zip(cols, steps), 1):
        col.markdown(f'<div class="step"><span class="n">{n}</span><b class="t">{title}</b><br>{body}</div>',
                     unsafe_allow_html=True)

    st.markdown("#### Mentor task")
    st.info("On **③ The dip**: find out **whether you've lost money**, and **what your XIRR means**. "
            "Then ask **whether you should stop**. Then try **①** and **②** to see FinSaar at the start and in between.")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Reading an answer")
        st.markdown(
            """
- AI answers sit in a **green card labelled "✦ FinSaar · AI"**. Everything else is normal app content.
- **✓ Checks passed**: the answer passed every quality check before you saw it (numbers match your SIP data,
  no advice, no predictions, no fear or urgency, sources listed, short enough).
- **How this answer was checked** shows each check, the sources and the numbers used.
- **⚠ Safe fallback shown**: the AI answer did not pass, or the AI was busy, so FinSaar shows your plain
  numbers and the official source instead of guessing.
"""
        )
    with right:
        st.markdown("#### What FinSaar will not do")
        st.markdown(
            """
- **No advice.** It won't tell you to continue, pause, stop, switch or buy, or recommend any fund.
  Ask *"Should I stop?"* and it explains each option, then says **the decision is yours**.
- **No predictions.** It won't say whether the value will recover or what it will be worth later.
- **No made-up numbers.** The app calculates every number; the AI only explains them.
"""
        )

    st.markdown("#### Good to know")
    st.markdown(
        f"""
- **Memory lasts for this session only.** *"FinSaar remembers: …"* shows what it has learned; **Reset memory**
  clears it. Learning across sessions is planned.
- **{config.SESSION_QUESTION_LIMIT} questions per session**, to keep the demo free for everyone. Nothing you type is stored.
- **Eval results** (top bar) shows how FinSaar scored on a fixed set of real investor questions.
- Only **FinSaar** and what it needs work. Other Groww-style tabs and buttons are for look only.
- All data is **fictional**. FinSaar is a concept feature for Groww; this prototype is not investment advice and not affiliated with Groww.
"""
    )
    st.caption("Hinglish mein: Next dabaiye → koi bhi number tap kariye (Returns, XIRR, Units, NAV) → FinSaar samjhayega. Ya chat mein koi bhi sawaal poochiye. Samajh aaye toh Yes, clear, "
               "nahi toh Explain simpler. FinSaar kabhi nahi batayega ki SIP band karein ya chalu rakhein: "
               "faisla aapka hai.")

    st.write("")
    c1, _ = st.columns([1, 2])
    if c1.button("Next: Open the app →", type="primary", key="next_btn"):
        st.switch_page(next_page)
