// Retrieval for each question: picks the user's instalment records, fund facts and investor-education
// definitions that are relevant to it, so the answer is built from what was fetched for that question.
import { KNOWLEDGE } from "./knowledge.js";
import { norm, xirrText, inr } from "./gate.js";

const MONTHS = [
  ["jan", "january", "janvari"], ["feb", "february", "farvari"], ["mar", "march"], ["apr", "april"], ["may", "mai"], ["jun", "june", "joon"],
  ["jul", "july", "julai"], ["aug", "august", "agast"], ["sep", "sept", "september", "sitambar"], ["oct", "october", "aktubar"], ["nov", "november", "navambar"], ["dec", "december", "disambar"],
];
const monthOf = (iso) => Number(iso.split("-")[1]) - 1;

// Which instalments the question points at: a month, the first or last, or the most or fewest units.
export const pickInstalments = (question, records) => {
  const q = norm(question);
  const months = MONTHS.map((names, i) => (names.some((n) => new RegExp(`\\b${n}\\b`).test(q)) ? i : -1)).filter((i) => i >= 0);
  if (months.length) return records.filter((r) => months.includes(monthOf(r.iso)));
  if (/(most units|sabse zyada|zyada units|maximum units|lowest nav|sabse kam nav)/.test(q)) return [records.reduce((a, b) => (b.units > a.units ? b : a))];
  if (/(fewest units|least units|sabse kam units|highest nav|sabse zyada nav)/.test(q)) return [records.reduce((a, b) => (b.units < a.units ? b : a))];
  if (/\b(first|pehla|pehli|pahla)\b/.test(q)) return [records[0]];
  if (/\b(last|latest|recent|pichla|pichle|pichhli|aakhri|akhri)\b/.test(q)) return [records[records.length - 1]];
  return [];
};

const line = (r) => `${r.date}: ${inr(r.amount)} bought ${r.units.toFixed(3)} units at a NAV of ₹${r.nav.toFixed(2)}`;

const sipDocs = (question, route, f) => {
  const records = f.instalments || [];
  if (!records.length) {
    return [{ kind: "sip", id: "no-records", label: "Your SIP totals", text: "Instalment-by-instalment records aren't available for this holding, only the totals entered. If asked about a specific instalment, say that data isn't available." }];
  }
  // "first year" in an expectations question isn't about the first instalment.
  const picked = route.path === "expectations" ? [] : pickInstalments(question, records);
  if (picked.length) return [{ kind: "sip", id: `instalments-${picked.map((r) => r.n).join("-")}`, label: picked.length === 1 ? `Your ${picked[0].date} instalment` : "Your instalments", text: `Instalment records: ${picked.map(line).join("; ")}.` }];
  if (!["units", "loss", "avg", "xirr", "holding", "instalment", "nav", "overview", "expectations"].includes(route.topic)) return [];
  const docs = [{ kind: "sip", id: "instalments-all", label: `Your ${records.length} instalments`, text: `All instalments: ${records.map(line).join("; ")}.` }];
  if (route.topic === "xirr" && f.xirr != null)
    docs.push({ kind: "sip", id: "xirr-calc", label: "XIRR from your instalment dates", text: `XIRR ${xirrText(f.xirr)} is calculated in code from these ${records.length} instalment dates and amounts and today's value of ${inr(f.current)}.` });
  return docs;
};

const fundDocs = (question, route, f) => {
  const q = norm(question);
  if (!(route.topic === "nav" || route.topic === "funds" || /\b(risk|riskometer|fund)\b/.test(q))) return [];
  return [{ kind: "fund", id: "fund-facts", label: "Your fund's facts", text: `${f.fund_name} (${f.fund_category}), riskometer: ${f.fund_risk}. NAV today ₹${f.nav.toFixed(2)}; previous day ₹${f.prev_nav.toFixed(2)}.` }];
};

const knowledgeDocs = (question, route) => {
  const q = norm(question);
  const forced = { decline: "sip-options", uncertain: "market-linked", expectations: "market-linked" }[route.path];
  const scored = KNOWLEDGE.map((k) => ({ k, score: (k.topics.includes(route.topic) ? 2 : 0) + k.keywords.filter((w) => q.includes(w)).length + (k.id === forced ? 10 : 0) }))
    .filter((x) => x.score >= 2)
    .sort((a, b) => b.score - a.score)
    .slice(0, 2);
  return scored.map(({ k }) => ({ kind: "knowledge", id: k.id, label: `${k.source.name}: ${k.title}`, text: k.text, url: k.source.url }));
};

export const retrieve = ({ question, route, facts }) => {
  if (route.path === "missing") return { docs: [], labels: [] };
  // A simpler re-explanation needs the concept, not more records.
  const docs = route.path === "simplify"
    ? knowledgeDocs(question, route).slice(0, 1)
    : [...sipDocs(question, route, facts), ...fundDocs(question, route, facts), ...knowledgeDocs(question, route)];
  return { docs, labels: docs.map((d) => d.label) };
};
