import { pickInstalments } from "./retrieve.js";
import { unitsStory } from "./unitsStory.js";

// The answer quality gate: language detection, question routing, the checks every
// draft must pass, and the safe replies used when a draft is blocked or no model answers.

const MINUS = /[−–—-]/g;
export const norm = (s) =>
  String(s || "")
    .toLowerCase()
    .replace(/[‘’]/g, "'")
    .replace(MINUS, "-")
    .replace(/cannot|can not/g, "can't")
    .replace(/\s+/g, " ");

export const inr = (n) => `₹${Math.abs(Math.round(n)).toLocaleString("en-IN")}`;
export const signedInr = (n) => `${n < 0 ? "−" : "+"}${inr(n)}`;
export const signedPct = (n) => `${n < 0 ? "−" : "+"}${Math.abs(n).toFixed(2)}%`;
export const xirrText = (n) => (n == null ? "not available" : `${n < 0 ? "−" : ""}${Math.abs(n)}%`);

// ---------- Language ----------
const HINGLISH_MARKERS = new Set(
  ("hai hain hoon ho hota hoti hote kya kyun kyu kaise kitna kitne kitni mera mere meri mujhe aap aapka aapke aapki " +
    "iska iski uska uski matlab paisa paise doob dooba gaya gayi hua hui karu karun karna karo du dun batao samjhao " +
    "samajh samjha samjhe nahi nahin aur sirf jab toh bhi wapas upar neeche kam zyada badh badha abhi raha rahi rahe " +
    "chahiye mein ko ka ki ke ek yeh woh wala wali jayega jaayega hoga bech becho isliye kyunki lekin dikh dikhta " +
    "keemat daam saare saara milte milta jaise jaisa").split(" ")
);
const markerCount = (text) => norm(text).split(/[^a-z']+/).filter((w) => HINGLISH_MARKERS.has(w)).length;

export const detectLanguage = (question) => {
  if (/[ऀ-ॿ]/.test(question)) return "Hinglish";
  const words = norm(question).split(/[^a-z']+/).filter(Boolean).length;
  const hits = markerCount(question);
  return hits >= 2 || (hits === 1 && words <= 4) ? "Hinglish" : "English";
};

export const profileFor = (language) => (language === "Hinglish" ? "beginner-hinglish" : "basics-english");
const isBeginner = (profile) => profile.startsWith("beginner");

// ---------- Routing ----------
const DECLINE = /\b(should i|should we|stop|switch|sell|redeem|withdraw|bech|band kar|band karu|pause|skip|put more|invest more|buy more|add more|better fund|which fund|move to|recommend|kya karu|kya karun|continue karu|nikal)/;
const UNCERTAIN = /\b(will|next (year|month|week)|recover|predict|future|jayega|jaayega|hoga|badhega|girega|forecast|worth .* (later|next)|kitna ho)/;
// First-year expectations: "reels said SIP gives good returns, why not mine?", "why am I in loss in my first year?".
const EXPECTATIONS = /(\b(reels?|youtube|insta|instagram|influencers?|finfluencers?|videos?)\b|first (year|few months|months)|pehle saal|pehla saal|shuru ke mahin|why not (mine|me)|not (getting|seeing) (any |good )?returns?|returns? kyun nahi|returns? nahi (aa|mil)|kyun nahi (aa|mil) raha|expected (more|better|good)|i thought (i'?d|it would))/;
const SWITCHING = /\b(switch|move to|shift|better fund|which fund|instead)/;
const SIMPLIFY = /(simpl|more simply|samajh nahi|samjha nahi|samjh nahi|nahi samjha|nahi samjhe|didn'?t (get|understand)|don'?t (get|understand)|not clear|explain (it |that )?again|again\??$|phir se|dobara|example do|ek example|an example|give (me )?(an )?example|easier|easy words|aasan)/;

const AMCS = [
  "sbi", "hdfc", "icici", "axis", "nippon", "kotak", "parag parikh", "ppfas", "mirae", "uti", "aditya birla", "birla",
  "tata", "dsp", "quant", "motilal", "franklin", "edelweiss", "canara robeco", "bandhan", "invesco", "sundaram", "hsbc", "pgim",
];
const FUND_TERMS = [
  "index fund", "index", "nifty", "sensex", "nasdaq", "s&p", "small cap", "smallcap", "mid cap", "midcap", "large cap",
  "largecap", "bluechip", "blue chip", "elss", "tax saver", "debt fund", "liquid fund", "gold fund", "gold etf", "etf",
  "hybrid", "balanced", "international fund", "value fund", "contra", "focused fund", "multi cap", "multicap", "flexi cap", "flexicap",
];
const SAMPLE_FUND_NAMES = ["sample flexi cap fund", "sample bluechip fund", "sample balanced advantage", "sample small cap fund"];
const wordRe = (w) => new RegExp(`(^|[^a-z])${w.replace(/[&]/g, "\\$&")}([^a-z]|$)`);

// A fund, AMC or index the question names that the user does not hold.
export const unheldFundIn = (question, facts) => {
  const q = norm(question);
  const held = norm(`${facts.fund_name} ${facts.fund_category}`);
  const amc = AMCS.find((a) => wordRe(a).test(q));
  if (amc) return amc;
  return FUND_TERMS.find((t) => wordRe(t).test(q) && !held.includes(t)) || null;
};

const TOPIC_KEYWORDS = {
  xirr: /xirr/,
  units: /units?/,
  holding: /units?|value/,
  loss: /units?|loss|nuksaan|paisa/,
  avg: /average|price|daam/,
  nav: /nav|price|keemat|daam/,
  options: /pause|skip|stop|decision|faisla/,
  future: /predict|tomorrow|kal|future/,
  funds: /fund/,
  overview: /./,
};

// A question about particular instalments: a month, an instalment, or which one bought the most or fewest units.
const INSTALMENT_REF = /\b(instalment|installment|kisht|jan(uary)?|feb(ruary)?|march|april|june|july|aug(ust)?|sept?(ember)?|oct(ober)?|nov(ember)?|dec(ember)?|most units|fewest units|least units|sabse zyada|sabse kam)\b/;

export const topicOf = (text) => {
  const q = norm(text);
  if (/xirr/.test(q)) return "xirr";
  if (/(units?.*(up|badh)|value.*(down|kam|gir))/.test(q)) return "units";
  if (INSTALMENT_REF.test(q)) return "instalment";
  if (/(average|avg)/.test(q)) return "avg";
  if (/\bnav\b/.test(q)) return "nav";
  if (/(doob|lost|loss|gone|gaya)/.test(q)) return "loss";
  if (/(units?|value|kitne|worth)/.test(q)) return "holding";
  return null;
};

const baseRoute = (question) => {
  const q = norm(question);
  if (DECLINE.test(q)) return { path: "decline", topic: "options" };
  if (EXPECTATIONS.test(q)) return { path: "expectations", topic: "expectations" };
  if (UNCERTAIN.test(q)) return { path: "uncertain", topic: "future" };
  return { path: "answer", topic: topicOf(question) || "overview" };
};

// What a "simpler" request refers to: walk back over earlier "simpler" requests to the answer they
// started from, and use the question it answered (or the answer itself if that question was general,
// or if it was an explainer opened from the dashboard with no question before it).
const topicBeingSimplified = (history) => {
  for (let i = history.length - 1; i >= 0; i--) {
    if (history[i].role === "user") continue;
    const asked = history[i - 1];
    if (asked?.role === "user" && SIMPLIFY.test(norm(asked.text))) { i--; continue; }
    const fromQuestion = asked?.role === "user" ? baseRoute(asked.text).topic : null;
    if (fromQuestion && fromQuestion !== "overview") return fromQuestion;
    return topicOf(history[i].text) || "overview";
  }
  return "overview";
};

// Decides how to answer: simplify the previous answer, say the fund isn't held, decline, admit uncertainty, or answer.
export const route = ({ question, history = [], facts }) => {
  const prevAnswer = [...history].reverse().find((m) => m.role !== "user");
  const q = norm(question);
  if (prevAnswer && SIMPLIFY.test(q)) {
    const prevTopic = topicBeingSimplified(history);
    const ownTopic = topicOf(question);
    if (!ownTopic || ownTopic === prevTopic) return { path: "simplify", topic: prevTopic, previous: prevAnswer.text };
  }
  const named = unheldFundIn(question, facts);
  if (named && !SWITCHING.test(q)) return { path: "missing", topic: "funds", named };
  return baseRoute(question);
};

// The dip explanation that connects today's NAV to the average price paid. All numbers are computed here, never by the model.
export const isDip = (f) => f.total_return < 0 && f.nav < f.avg_nav;
export const dipSentence = (f, language) =>
  language === "Hinglish"
    ? `Aaj ka NAV (ek unit ki aaj ki keemat) ₹${f.nav.toFixed(2)} hai, jo aapke average ₹${f.avg_nav.toFixed(2)} per unit se lagbhag ${f.nav_vs_avg_pct}% kam hai, isliye aaj aapke units ${inr(f.total_return)} kam ke hain. Aapke saare ${f.units.toFixed(2)} units abhi bhi aapke hain (the units are still yours).`
    : `Today's NAV (the price of one unit) is ₹${f.nav.toFixed(2)}, about ${f.nav_vs_avg_pct}% below the ₹${f.avg_nav.toFixed(2)} you paid on average per unit, so your units are worth ${inr(f.total_return)} less today. You still own all ${f.units.toFixed(2)} units.`;

// ---------- Checks ----------
const ADVICE = [
  "will recover", "don't worry", "dont worry", "you should", "stay invested", "good time to", "buy more now",
  "will grow", "will go up", "will be worth", "band kar do", "continue karo", "chinta mat", "recover ho jayega",
  "upar jayega", "badhega", "underperforming", "it will come back", "keep investing", "rest assured", "guaranteed",
  "keep going", "good time to invest", "working hard", "returns will come", "will come back", "bounce back", "will improve",
  "will pick up", "give it time", "be patient", "in the long run", "long term mein", "wapas aa jayega", "returns aayenge",
];
// Talk of how SIPs usually or have typically behaved; it must end with "...not a forecast".
const TYPICAL = /(usually|typically|historically|in the past|past data|past returns|swings are common|are common|is common|common hain|common hai|aam taur par|aksar)/;
const NOT_FORECAST = /(past data, not a forecast|general information, not a forecast)/;
// An expectations answer explains; it never weighs what reels or videos promised.
const MEDIA = /\b(reels?|youtube|instagram|influencers?|finfluencers?|videos?)\b/;
const PLAIN_NAV = /(price of one unit|per-unit price|per unit price|one unit's price|price per unit|price tag on one unit|ek unit ki|ek unit ka|per-unit keemat|unit ki keemat)/;
const JARGON = [
  { term: /paper loss/, ok: /(only on paper|sirf kaagaz par|sirf kagaz par|sirf paper par)/, say: "say 'a loss only on paper until you sell'" },
  { term: /annuali[sz]/, ok: null, say: "say 'per year'" },
  { term: /average buy nav/, ok: /(average price you paid per unit|paid on average per unit|average price per unit|per unit average)/, say: "say 'the average price you paid per unit'" },
];
const NEW_TERMS = ["xirr", "nav", "redeem", "redemption", "annualis", "annualiz", "cagr", "expense ratio", "folio"];
const ANALOGY = /\b(like|jaise|jaisa|jaisi|similar to|think of|samjho|imagine)\b/;

// Each number token in the text. Small bare counting numbers ("1 unit", "2 sentences") are not data figures,
// and dates ("01 Nov 2026") are not counted as numbers at all.
const DATE = /\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?(\s+\d{4})?\b|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b/gi;
const numberTokens = (text) =>
  (String(text).replace(DATE, " ").match(/[−-]?₹?\d[\d,]*(?:\.\d+)?%?/g) || []).map((t) => {
    const value = parseFloat(t.replace(/−/g, "-").replace(/[₹,%]/g, ""));
    const figure = /[₹%.]/.test(t) || Math.abs(value) > 12;
    return { value, figure };
  }).filter((t) => !Number.isNaN(t.value));

const allowedNumbers = (facts) => {
  const out = [];
  for (const v of Object.values(facts)) if (typeof v === "number") out.push(v, Math.abs(v), Math.round(Math.abs(v)));
  for (const v of [facts.next_installment, facts.started]) if (v) out.push(...numberTokens(v).map((t) => t.value));
  // Every figure in the instalment records the answer may have been given.
  for (const r of facts.instalments || []) out.push(r.amount, r.nav, r.units, +r.units.toFixed(2), +r.units.toFixed(1), Math.round(r.units));
  return out;
};

const sentences = (text) => String(text).trim().split(/(?<=[.!?])\s+(?=[A-Z₹"(]|[a-z])/).filter((s) => s.trim());

export const runGate = ({ answer, question, path, topic, language, profile, facts, previous }) => {
  const a = norm(answer);
  const q = norm(question);
  const checks = [];
  const add = (name, passed, detail = "") => checks.push({ name, passed, detail });
  const figures = numberTokens(answer).filter((t) => t.figure);

  add("Not empty", a.trim().length > 0);

  const advice = ADVICE.find((p) => a.includes(p));
  add("No advice, reassurance or prediction phrases", !advice, advice ? `"${advice}"` : "");

  const held = norm(facts.fund_name);
  const named = [...SAMPLE_FUND_NAMES.filter((n) => n !== held), ...AMCS].find((n) => wordRe(n).test(a));
  add("No fund or AMC names (except your own)", !named, named || "");

  const allowed = allowedNumbers(facts);
  const stray = [...new Set(figures.map((t) => t.value))].filter((n) => !allowed.some((v) => Math.abs(Math.abs(n) - Math.abs(v)) < 0.011));
  const spelled = /\bminus\s+\u20b9?\d/.test(a);
  add("Numbers match your data", stray.length === 0 && !spelled, stray.length ? `not in data: ${stray.join(", ")}` : spelled ? "write \u2212, not 'minus'" : "");

  // A question about a fund the user doesn't hold must not borrow another fund's numbers.
  add("Only the asked-about fund's numbers", path !== "missing" || figures.length === 0, path === "missing" ? `${figures.length} numbers` : "");

  const declines = /(can't recommend|recommend nahi kar sakta|recommend nahi kar sakti)/.test(a);
  const yours = /(decision is yours|faisla aapka)/.test(a);
  const unsure = /(can't predict|predict nahi kar sakta|predict nahi kar sakti)/.test(a);
  const notHeld = /(don't see|do not see|nahi dikh)/.test(a);
  const fits = {
    decline: declines && yours,
    uncertain: unsure && !declines,
    missing: notHeld,
    expectations: !declines && !unsure && !notHeld,
    simplify: !declines || /decision is yours|faisla aapka/.test(a),
    answer: !declines && !unsure && !notHeld,
  }[path];
  add("Answer type fits the question", fits, `expected ${path}`);

  const hits = markerCount(answer);
  const langOk = language === "Hinglish" ? hits >= 3 : hits <= 2;
  add("Language matches question or toggle", langOk, `expected ${language}`);

  const asksReturns = /\b(xirr|return|returns|annual|yearly|per year|minus|profit|gain|perform|kamai|kamaya)\b/.test(q) || topic === "xirr";
  const offTopic = /\bxirr\b/.test(a) && !asksReturns;
  add("Answers only what was asked", !offTopic, offTopic ? "mentions XIRR" : "");

  const wordCount = answer.trim().split(/\s+/).length;
  const maxWords = isBeginner(profile) ? 80 : 120;
  add("Length fits profile", wordCount <= maxWords, `${wordCount} words, max ${maxWords}`);

  const last = norm(sentences(answer).slice(-1)[0] || "");
  const typical = TYPICAL.test(a) || path === "expectations";
  add("Typical behaviour ends with \"not a forecast\"", !typical || NOT_FORECAST.test(last), typical ? "end with 'past data, not a forecast' or 'general information, not a forecast'" : "");

  if (path === "expectations") {
    const media = a.match(MEDIA);
    add("Doesn't judge what reels or videos promised", !media, media ? `mentions "${media[0]}"` : "");
    const story = facts.units_story;
    const need = [inr(facts.invested), inr(facts.current), ...(story ? [story.total_units.toFixed(2)] : [])];
    const missing = need.filter((n) => !answer.includes(n));
    add("Uses your own invested, value and units", missing.length === 0, missing.length ? `missing ${missing.join(", ")}` : "");
  }

  const dipAnswer = path === "answer" && topic === "loss" && isDip(facts);
  const count = new Set(figures.map((t) => Math.abs(t.value))).size;
  // Beginners get at most 3 figures; everyone else at most 8, so answers can't recite every fact.
  if (!isBeginner(profile)) add("At most 8 numbers", count <= 8, `${count} numbers`);
  if (isBeginner(profile)) {
    // The dip and expectations answers carry pre-computed lines with more figures.
    const max = path === "expectations" ? 7 : dipAnswer ? 5 : 3;
    add(`At most ${max} numbers`, count <= max, `${count} numbers`);
    add("NAV explained in plain words", !/\bnav\b/.test(a) || PLAIN_NAV.test(a));
    const jargon = JARGON.find((j) => j.term.test(a) && !(j.ok && j.ok.test(a)));
    add("No unexplained jargon", !jargon, jargon ? jargon.say : "");
  }

  if (dipAnswer) {
    const need = [facts.nav.toFixed(2), facts.avg_nav.toFixed(2), `${facts.nav_vs_avg_pct}%`, inr(facts.total_return).slice(1), facts.units.toFixed(2)];
    const missing = need.filter((n) => !answer.includes(n));
    add("Connects today's NAV to your average price", missing.length === 0, missing.length ? `missing ${missing.join(", ")}` : "");
  }

  if (path === "simplify") {
    const s = sentences(answer).length;
    const prev = norm(previous);
    const newTerm = NEW_TERMS.find((t) => a.includes(t) && !prev.includes(t));
    const problems = [
      s > 2 && `${s} sentences, max 2`,
      figures.length > 1 && `${figures.length} numbers, max 1`,
      !ANALOGY.test(a) && "no everyday comparison",
      !(TOPIC_KEYWORDS[topic] || /./).test(a) && `doesn't stay on ${topic}`,
      newTerm && `new term "${newTerm}"`,
    ].filter(Boolean);
    add("Simpler re-explanation of the same topic", problems.length === 0, problems.join("; "));
  }

  return { passed: checks.every((c) => c.passed), checks, blocked: checks.filter((c) => !c.passed) };
};

// ---------- Safe replies (when the gate blocks a draft, no model answers, or by design) ----------
export const missingReply = (facts, language) =>
  language === "Hinglish"
    ? `Mujhe aapke SIPs mein woh fund nahi dikh raha (I don't see that fund in your SIPs). Main aapke SIP samjha sakta hoon: ${facts.fund_name}.`
    : `I don't see that fund in your SIPs. I can explain the SIPs you hold: ${facts.fund_name}.`;

const simplifyReply = (topic, hi) => {
  const r = {
    xirr: hi
      ? ["XIRR aapke SIP ki saal bhar ki average speed jaisa hai, jaise rukte-chalte car trip ki bhi ek average speed hoti hai.", "Yeh aapke saare instalments ko milakar ek saal ka number banata hai."]
      : ["XIRR is like your SIP's average speed per year, the way a car trip with stops still has one average speed.", "It turns all your instalments into one yearly number."],
    nav: hi
      ? ["NAV ek unit ka price tag jaisa hai, jaise dukaan mein ek aam ka daam likha hota hai.", "Daam roz badalta hai, par aapke units utne hi rehte hain."]
      : ["NAV is like the price tag on one unit, the way a shop marks the price of one mango.", "The tag changes daily, but how many units you own doesn't."],
    options: hi
      ? ["SIP ke options monthly gym plan jaise hain: chalu rakhna, pause, ek mahina skip ya stop, sab options hote hain.", "FinSaar aapke liye chun nahi sakta; faisla aapka hai (the decision is yours)."]
      : ["Your SIP options are like a monthly gym plan: keep going, pause, skip a month or stop.", "FinSaar can't choose for you; the decision is yours."],
    future: hi
      ? ["Kal ka daam koi pakka nahi bata sakta, jaise kal ka mausam koi pakka nahi bata sakta.", "FinSaar sirf aaj ke numbers samjhata hai (I can't predict)."]
      : ["Nobody can promise tomorrow's prices, just like nobody can promise tomorrow's weather.", "FinSaar can't predict; it only explains today's numbers."],
    loss: hi
      ? ["Aapke units aise aam jaise hain jo abhi bhi aapke paas hain, bas aaj unka daam kam hai.", "Yeh nuksaan sirf kaagaz par hai jab tak aap bechte nahi."]
      : ["Your units are like mangoes you still own, but today's price for them is lower.", "It's a loss only on paper until you sell."],
    units: hi
      ? ["Units ko aam (mangoes) jaisa samjho, aur aaj ka daam ek aam ki keemat jaisa.", "Aapke saare aam abhi bhi aapke hain; sirf aaj ka daam badla hai."]
      : ["Think of units like mangoes you own, and today's price as what one mango sells for.", "You still have all your mangoes; only today's price changed, so your units are worth less."],
  };
  const key = { holding: "units", avg: "units", overview: "units", funds: "units" }[topic] || topic;
  return (r[key] || r.units).join(" ");
};

export const safeReply = ({ question, path, topic, language, profile, facts: f }) => {
  const hi = language === "Hinglish";
  const beginner = isBeginner(profile);
  const loss = f.total_return < 0;
  const ret = `${signedInr(f.total_return)} (${signedPct(f.total_return_pct)})`;

  if (path === "missing") return missingReply(f, language);
  if (path === "simplify") return simplifyReply(topic, hi);
  if (path === "decline") {
    return hi
      ? `Main recommend nahi kar sakta (I can't recommend). Continue, pause, skip ya stop SIP ke alag options hain. Stop karne par naye instalments ruk jaate hain, par aapke ${f.units.toFixed(2)} units aapke hi rehte hain. Faisla aapka hai (the decision is yours). Personal advice ke liye SEBI-registered investment adviser ya AMFI investor education dekh sakte hain.`
      : `I can't recommend what to do. Continue, pause, skip and stop are options for any SIP: pause or skip holds new instalments, and stop ends them, while your existing units stay yours unless redeemed. The decision is yours. For personal guidance, speak with a SEBI-registered investment adviser or see AMFI investor education.`;
  }
  if (path === "expectations") return expectationsReply(f, language);
  if (path === "uncertain") {
    return hi
      ? `Main predict nahi kar sakta (I can't predict). Aaj ki baat: NAV (ek unit ki aaj ki keemat) ₹${f.nav.toFixed(2)} hai, aur aapke units abhi bhi aapke hain (the units are still yours). Basics ke liye AMFI investor education dekh sakte hain.`
      : `I can't predict that. What's known today: NAV, the price of one unit, is ₹${f.nav.toFixed(2)}, and your current value is ${inr(f.current)}. For general investor education, see AMFI.`;
  }

  const navPlain = hi ? "NAV (ek unit ki aaj ki keemat)" : "NAV, the price of one unit,";
  switch (topic || topicOf(question)) {
    case "xirr":
      if (f.xirr == null)
        return hi
          ? `XIRR saal bhar ka return hai jo dekhta hai ki har instalment kab gaya. Aapke case mein XIRR abhi available nahi hai, isliye yahan saal ka exact return nahi dikh raha.`
          : `XIRR is a yearly return that accounts for when each instalment went in. It isn't available for your SIP yet, so a yearly figure can't be shown here.`;
      return hi
        ? `XIRR saal bhar ka (per year) return hai, jo dekhta hai ki har instalment kab gaya. Aapka XIRR ${xirrText(f.xirr)} hai. Total return ${signedInr(f.total_return)} hai; yeh per year wala number nahi hai, isliye dono alag dikhte hain.`
        : `XIRR is a yearly return for your SIP that accounts for when each instalment went in. Yours is ${xirrText(f.xirr)}. Your total return is ${ret}, which is not a per-year figure, so the two can look different.`;
    case "units":
      return hi
        ? `Har instalment se naye units milte hain, isliye aapke paas ab ${f.units.toFixed(2)} units hain. Value = units × ${navPlain}. Aaj ka NAV ₹${f.nav.toFixed(2)} hai, isliye value ${inr(f.current)} dikh rahi hai.`
        : `Each instalment buys more units, so you now hold ${f.units.toFixed(2)}. Value is units × ${navPlain} which is ₹${f.nav.toFixed(2)} today, below the ₹${f.avg_nav.toFixed(2)} you paid on average per unit. That's why value is ${inr(f.current)} even as units grow.`;
    case "avg":
      return hi
        ? `Aapne per unit average ₹${f.avg_nav.toFixed(2)} diya hai. ${navPlain} aaj ₹${f.nav.toFixed(2)} hai.`
        : `Your average buy NAV, the average price you paid per unit, is ₹${f.avg_nav.toFixed(2)}. ${navPlain} is ₹${f.nav.toFixed(2)} today, so today's NAV is ${f.nav < f.avg_nav ? "lower" : "higher"} than your average.`;
    case "nav":
      return hi
        ? `${navPlain} ab ₹${f.nav.toFixed(2)} hai. Fund ke andar ke investments ki market value badalne se NAV roz badalta hai. Aapke units wahi rehte hain.`
        : `${navPlain} is ₹${f.nav.toFixed(2)} today. It moves every day with the market value of what the fund holds. Your units stay the same; only their price changes.`;
    case "loss":
      if (isDip(f)) return `${hi ? "Nahi, paisa gaya nahi hai." : "Not gone."} ${dipSentence(f, language)}`;
      return hi
        ? `Nahi. Units abhi bhi aapke hain (the units are still yours), aur abhi total return ${signedInr(f.total_return)} hai.`
        : loss
          ? `Not gone. Your units are still yours: ${f.units.toFixed(2)} units, worth ${inr(f.current)} today on ${inr(f.invested)} invested. It's a loss only on paper until you sell.`
          : `Not gone. Your units are still yours, worth ${inr(f.current)} today on ${inr(f.invested)} invested (${ret}).`;
    case "instalment": {
      const records = f.instalments || [];
      if (!records.length)
        return hi
          ? `Is holding ke har instalment ka record mere paas nahi hai, sirf total. Aapke paas ${f.units.toFixed(2)} units hain.`
          : `I don't have instalment-by-instalment records for this holding, only the totals. You hold ${f.units.toFixed(2)} units.`;
      const r = pickInstalments(question, records)[0] || records[records.length - 1];
      const most = r === records.reduce((a, b) => (b.units > a.units ? b : a)) && /(most|zyada)/.test(norm(question));
      return hi
        ? `${r.date} ke instalment mein ${inr(r.amount)} se ${r.units.toFixed(2)} units mile, jab NAV (ek unit ki keemat) \u20b9${r.nav.toFixed(2)} tha.${most ? " Us din NAV sabse kam tha, isliye sabse zyada units mile." : ""}`
        : `Your ${r.date} instalment of ${inr(r.amount)} bought ${r.units.toFixed(2)} units at a NAV (the price of one unit) of \u20b9${r.nav.toFixed(2)}.${most ? " NAV was lowest that day, so it bought the most units." : ""}`;
    }
    case "holding":
      return hi
        ? `Aapke paas ${f.units.toFixed(2)} units hain. In units ki abhi ki value ${inr(f.current)} hai. ${navPlain} se units ki total value nikalti hai.`
        : `You hold ${f.units.toFixed(2)} units, worth ${inr(f.current)} today at a NAV (price of one unit) of ₹${f.nav.toFixed(2)}.`;
    default:
      return hi
        ? `Aapne ${inr(f.invested)} invest kiye hain aur aaj value ${inr(f.current)} hai. ${beginner ? "" : `Total return ${ret} hai. `}Kisi number ke baare mein poochiye, main simple shabdon mein samjhaunga.`
        : `You've invested ${inr(f.invested)} and your SIP is worth ${inr(f.current)} today (${ret}). Ask about any number and I'll explain it simply.`;
  }
};

// The answer pattern for first-year expectations; every figure comes from the user's SIP data.
export const expectationsReply = (f, language) => {
  const hi = language === "Hinglish";
  const story = f.units_story || unitsStory(f.instalments);
  const lower = (t) => t.charAt(0).toLowerCase() + t.slice(1);
  const pct = signedPct(f.total_return_pct);
  if (hi)
    return `Shuru ke mahinon mein SIP ki value upar-neeche hoti hai; early swings common hain. Aapke ${inr(f.invested)} aaj ${inr(f.current)} hain (${pct}). ${
      story ? `Kam daam par har instalment ne zyada units kharide: ${lower(story.hi)}` : `Aapke paas ${f.units.toFixed(2)} units hain; kam daam se unki value badalti hai, ginti nahi.`
    } Yeh general information hai, forecast nahi (general information, not a forecast).`;
  return `In the first months, SIP value moves up and down; early swings are common. Your ${inr(f.invested)} is ${inr(f.current)} today (${pct}). ${
    story ? `Each instalment at a lower price bought more units: ${lower(story.en)}` : `You hold ${f.units.toFixed(2)} units; a lower price changes what they're worth, not how many you have.`
  } This is general information, not a forecast.`;
};

export const sourceFor = (path) =>
  path === "decline" ? "Not investment advice · SEBI / AMFI investor education" : path === "uncertain" ? "AMFI investor education" : "Your SIP data";
