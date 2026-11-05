"""'How to use' page: a short guide for investors and mentors."""
import streamlit as st

import calc
import config

s = calc.compute()

st.markdown("### How to use FinSaar")
st.markdown(
    f"FinSaar (*\"Aapke SIP ka saar\"*) explains **your own SIP numbers** in simple English or Hinglish when your "
    f"SIP value is below what you invested. In this demo, a fictional SIP of {calc.inr(s.monthly_amount)}/month "
    f"is {calc.inr(s.gain)} below the amount invested."
)

st.markdown("#### Try it in 5 steps")
st.markdown(
    """
1. **Open *My SIP*.** You see the fund, what you invested, today's value, and the XIRR, Units and NAV tiles.
2. **Tap *Explain this*** on the green FinSaar card, or tap **What does this mean for me?** under any tile.
3. **Ask a question.** Tap a suggested question or type your own, in English or Hinglish
   (e.g. *"Iska matlab paisa doob gaya?"*).
4. **Tell FinSaar if it helped**, using the buttons under each answer:
   - **Yes, clear**: FinSaar remembers the terms explained and won't define them again.
   - **Explain simpler**: you get the same answer in simpler words, and later answers stay simple.
   - **Ask another**: move on to a new question.
5. **Switch the profile** at the top (*Beginner · Hinglish* ↔ *Knows basics · English*) and ask again
   to see how the answer changes.
"""
)

st.markdown("#### Mentor task")
st.info("Your SIP is down. Find out **whether you've lost money**, and **what your XIRR means**. "
        "Then ask **whether you should stop**.")

st.markdown("#### Reading an answer")
st.markdown(
    """
- Answers from the AI sit in a **green card labelled "✦ FinSaar · AI"**. Everything else is normal app content.
- **✓ Checks passed** means the answer passed every quality check before you saw it:
  numbers match your SIP data · no advice · no predictions · no fear or urgency · sources listed · short enough.
- Open **How this answer was checked** to see each check, the sources used and the numbers used.
- **⚠ Safe fallback shown** means the AI answer did not pass, or the AI was busy, so FinSaar shows
  your plain numbers and the official source instead of guessing.
"""
)

st.markdown("#### What FinSaar will not do")
st.markdown(
    """
- **No advice.** It won't tell you to continue, pause, stop, switch or buy, and it won't recommend any fund.
  Ask *"Should I stop?"* and it explains what each option means, then says **the decision is yours**.
- **No predictions.** It won't say whether the value will recover or what it will be worth later.
- **No made-up numbers.** All numbers are calculated by the app, not by the AI.
"""
)

st.markdown("#### Good to know")
st.markdown(
    f"""
- **Memory lasts for this session only.** The line *"FinSaar remembers: …"* shows what it has learned.
  **Reset memory** clears it. Learning across sessions is planned.
- **Limit:** {config.SESSION_QUESTION_LIMIT} questions per session, to keep the demo free for everyone.
- **Privacy:** nothing you type is stored. Closing the tab clears everything.
- **Eval results** shows how FinSaar scored on a fixed set of real investor questions.
- All data is **fictional**. This is a concept prototype, not investment advice, and not affiliated with Groww.
"""
)

st.markdown("#### Hinglish mein")
st.markdown(
    "*My SIP* kholiye → **Explain this** dabaiye → koi bhi sawaal poochiye (English ya Hinglish). "
    "Samajh aaye toh **Yes, clear**, nahi toh **Explain simpler**. FinSaar kabhi nahi batayega ki SIP band karein "
    "ya chalu rakhein: woh sirf options samjhata hai, **faisla aapka hai**."
)
