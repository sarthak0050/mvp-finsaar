import { useEffect, useRef, useState } from "react";
import { CheckCircle2, ChevronDown, Play, ShieldCheck, XCircle } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
// Rows that passed on the AI's own answer (or a by-design fixed reply), not on a safe-reply replacement.
const withoutReplacement = (run) => run.passed_without_replacement ?? run.results.filter((r) => r.passed && !(r.replaced ?? r.fallback_used)).length;
const when = (iso) => (iso ? new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : "");

const ResultRow = ({ r }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className={`eval-row ${r.passed ? "pass" : "fail"}`} data-testid={`eval-row-${r.id}`}>
      <button className="eval-row-head" data-testid={`eval-row-toggle-${r.id}`} onClick={() => setOpen(!open)}>
        {r.passed ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
        <b>{r.id}</b>
        <span className="eval-q">{r.question}</span>
        <em>{r.expected_path} → {r.path}</em>
        <ChevronDown size={15} className={open ? "flip" : ""} />
      </button>
      {!r.passed && <ul className="eval-reasons" data-testid={`eval-reasons-${r.id}`}>{r.reasons.map((x) => <li key={x}>{x}</li>)}</ul>}
      {open && (
        <div className="eval-detail">
          <p className="eval-meta">{r.profile} · {r.source}{r.reply_language ? ` · replied in ${r.reply_language}` : ""}{(r.replaced ?? r.fallback_used) ? " · replaced by safe reply" : r.model_written === false ? " · fixed reply by design" : " · AI answer"}</p>
          {r.retrieved?.length > 0 && <p className="eval-meta" data-testid={`eval-retrieved-${r.id}`}>Retrieved: {r.retrieved.join(" · ")}</p>}
          <p className="eval-answer">{r.answer}</p>
          <div className="eval-checks">
            {Object.entries(r.checks).map(([k, v]) => <span key={k} className={v ? "ok" : "bad"}>{k.replaceAll("_", " ")}</span>)}
          </div>
          {r.blocked?.length > 0 && <p className="eval-meta">Gate blocked the first draft: {r.blocked.map((c) => `${c.name}${c.detail ? ` (${c.detail})` : ""}`).join("; ")}</p>}
        </div>
      )}
    </div>
  );
};

// Runs completed in this browser (newest first), for the "Past runs" list. The latest completed run
// on the server is the one every visitor sees.
const RUNS_KEY = "finsaar-eval-runs";
const loadRuns = () => { try { return JSON.parse(localStorage.getItem(RUNS_KEY)) || []; } catch { return []; } };
const saveRuns = (list) => { try { localStorage.setItem(RUNS_KEY, JSON.stringify(list.slice(0, 10))); } catch { /* storage full or blocked */ } };

const timeLeft = (live) => {
  if (!live.completed) return "about 4 min left";
  const perRow = (Date.now() - live.startedAt) / live.completed;
  const min = (perRow * (live.total - live.completed)) / 60000;
  return min < 1 ? "less than a minute left" : `about ${Math.ceil(min)} min left`;
};

const RunResults = ({ run }) => {
  const failures = run.results.filter((r) => !r.passed);
  return (
    <>
      <div className="section-head"><h2>Failures <span className="count">{failures.length}</span></h2></div>
      {failures.length === 0 && <p className="subline" data-testid="eval-no-failures">Every row passed every check.</p>}
      {failures.map((r) => <ResultRow key={r.id} r={r} />)}
      <div className="section-head"><h2>All rows</h2></div>
      {run.results.filter((r) => r.passed).map((r) => <ResultRow key={r.id} r={r} />)}
    </>
  );
};

