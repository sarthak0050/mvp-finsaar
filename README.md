# FinSaar · "Aapke SIP ka saar"

A concept prototype that helps first-time mutual fund investors understand their own SIP numbers when the
value falls below what they invested, in English or Hinglish. Every AI answer passes a visible quality check
(the **eval gate**) or is replaced by a safe fallback. It never gives investment advice or predictions.

> Concept prototype · Not investment advice · Not affiliated with Groww. All data is fictional.

## Where FinSaar shows up

The MVP page looks like a typical investing app's fund page (holdings, SIP details, transactions), with FinSaar
built into it at every moment of the journey:

| Moment | FinSaar nudge | Suggested questions |
|---|---|---|
| ① First instalment | "₹2,000 bought 83.33 units at NAV ₹24.00" | What did my first ₹2,000 buy? · Why is XIRR not shown yet? |
| ② Month 3 · value up | "Your SIP is ₹148 above what you invested" | Why is my value up? · Why did I get fewer units in July? · Should I invest more? |
| ③ The dip · today | "Your SIP is ₹496 below what you invested" | Iska matlab paisa doob gaya? · What does XIRR mean? · Should I stop? |

* **Tap any number** (Returns, XIRR, Units, NAV) → a "FinSaar explains" sheet opens on the spot.
* **In between:** each transaction has a ✦ (Why more units? / Why fewer units?) that explains that instalment.
* **Chat** on the right for anything else. Every path uses the same pipeline and the same gate.

The layout follows common investing-app patterns but uses FinSaar's own styling; it does not copy any real
app's logo or branding.

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
| `app.py` | UI: top bar (How to use → FinSaar MVP → Eval results, no sidebar), SIP on the left, FinSaar panel on the right, profile switch, mentor task, session learning |
| `how_to_use.py` | landing page: how to use, with a Next button into the MVP |
| `calc.py` | all numbers (units, average NAV, value, gain/loss, XIRR via bisection) |
| `rag.py` | parses `knowledge.md`, embeddings + cosine, keyword fallback (cached) |
| `llm.py` | system prompt, Gemini JSON call, model fallback, LLM judge for evals |
| `gate.py` | the eval gate |
| `pipeline.py` | intent rule → retrieve → generate → gate → retry → fallback (shared by app and eval) |
| `eval_page.py` | golden-set evaluation page |
| `config.py` | reads `st.secrets` / env vars |
| `ui_style.py` | phone-frame CSS + banner |
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
   (`GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL`, `AMFI_LINK`, `EVAL_PASSCODE`).
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
