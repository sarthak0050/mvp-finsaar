# FinSaar: explaining a first-time SIP investor's own numbers

FinSaar is a prototype assistant inside a mutual fund app. It explains a new investor's SIP in plain English or Hinglish, using their own numbers, especially on days when the value is below what they put in.

**Live MVP:** https://groww-mf-finsaar.vercel.app

> Prototype for a case study. All funds and figures are sample data. FinSaar is educational only: it gives no investment advice, names no real funds or fund houses, and makes no predictions.

## The problem

Interviews with SIP investors showed that most judge their SIP only by red or green, don't understand terms like NAV and XIRR, and learn them from YouTube or Google. Many nearly stopped, or did stop, during their first fall. What kept them invested was rarely the app itself. FinSaar puts the explanation inside the app, at the moment it's needed.

## What it does

- **Dip card, led by units.** When today's value is under the amount invested, or NAV moves 1% or more in a day, the dashboard shows "Your dip, in units". For example: "This month your ₹2,000 bought 87 units. At last month's price, it would have bought 84. You now own 412.15 units; none were lost." Every number is computed in code from the instalment records.
- **"What changed, and what didn't".** A four-step sheet covering today's NAV against your average price paid, the units you still own, what the value means, and your options.
- **Chat in English or Hinglish.** Replies follow the language of the question unless one is picked on the toggle. Users can ask for a simpler explanation ("explain simpler", "aur simple batao").
- **Answer types:**

  | Type | Example question |
  |---|---|
  | Explain | "Iska matlab paisa doob gaya?" |
  | Decline advice | "Should I stop my SIP?" (fixed reply: the options exist, the decision is yours) |
  | Can't predict | "Will my SIP recover by next month?" |
  | Fund not held | "How is my HDFC fund doing?" |
  | Simplify | "explain simpler" |
  | First-year expectations | "Reels said SIP gives good returns, why not mine?" |

- **Source labels.** Each answer shows what it was based on, e.g. "Your 5 instalments · AMFI investor education: What NAV means".
- **Quality page.** Runs the golden test set against the live model and shows pass rates, progress and each row's retrieved sources.

## How an answer is made

```
question ─► route (answer / decline / uncertain / missing / simplify / expectations)
         ─► retrieve (instalment records, fund facts, investor-education entries)
         ─► Gemini drafts a reply, given only the user's facts and retrieved text
         ─► quality gate checks the draft ─► passes: stream it
                                          └► fails: one rewrite, then a safe reply
```

- **Retrieval (RAG).**
  - Each question pulls the relevant instalment records, e.g. "How many units did my November instalment buy?".
  - It also pulls the fund's facts and up to two entries from a small knowledge base, written in our own words with links to AMFI and SEBI investor education.
- **Numbers come from code.** Units, average price, value and XIRR are computed from the instalment records. XIRR is calculated by bisection on the instalment dates.
- **The quality gate** (`lib/gate.js`) blocks any draft that:
  - gives advice, reassurance or a prediction ("will recover", "stay invested", "returns will come");
  - names another fund or fund house;
  - uses a number that isn't in the user's data;
  - replies in the wrong language;
  - is too long or has too many numbers for a beginner;
  - leaves NAV or other jargon unexplained;
  - mentions typical or past behaviour without ending "…not a forecast";
  - in an expectations answer, mentions reels or videos.
- **Fixed replies.** Requests for advice and questions about funds not held get fixed text at once, with no model call.
- **Fallbacks.** When Gemini is slow, overloaded or rate-limited, the backup models are tried. After 12 seconds a safe reply is used.

## Golden test set

`lib/goldens.json` holds 28 cases from the brief, usability tests and interviews. Each case lists the expected answer type, the expected language, words that must appear and words that must not. Synonyms are accepted, so "per year" also matches "a year" or "annual". The latest live run passed 28/28; 25 of those passed with the model's own answer, without replacement.

## Project layout

```
src/                     React front end (Vite)
  App.jsx                pages, navigation, explainer sheets
  components/finsaar/    Dashboard, DipCard, Chat, QualityPage
  lib/sampleData.js      offline fallback data
api/                     Vercel serverless functions
  chat.js                streams an answer (server-sent events)
  portfolio.js           portfolio and summary
  holdings.js            saves a holding the user adds (cookie)
  evals/run.js           runs the golden set
  evals/latest.js        latest saved run
lib/                     shared logic
  answer.js              prompt, Gemini calls, fallbacks
  gate.js                routing, quality gate, safe replies
  retrieve.js            retrieval for each question
  knowledge.js           investor-education knowledge base
  sipData.js             instalment records, XIRR
  unitsStory.js          the units line
  portfolio.js           funds, holdings, facts for the model
  keywords.js            keyword synonyms for the golden set
  evalStore.js           saves the latest run to Vercel Blob
  goldens.json           the golden test cases
```

## Run it locally

Requires Node 18 or later.

```bash
npm install
cp .env.example .env.local   # then add your GEMINI_API_KEY
npm run dev                  # http://localhost:5173
```

The dev server also runs the `api/` functions. Without a Gemini key, the chat still works using the built-in safe replies.

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (required for model-written answers) |
| `GEMINI_MODEL` | Main model, default `gemini-3.8-flash` |
| `GEMINI_BACKUP_MODELS` | Comma-separated backups, default `gemini-flash-latest,gemini-flash-lite-latest` |
| `BLOB_READ_WRITE_TOKEN` | Vercel Blob token, used to save golden-set runs |

## Deploy

Deploy to Vercel (`vercel deploy --prod`), and set the variables above in the project's settings. Golden-set runs use the live model, so they only run on a deployed copy that has the key.

## Tech

React 18 and Vite, Tailwind (base styles), Vercel serverless functions, Google Gemini (`@google/genai`) and Vercel Blob.