export const QualityPage = () => {
  const [runs, setRuns] = useState(loadRuns);
  const [latest, setLatest] = useState(() => loadRuns()[0] || null);
  const [live, setLive] = useState(null);
  const [stopped, setStopped] = useState(null);
  const [error, setError] = useState(false);
  const [, tick] = useState(0);
  const abort = useRef(null);
  const total = runs.length;
  const loadRun = (id) => setLatest(runs.find((r) => r.id === id) || latest);

  // Show the saved run straight away; every visitor gets the same one from the server.
  useEffect(() => {
    fetch(`${API}/evals/latest`).then((r) => (r.ok ? r.json() : null)).then((d) => { if (d?.run) setLatest(d.run); }).catch(() => {});
    return () => abort.current?.abort();
  }, []);
  // Re-render every few seconds while running so the time estimate stays current.
  useEffect(() => { if (!live) return undefined; const t = setInterval(() => tick((n) => n + 1), 5000); return () => clearInterval(t); }, [live]);

  const start = async () => {
    setError(false); setStopped(null);
    const ctrl = new AbortController();
    abort.current = ctrl;
    let progress = { completed: 0, total: latest?.total || 22 };
    setLive({ ...progress, startedAt: Date.now() });
    try {
      const res = await fetch(`${API}/evals/run`, { method: "POST", signal: ctrl.signal });
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buf = "", finished = null;
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop();
        for (const p of parts) {
          if (!p.startsWith("data: ")) continue;
          const ev = JSON.parse(p.slice(6));
          if (ev.run && !ev.done) { progress = { completed: 0, total: ev.run.total }; setLive((l) => ({ ...l, ...progress })); }
          if (ev.progress) { progress = { ...progress, ...ev.progress }; setLive((l) => ({ ...l, ...ev.progress })); }
          if (ev.done) finished = ev.run;
        }
      }
      if (!finished) throw new Error("connection ended before the run finished (time limit)");
      if (finished.status !== "done") {
        setStopped({ at: finished.completed, total: finished.total, reason: finished.stop_reason || finished.status });
      } else {
        setLatest(finished);
        setRuns((prev) => { const next = [finished, ...prev]; saveRuns(next); return next.slice(0, 10); });
      }
    } catch (e) {
      if (e.name !== "AbortError") setStopped({ at: progress.completed, total: progress.total, reason: e.message || "connection lost" });
    } finally {
      setLive(null);
    }
  };
  const running = Boolean(live);
  const shown = latest?.results?.length ? latest : null;

  return (
    <section className="page reveal" data-testid="quality-page">
      <div className="page-heading"><div><p className="eyebrow">ANSWER QUALITY</p><h1>How FinSaar checks itself</h1><p className="subline">Every answer passes a quality gate before you see it. This page scores that gate against a golden set.</p></div><ShieldCheck size={22} className="heading-icon" /></div>
      <div className="gate-explainer">
        <b>The gate blocks any answer that:</b>
        <ul><li>gives advice, reassurance or predictions</li><li>names a fund or AMC other than the one you hold</li><li>uses a number not in your data, or another fund’s numbers when you ask about a fund you don’t hold</li><li>doesn’t fit the question type (answer, decline, uncertain, fund not held, or a simpler re-explanation)</li><li>isn’t in your question’s language (or the language you picked), or adds things you didn’t ask (like XIRR)</li><li>for beginners: runs over 80 words, uses more than 3 numbers, skips a plain-words NAV explanation, or uses jargon like “paper loss” without explaining it</li><li>on a dip, doesn’t connect today’s NAV to the average price you paid</li></ul>
        <span>Blocked answers are replaced with a safe reply that states the facts, says what FinSaar can't do, and points to AMFI or SEBI.</span>
      </div>
      <div className="eval-score" data-testid="eval-score-card">
        {running ? (
          <div className="eval-progress-wrap">
            <span>Running…</span>
            <strong data-testid="eval-score">{live.completed} of {live.total} checked</strong>
            <div className="eval-progress" role="progressbar" aria-valuemin={0} aria-valuemax={live.total} aria-valuenow={live.completed}><i style={{ width: `${(live.completed / live.total) * 100}%` }} /></div>
            <small data-testid="eval-progress-text">{live.completed} of {live.total} checked · {timeLeft(live)}</small>
          </div>
        ) : (
          <div>
            <span>{shown ? "Latest run" : "No runs yet"}</span>
            <strong data-testid="eval-score">{shown ? `${shown.passed} of ${shown.total} passed` : "—"}</strong>
            {shown && <em className="eval-ai-score" data-testid="eval-ai-score">{withoutReplacement(shown)} of {shown.total} passed without replacement ({Math.round((withoutReplacement(shown) / shown.total) * 100)}%)</em>}
            {shown && <small data-testid="eval-run-meta">{shown.model} · {when(shown.finished_at || shown.started_at)}</small>}
          </div>
        )}
        <button className="primary-button" data-testid="run-eval-button" onClick={start} disabled={running}><Play size={15} /> {running ? "Running…" : "Re-run golden set (takes ~4 min)"}</button>
      </div>
      {stopped && <p className="form-error" role="alert" data-testid="eval-stopped">Run stopped at {stopped.at} of {stopped.total}: {stopped.reason}. The last completed run is still shown.</p>}
      {error && <p className="form-error" role="alert" data-testid="eval-error">Couldn’t reach the eval service. Please try again.</p>}
      {shown && running && (
        <div className="section-head" data-testid="eval-last-completed"><h2>Last completed run</h2><span>{shown.passed} of {shown.total} passed · {shown.model} · {when(shown.finished_at)}</span></div>
      )}
      {shown && <RunResults run={shown} />}
      {runs.length > 1 && (
        <>
          <div className="section-head"><h2>Past runs</h2></div>
          <div className="eval-history">{runs.map((x, i) => <button key={x.id} data-testid={`eval-history-${x.id}`} className={latest?.id === x.id ? "active" : ""} onClick={() => loadRun(x.id)}><span>Run {total - i}</span><b>{x.status === "done" ? `${x.passed}/${x.total}` : x.status}</b></button>)}</div>
        </>
      )}
      <div className="why-ai" data-testid="why-ai-card">
        <b>Where AI earns its place</b>
        <p>A first-time SIP investor who sees a dip asks things in their own words, often in Hinglish (“Iska matlab paisa doob gaya?”). AI turns that worry into an explanation built on their own units, NAV and XIRR. A non-AI version can only show fixed FAQ cards. It can't answer follow-ups or mixed-language questions, and it can't link a general concept to the person's own numbers.</p>
        <p>The gate exists because a fluent model can still slip into advice or comfort-predictions (“it will recover”). FinSaar is not investment advice.</p>
      </div>
    </section>
  );
};
