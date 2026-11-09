// Routes a question, drafts an answer with Gemini, runs it through the gate, retries once
// with the gate's feedback, and falls back to the safe reply if it is still blocked.
import { GoogleGenAI } from "@google/genai";
import { detectLanguage, dipSentence, isDip, missingReply, profileFor, route, runGate, safeReply, sourceFor, inr, signedInr, signedPct, xirrText } from "./gate.js";
import { retrieve } from "./retrieve.js";

export const MODEL = process.env.GEMINI_MODEL || "gemini-3.8-flash";
// Tried in order when the main model is overloaded (503), retired (404) or slow.
const BACKUP_MODELS = (process.env.GEMINI_BACKUP_MODELS || "gemini-flash-latest,gemini-flash-lite-latest").split(",").map((m) => m.trim()).filter(Boolean);
const CALL_TIMEOUT_MS = 6000;
// Total time an answer may spend on Gemini before the safe reply is used instead.
const ANSWER_BUDGET_MS = 12000;
export const modelLabel = () => (process.env.GEMINI_API_KEY ? `google/${MODEL}` : "offline safe replies");

let client;
const gemini = () => {
  if (!process.env.GEMINI_API_KEY) return null;
  // Single request per call (no SDK retry wrapper): on overload we switch models instead of waiting on backoff.
  client ||= new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY, httpOptions: { timeout: CALL_TIMEOUT_MS } });
  return client;
};

// Phrases are given only in the reply language, so English answers don't copy Hinglish wording.
const PATH_RULES = {
  answer: () => "Explain the user's own numbers. Do not recommend or predict anything.",
  decline: (hi) =>
    `This asks for a decision. Say ${hi ? "'Main recommend nahi kar sakta (I can't recommend)'" : "you can't recommend"}. Explain neutrally what continue, pause, skip and stop mean for a SIP. Say ${hi ? "'Faisla aapka hai (the decision is yours)'" : "'The decision is yours'"}. Point to a SEBI-registered investment adviser or AMFI investor education. Do not mention XIRR.`,
  uncertain: (hi) =>
    `This asks about the future. Say ${hi ? "'Main predict nahi kar sakta (I can't predict)'" : "you can't predict"}. Then give only one or two of today's known facts, and point to AMFI investor education.`,
  expectations: (hi) =>
    `This is about first-year expectations. Follow this pattern${hi ? " in Hinglish" : ""}: first months' SIP value moves up and down and early swings are common; the user's invested amount, today's value and return %; then the units line exactly as given below; and end with ${hi ? "'Yeh general information hai, forecast nahi (general information, not a forecast).'" : "'This is general information, not a forecast.'"} Never say or imply the value will recover or go up, or that returns will come. Do not mention or judge reels, videos or influencers; just explain the numbers.`,
  simplify: (hi) =>
    `The user did not understand your previous answer. Re-explain the SAME topic more simply: at most 2 short sentences, exactly one everyday comparison (use ${hi ? "'jaise'" : "'like'"}), at most 1 number, and no new terms that weren't in your previous answer. Do not add facts.`,
};

