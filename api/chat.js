import { answerQuestion } from "../lib/answer.js";
import { factsFor, getPortfolio } from "../lib/portfolio.js";

const send = (res, obj) => res.write(`data: ${JSON.stringify(obj)}\n\n`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  // language is the user's explicit toggle choice, or null to follow the question's language.
  const { question, language = null, scenario = "dip", history = [] } = req.body || {};
  if (!question || typeof question !== "string" || question.length > 500) return res.status(422).json({ error: "question required" });

  const facts = factsFor(getPortfolio(scenario === "normal" ? "normal" : "dip", req));
  const result = await answerQuestion({ question, language, history: history.slice(-6), facts });

  // The answer has already passed the gate; stream it word by word so it reads like the original.
  res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-cache, no-transform", Connection: "keep-alive" });
  for (const token of result.answer.match(/\S+\s*/g) || []) {
    send(res, { token });
    await sleep(18);
  }
  send(res, { done: true, source: result.source, path: result.path, topic: result.topic, language: result.language, replaced: result.replaced, fallback_used: result.fallback_used });
  res.end();
}
