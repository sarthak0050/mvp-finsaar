# FinSaar · "Aapke SIP ka saar"

A concept prototype that helps first-time mutual fund investors understand their own SIP numbers when the
value falls below what they invested, in English or Hinglish. Every AI answer passes a visible quality check
(the **eval gate**) or is replaced by a safe fallback. It never gives investment advice or predictions.

> Concept prototype · Not investment advice · Not affiliated with Groww. All data is fictional.

## The prototype

**Desktop:** a phone frame in the centre shows a Groww-style app with FinSaar inside it. On the left,
**Prototype controls** (demo investor, journey moment for testing, Simulate next visit, Reset session, the
mentor task, Guide and Eval links). On the right, **How it works** notes for the current screen.
**Phone:** just the app, full screen (controls below).

Screens inside the phone:

1. **Home / Investments:** SIP card; when value < invested, the FinSaar card *"Your SIP is ₹496 below what you
   invested. Want to understand it?"* (Explain this · Maybe later). Code decides when it appears.
2. **Fund page:** value, returns, XIRR / Units / NAV chips, a "Your SIP this month" card built only from the
   investor's own data, display-only Change amount / Skip / Pause / Cancel SIP, transactions with ✦ explainers.
3. **Bottom sheet:** tap a number → *What it is* (definition) · *Your number* (calc) · *What it means for you now*
   (AI, gated) · follow-up chips.
4. **FinSaar chat:** any question in English or Hinglish; every answer shows "✓ Checked …" and
   "How this answer was checked".
5. **Advice question:** neutral options, "the decision is yours", SEBI registered-adviser and AMFI links.
6. **Close the loop:** Did this help? Yes, clear · Explain simpler · Ask another; "FinSaar remembers: …".
7. **Next visit:** *Last time: NAV. XIRR next?* (Continue · Not now), after **Simulate next visit**.

Journey moments ① first instalment and ② month 3 are **for testing only**; the real flow is ③ the dip.
Out of scope by design: market or category comparisons, a pre-dip course, a fixed dip note, push alerts.
Only FinSaar and what it needs work; the other Groww-style tabs and buttons are display-only. The layout is
Groww-style but uses a plain text wordmark, not Groww's logo or brand assets.

## How an answer is made

```
question
  → intent rule (no AI):  advice/decision → decline   ·   prediction → uncertain   ·   else → answer
  → retrieve (rag.py):    top 3 chunks from data/knowledge.md (Gemini embeddings + cosine;
                          keyword-overlap fallback) + the "SIP facts" block from calc.py
  → personalise:          level, language, terms already understood, "simpler" flag (session only)
  → generate (llm.py):    Gemini, JSON only {answer, numbers_used, sources, terms_explained}, 15 s timeout
  → gate (gate.py):       pass → show with "✓ Checks passed"
                          fail → retry once with the reasons → fail → safe fallback
```

* **Prediction questions** ("What will it be worth next year?") never reach the model. They get a fixed
  "I can't predict" reply plus the plain numbers.
* **Decision questions** ("Should I stop?", "Which fund?") get a neutral explanation of pause / skip / change
  amount / stop that ends with "The decision is yours". If the AI fails or is unavailable, a fixed neutral text
  is shown, so these questions always decline.
* **API error / quota hit:** a friendly note plus the numbers from `calc.py`. No stack traces.
* If the main model is busy (503/504/429), the call is retried once on `GEMINI_FALLBACK_MODEL`.

## Eval gate checks (every answer)

| Check | Rule |
|---|---|
| Numbers match | every ₹ amount, %, NAV and unit count matches a `calc.py` value within rounding (e.g. ₹9,504 or "about ₹9,500"). Dates and small counts ("5 months") are ignored |
| No advice | English + Hinglish decision phrases ("you should", "stay invested", "band kar do", "continue karo"…). A negated phrase in the same clause ("I can't tell you whether to continue your SIP") is allowed |
| No prediction | "will recover", "will go up", "market will"…; allowed only when negated ("no one can say whether it will recover") |
| No fear or urgency | "hurry", "huge loss", "act now", "don't miss"… |
| Grounded | at least one source, and every source is a retrieved chunk or "Your SIP data" |
| Readable | ≤ 80 words (beginner) or ≤ 120 (knows basics) |
| Decision left to you | decline answers only: must say "The decision is yours" / "Faisla aapka hai" |