const systemPrompt = ({ path, topic, language, profile, facts: f, previous, retrieved }) => {
  const beginner = profile.startsWith("beginner");
  const lines = [
    "You are FinSaar, an assistant that explains a first-time SIP investor's own mutual fund numbers in plain words.",
    "You are not an adviser. Never give advice, reassurance or predictions (no 'will recover', 'don't worry', 'you should', 'stay invested', 'good time to invest'). No fear or urgency.",
    `The user holds one fund: ${f.fund_name}. You may name it, but never name any other fund or any AMC.`,
    "Use ONLY numbers from the facts below, written exactly as given, with the ₹ and − signs (write the − sign, never the word 'minus'). Do not compute new numbers or invent dates.",
    "Use only the one to three facts that answer this question. Never list or recite the other facts. Keep it to at most 4 short sentences.",
    "Answer only what was asked. Do not bring up XIRR unless asked about returns or XIRR.",
    "If you mention how SIPs usually or have typically behaved, end the answer with 'This is general information, not a forecast.'",
    language === "Hinglish"
      ? "Reply ONLY in Hinglish (Hindi in Roman script, mixed with simple English). Add a short English gloss in brackets for key phrases, e.g. 'units abhi bhi aapke hain (the units are still yours)'."
      : "Reply ONLY in simple English.",
    beginner
      ? "The user is a beginner: at most 80 words, at most 3 numbers, and if you mention NAV explain it in plain words (Hinglish: 'NAV (ek unit ki aaj ki keemat)'; English: 'NAV, the price of one unit'). Avoid jargon: say 'a loss only on paper until you sell' (Hinglish: 'sirf kaagaz par nuksaan, jab tak aap bechte nahi') instead of 'paper loss', 'per year' instead of 'annualised', and 'the average price you paid per unit' instead of 'average buy NAV'."
      : "Keep it under 110 words. If you mention NAV, explain it as the price of one unit.",
    "Plain text only: no markdown, no bullet lists.",
    `Question type: ${path}. ${PATH_RULES[path](language === "Hinglish")}`,
  ];
  if (path === "answer" && topic === "loss" && isDip(f))
    lines.push(`This is about today's dip. Include this sentence exactly as written (its numbers are pre-computed): "${dipSentence(f, language)}" You may add at most one short sentence before it. Do not add other numbers.`);
  if (path === "expectations" && f.units_story)
    lines.push(`Units line (pre-computed from the instalment records; include it exactly as written, do not change its numbers): "${language === "Hinglish" ? f.units_story.hi : f.units_story.en}"`);
  if (path === "simplify") lines.push(`Your previous answer was: "${previous}"`);
  if (retrieved?.docs.length) {
    lines.push(
      "",
      "RETRIEVED FOR THIS QUESTION (the user's records and investor-education definitions). Ground your explanation in these; you may quote instalment dates, NAVs and units from them. If something the user asks about isn't here or in the facts, say you don't have that data.",
      ...retrieved.docs.map((d) => `- [${d.label}] ${d.text}`)
    );
  }
  lines.push(
    "",
    "FACTS (the user's SIP):",
    `- Invested: ${inr(f.invested)}`,
    `- Current value: ${inr(f.current)}`,
    `- Total return: ${signedInr(f.total_return)} (${signedPct(f.total_return_pct)}). A loss is only on paper until units are sold.`,
    `- Units held: ${f.units.toFixed(2)}`,
    `- ${beginner ? "Average price you paid per unit" : "Average buy NAV (average price paid per unit)"}: ₹${f.avg_nav.toFixed(2)}`,
    `- Today's NAV (price of one unit): ₹${f.nav.toFixed(2)}`,
    `- XIRR (return per year that accounts for instalment dates): ${xirrText(f.xirr)}`,
    `- 1-day change: ${signedInr(f.day_change)} (${signedPct(f.day_change_pct)})`,
    `- Monthly SIP: ${inr(f.sip)}, ${f.installments} instalments, next on ${f.next_installment}`
  );
  return lines.join("\n");
};

// Minimal thinking keeps answers fast; models that reject the setting (400) are retried without it.
const callModel = async (ai, model, contents, ctx, msLeft, thinking = true) => {
  try {
    return await ai.models.generateContent({
      model,
      contents,
      config: {
        systemInstruction: systemPrompt(ctx),
        temperature: 0.2,
        maxOutputTokens: 800,
        ...(thinking && { thinkingConfig: { thinkingLevel: "MINIMAL" } }),
        abortSignal: AbortSignal.timeout(Math.max(1000, Math.min(CALL_TIMEOUT_MS, msLeft))),
      },
    });
  } catch (err) {
    if (thinking && err?.status === 400) return callModel(ai, model, contents, ctx, msLeft, false);
    throw err;
  }
};

