import goldens from "../../lib/goldens.json" with { type: "json" };
import { answerQuestion, modelLabel } from "../../lib/answer.js";
import { saveLatestRun } from "../../lib/evalStore.js";
import { norm } from "../../lib/gate.js";
import { findKeyword } from "../../lib/keywords.js";
import { factsFor, getPortfolio } from "../../lib/portfolio.js";

const ROW_PAUSE_MS = 6000;
// Stop before Vercel's 300 s function limit so the run ends cleanly instead of being cut off.
const RUN_BUDGET_MS = 280000;
const send = (res, obj) => res.write(`data: ${JSON.stringify(obj)}\n\n`);

const scoreRow = async (g, facts) => {
  // g.toggle is an explicit language choice; without it the reply language follows the question.
  const r = await answerQuestion({ question: g.question, language: g.toggle || null, profile: g.profile, history: g.history || [], facts });
  const a = norm(r.answer);
  const gatePassed = r.gate_checks.every((c) => c.passed);
  const fundCheck = r.gate_checks.find((c) => c.name.startsWith("No fund or AMC names"));
  const include = g.must_include.map((item) => {
    const matched = findKeyword(r.answer, item);
    return { item, keyword: Boolean(matched), matched, passed: Boolean(matched) };
  });
  const exclude = g.must_not_include.map((item) => {
    const hit = item === "any fund name" ? !fundCheck.passed : a.includes(norm(item));
    return { item, keyword: hit, passed: !hit };
  });
  const checks = {
    gate: gatePassed,
    must_include: include.every((x) => x.passed),
    must_not_include: exclude.every((x) => x.passed),
    path: r.path === g.expected_path,
    language: r.language === g.language,
  };
  const reasons = [
    !checks.gate && `Gate failed: ${r.gate_checks.filter((c) => !c.passed).map((c) => c.name).join(", ")}`,
    ...include.filter((x) => !x.passed).map((x) => `Missing "${x.item}"`),
    ...exclude.filter((x) => !x.passed).map((x) => `Contains "${x.item}"`),
    !checks.path && `Expected ${g.expected_path}, got ${r.path}`,
    !checks.language && `Replied in ${r.language}, expected ${g.language}`,
  ].filter(Boolean);
  return { ...g, answer: r.answer, path: r.path, retrieved: r.retrieved || [], reply_language: r.language, replaced: r.replaced, model_written: r.model_written, fallback_used: r.fallback_used, errors: r.errors || [], gate_checks: r.gate_checks, blocked: r.blocked, include, exclude, checks, reasons, passed: reasons.length === 0 };
};

// A row replaced only because Gemini couldn't answer means the run is measuring the outage, not the app.
const outageReason = (row) => {
  if (!row.replaced || row.blocked.length || !row.errors.length) return null;
  if (row.errors.every((e) => e.endsWith(":429"))) return "Gemini quota or rate limit reached (429)";
  return `Gemini unavailable (${[...new Set(row.errors.map((e) => e.split(":").pop()))].join(", ")})`;
};

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  const facts = factsFor(getPortfolio("dip", req));
  const live = Boolean(process.env.GEMINI_API_KEY);
  const startedAt = Date.now();
  const run = {
    id: Math.random().toString(16).slice(2) + startedAt.toString(16),
    status: "running",
    model: modelLabel(),
    started_at: new Date(startedAt).toISOString(),
    golden_version: "default",
    total: goldens.length,
    completed: 0,
    passed: 0,
    // Rows that passed with the model's own answer (or a by-design fixed reply), not a safe-reply replacement.
    passed_without_replacement: 0,
    results: [],
  };
  res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-cache, no-transform", Connection: "keep-alive" });
  send(res, { run: { ...run, results: undefined } });

  // One row at a time, with a pause between rows, stays inside Gemini free-tier per-minute limits.
  // (Parallel batches were tried and hit 429s on the free tier, so rows stay sequential.)
  try {
    for (const [i, g] of goldens.entries()) {
      if (Date.now() - startedAt > RUN_BUDGET_MS) { run.status = "stopped"; run.stop_reason = "time limit reached"; break; }
      const row = await scoreRow(g, facts);
      const outage = live && outageReason(row);
      if (outage) { run.status = "stopped"; run.stop_reason = outage; break; }
      run.results.push(row);
      run.completed += 1;
      run.passed += row.passed ? 1 : 0;
      run.passed_without_replacement += row.passed && !row.replaced ? 1 : 0;
      send(res, { progress: { completed: run.completed, passed: run.passed } });
      // Fixed replies (declines, funds not held) make no Gemini call, so they need no pause.
      const calledGemini = row.model_written || row.replaced;
      if (live && calledGemini && i < goldens.length - 1) await new Promise((r) => setTimeout(r, ROW_PAUSE_MS));
    }
    if (run.status === "running") run.status = "done";
  } catch (err) {
    console.error("eval run failed", err);
    run.status = "stopped";
    run.stop_reason = err?.message || "unexpected error";
  }
  run.finished_at = new Date().toISOString();

  // Only a complete run on the real model replaces the saved result; stopped or offline runs never do.
  let saved = false;
  if (run.status === "done" && live) {
    try { saved = await saveLatestRun(run); } catch (err) { console.error("save latest run failed", err?.message || err); }
  }
  send(res, { done: true, run, saved });
  res.end();
}
