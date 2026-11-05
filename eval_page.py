"""Golden-set evaluation: runs every golden question through the full pipeline (gate included)."""
from __future__ import annotations

import csv
import io
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

import config
import llm
import pipeline

ROOT = Path(__file__).parent
GOLDEN = ROOT / "data" / "golden_set.csv"
RESULTS = ROOT / "eval_results.csv"
EMPTY = {"", "—", "-", "–", "none", "n/a"}


def split_items(cell: str) -> list[str]:
    return [x.strip() for x in str(cell or "").split("|") if x.strip() and x.strip().lower() not in EMPTY]


def norm(t: str) -> str:
    t = t.lower().replace("’", "'").replace("−", "-").replace("–", "-")
    t = re.sub(r"₹\s+", "₹", t)
    t = re.sub(r"(?<=\d),(?=\d)", "", t)
    t = t.replace("cannot", "can't").replace("can not", "can't")
    return re.sub(r"\s+", " ", t)


def keyword_hit(answer: str, item: str) -> bool:
    return norm(item) in norm(answer)


def load_golden() -> list[dict]:
    with open(GOLDEN, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def score_row(row: dict, model: str) -> dict:
    profile = pipeline.default_profile(row["profile"])
    r = pipeline.answer(row["question"], profile)
    inc, exc = split_items(row["must_include"]), split_items(row["must_not_include"])
    kw_inc = [keyword_hit(r.answer, i) for i in inc]
    kw_exc = [keyword_hit(r.answer, i) for i in exc]
    judge_note = ""
    try:
        j = llm.judge(row["question"], r.answer, inc, exc) if (inc or exc) else {"include": [], "exclude": []}
    except llm.LLMError as e:
        j = {"include": [False] * len(inc), "exclude": [False] * len(exc)}
        judge_note = f"judge unavailable ({str(e)[:60]}); keyword check only"
    inc_ok_each = [k or jj for k, jj in zip(kw_inc, j["include"])]
    exc_bad_each = [k or jj for k, jj in zip(kw_exc, j["exclude"])]
    missing = [i for i, ok in zip(inc, inc_ok_each) if not ok]
    present = [i for i, bad in zip(exc, exc_bad_each) if bad]
    path_ok = r.path == row["expected_path"].strip()
    reasons = []
    if not r.gate_passed:
        reasons.append("gate: " + "; ".join(r.gate.reasons if r.gate else ["no gate result"]))
    if missing:
        reasons.append("missing: " + ", ".join(missing))
    if present:
        reasons.append("should not include: " + ", ".join(present))
    if not path_ok:
        reasons.append(f"path {r.path} (expected {row['expected_path']})")
    if r.kind == "fallback-error":
        reasons.append("AI unavailable: " + r.error[:80])
    if judge_note:
        reasons.append(judge_note)
    return {
        "run_at": "", "model": model, "id": row["id"], "question": row["question"], "profile": row["profile"],
        "expected_path": row["expected_path"], "got_path": r.path, "kind": r.kind,
        "gate_passed": r.gate_passed, "must_include_ok": not missing, "must_not_include_ok": not present,
        "path_ok": path_ok,
        "passed": bool(r.gate_passed and not missing and not present and path_ok),
        "reasons": " | ".join(reasons), "answer": r.answer, "source": row.get("source", ""),
    }


def save(rows: list[dict]):
    new = not RESULTS.exists()
    with open(RESULTS, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        if new:
            w.writeheader()
        w.writerows(rows)


def latest_run() -> pd.DataFrame | None:
    if not RESULTS.exists():
        return None
    df = pd.read_csv(RESULTS)
    return df[df["run_at"] == df["run_at"].max()] if len(df) else None


def show(df: pd.DataFrame):
    n, ok = len(df), int(df["passed"].astype(bool).sum())
    st.metric("Overall pass rate", f"{ok} of {n} passed", f"{ok / n:.0%}" if n else None, delta_color="off")
    st.caption(f"Run at {df['run_at'].iloc[0]} · model {df['model'].iloc[0]}")
    tick = lambda v: "✅" if bool(v) else "❌"
    view = pd.DataFrame({
        "id": df["id"], "question": df["question"], "profile": df["profile"],
        "path (exp → got)": df["expected_path"] + " → " + df["got_path"],
        "gate": df["gate_passed"].map(tick), "must include": df["must_include_ok"].map(tick),
        "must not include": df["must_not_include_ok"].map(tick), "path": df["path_ok"].map(tick),
        "PASS": df["passed"].map(tick),
    })
    st.dataframe(view, hide_index=True, width="stretch")
    fails = df[~df["passed"].astype(bool)]
    st.subheader("Failures")
    if fails.empty:
        st.success("No failures in this run.")
    for _, f in fails.iterrows():
        st.markdown(f"**{f['id']}** · {f['question']}  \n{f['reasons']}")
    with st.expander("All answers"):
        for _, f in df.iterrows():
            st.markdown(f"**{f['id']}** ({f['profile']}, {f['kind']}): {f['answer']}")
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button("Download eval_results.csv (this run)", buf.getvalue(), file_name="eval_results.csv",
                       mime="text/csv")


def page():
    st.markdown("<style>.block-container{max-width:1100px !important;}</style>", unsafe_allow_html=True)
    st.title("Golden-set evaluation")
    golden = load_golden()
    st.write(f"{len(golden)} golden questions from `data/golden_set.csv`. Each runs through the full FinSaar "
             "pipeline (intent rule → retrieval → Gemini → gate → retry/fallback) and is scored on: gate passed, "
             "must-include covered (keyword check + LLM judge), must-not-include absent, correct path.")
    with st.expander("Golden set"):
        st.dataframe(pd.DataFrame(golden), hide_index=True, width="stretch")

    passcode = config.get("EVAL_PASSCODE")
    allowed = True
    if passcode:
        entered = st.text_input("Passcode to run the eval (protects the shared API quota)", type="password")
        allowed = entered == passcode
    if st.button("Run golden-set eval", type="primary", disabled=not allowed):
        model = config.model_name()
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        rows, bar = [], st.progress(0.0, text="Starting…")
        for n, row in enumerate(golden):
            bar.progress(n / len(golden), text=f"{row['id']}: {row['question']}")
            try:
                res = score_row(row, model)
            except Exception as e:  # never crash the page
                res = {"run_at": "", "model": model, "id": row["id"], "question": row["question"],
                       "profile": row["profile"], "expected_path": row["expected_path"], "got_path": "error",
                       "kind": "error", "gate_passed": False, "must_include_ok": False,
                       "must_not_include_ok": False, "path_ok": False, "passed": False,
                       "reasons": f"error: {type(e).__name__}", "answer": "", "source": row.get("source", "")}
            res["run_at"] = stamp
            rows.append(res)
            time.sleep(1.0)  # be gentle with free-tier rate limits
        bar.progress(1.0, text="Done")
        save(rows)
        st.session_state.eval_df = pd.DataFrame(rows)

    df = st.session_state.get("eval_df")
    if df is None:
        df = latest_run()
    if df is not None and len(df):
        show(df)
    else:
        st.info("No results yet. Press **Run golden-set eval**.")


page()