const draft = async ({ question, history, feedback, deadline, errors, ...ctx }) => {
  const ai = gemini();
  if (!ai) return null;
  const contents = [
    ...(history || []).map((m) => ({ role: m.role === "user" ? "user" : "model", parts: [{ text: m.text }] })),
    { role: "user", parts: [{ text: feedback ? `${question}\n\n(Your previous draft was blocked: ${feedback}. Rewrite it to fix that.)` : question }] },
  ];
  for (const model of [...new Set([MODEL, ...BACKUP_MODELS])]) {
    const msLeft = deadline - Date.now();
    if (msLeft < 1500) break;
    try {
      const res = await callModel(ai, model, contents, ctx, msLeft);
      const text = (res.text || "").replace(/\*\*|__|^#+\s/gm, "").trim();
      if (text) return { text, model };
    } catch (err) {
      errors.push(`${model}:${err?.status || err?.name || "error"}`);
    }
  }
  throw new Error("no answer from Gemini in time");
};

// One structured log line per answer: did the model's answer pass, or was it replaced, and why.
const logAnswer = (entry) => console.log(JSON.stringify({ event: "finsaar_answer", ...entry }));

export const answerQuestion = async ({ question, language, profile: profileOverride, history = [], facts }) => {
  const lang = language === "English" || language === "Hinglish" ? language : detectLanguage(question);
  const profile = profileOverride || profileFor(lang);
  const { path, topic, previous } = route({ question, history, facts });
  const retrieved = retrieve({ question, route: { path, topic }, facts });
  const ctx = { path, topic, language: lang, profile, facts, previous, retrieved };
  // The answer cites what was retrieved for it; a decline keeps its "not investment advice" label.
  const source = path === "decline" || !retrieved.labels.length ? sourceFor(path) : retrieved.labels.join(" · ");
  const base = { path, topic, language: lang, profile, source, retrieved: retrieved.labels };

  // A fund the user doesn't hold, or a request for advice: answer at once with the fixed reply.
  // (Model-written declines were usually blocked and replaced anyway, after up to 20 s.)
  if (path === "missing" || path === "decline") {
    const answer = path === "missing" ? missingReply(facts, lang) : safeReply({ question, ...ctx });
    const gate = runGate({ answer, question, ...ctx });
    logAnswer({ ...base, outcome: "fixed_reply", rules: [] });
    return { ...base, answer, replaced: false, fallback_used: false, model_written: false, gate_checks: gate.checks, blocked: [] };
  }

  const blocked = [];
  const errors = [];
  const deadline = Date.now() + ANSWER_BUDGET_MS;
  let feedback = "";
  let noModel = false;
  for (let attempt = 0; attempt < 2; attempt++) {
    let res;
    try {
      res = await draft({ question, history, feedback, deadline, errors, ...ctx });
    } catch {
      break;
    }
    if (res == null) { noModel = true; break; }
    const gate = runGate({ answer: res.text, question, ...ctx });
    if (gate.passed) {
      logAnswer({ ...base, outcome: "model_passed", model: res.model, attempt: attempt + 1, rules: blocked.map((c) => c.name) });
      return { ...base, answer: res.text, replaced: false, fallback_used: false, model_written: true, gate_checks: gate.checks, blocked };
    }
    blocked.push(...gate.blocked);
    feedback = gate.blocked.map((c) => `${c.name}${c.detail ? ` (${c.detail})` : ""}`).join("; ");
  }

  const answer = safeReply({ question, ...ctx });
  const gate = runGate({ answer, question, ...ctx });
  const outcome = noModel ? "replaced_no_key" : blocked.length ? "replaced_blocked" : "replaced_model_error";
  logAnswer({ ...base, outcome, rules: blocked.map((c) => `${c.name}${c.detail ? ` (${c.detail})` : ""}`), errors });
  return { ...base, answer, replaced: true, fallback_used: true, model_written: false, gate_checks: gate.checks, blocked, errors };
};