The phrase lists live at the top of `gate.py`; add to them as you find new cases.

## Files

| File | What it does |
|---|---|
| `app.py` | Streamlit host: builds all data from `calc.py`, runs questions through `pipeline.py`, runs the golden set, and mounts the front end |
| `ui/finsaar.js`, `ui/finsaar.css` | the FinSaar app front end (Streamlit custom component v2): Explore, Dashboard, SIPs, Watchlist, Quality, fund pages, explainer sheets and the chat |
| `data/eval_history.json` | saved golden-set runs shown on the Quality tab |
| `calc.py` | all numbers (units, average NAV, value, gain/loss, XIRR via bisection) |
| `rag.py` | parses `knowledge.md`, embeddings + cosine, keyword fallback (cached) |
| `llm.py` | system prompt, Gemini JSON call, model fallback, LLM judge for evals |
| `gate.py` | the eval gate |
| `pipeline.py` | intent rule → retrieve → generate → gate → retry → fallback (shared by app and eval) |
| `eval_page.py` | golden-set evaluation page |
| `config.py` | reads `st.secrets` / env vars |
| `data/sip.json` | the fictional SIP, plus three journey moments (`scenarios`): first instalment, month 3 (value up), the dip (today) |
| `data/knowledge.md` | plain-language definitions, each with a source line (`{AMFI_LINK}` is filled from secrets) |
| `data/golden_set.csv` | golden questions |
| `tests/` | unit tests for calc, gate and retrieval (`python -m pytest -q`) |

## Run locally

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then paste your Gemini key
python -m pytest -q
streamlit run app.py
```

Get a Gemini API key at <https://aistudio.google.com/apikey>. `.streamlit/secrets.toml` is in `.gitignore`;
never commit it.

## Deploy on Streamlit Community Cloud

1. Push this folder to a GitHub repo (public or private).
2. Go to <https://share.streamlit.io> → **Create app** → pick the repo, branch `main`, main file `app.py`.
3. **Advanced settings → Python 3.11**, and paste the contents of your `secrets.toml` into **Secrets**
   (`GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL`, `AMFI_LINK`, `EVAL_PASSCODE`; optional `SEBI_LINK`).
4. Deploy. The app is public by default (Settings → Sharing → "This app is public"), so viewers need no login.
5. Open the URL on your phone and on a desktop and run the "Try this task" flow once.

To change the model later, edit `GEMINI_MODEL` in the app's Secrets. No code change is needed.

## Golden-set evaluation

Open **Eval results** (top bar), enter the passcode, and press
**Run golden-set eval**. Each row is scored on:

* **gate passed**: the final answer shown passed every gate check
* **must include**: each item found by keyword match *or* judged present by an LLM judge (handles Hinglish
  and paraphrase)
* **must not include**: no item found by keyword *or* by the judge
* **path**: `answer` / `decline` / `uncertain` matches `expected_path`

A row passes only if all four pass. Results are appended to `eval_results.csv` with a timestamp and the model
name. On Streamlit Cloud the disk is wiped on restart, so use **Download eval_results.csv** to keep a run.

### Updating the golden set

Edit `data/golden_set.csv` (Excel / Google Sheets is fine; save as CSV UTF-8):

| column | meaning |
|---|---|
| `id` | G1, G2… |
| `question` | exact wording from your Evidence Log |
| `source` | comment / survey / interview + reference |
| `profile` | `beginner-hinglish` or `basics-english` |
| `must_include` | facts or ideas, separated by `\|`, e.g. `units are still yours\|₹496` |
| `must_not_include` | separated by `\|`; use `—` for none |
| `expected_path` | `answer`, `decline` or `uncertain` |

Commit and push; Streamlit Cloud redeploys automatically. Each eval run costs about 2–4 Gemini calls per row.

## Limits and privacy

* At most 20 questions per browser session (protects the free-tier quota).
* Nothing is stored. Profile, learning and conversation live only in `st.session_state`; learning across
  sessions is planned.
