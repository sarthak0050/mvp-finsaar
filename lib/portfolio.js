// Server-side portfolio data. Mirrors src/lib/sampleData.js, plus the holding a user
// saves from "Import or add investments" (kept in a cookie, since Vercel functions are stateless).
import { INSTALMENTS, holdingFromRecords } from "./sipData.js";
import { unitsStory } from "./unitsStory.js";

export const FUNDS = [
  { id: "flexi-cap", name: "Sample Flexi Cap Fund", category: "Flexi Cap · Direct Growth", nav: 23.06, prev_nav: 22.9, return_1y: 18.4, risk: "Moderately high", color: "#087f5b" },
  { id: "bluechip", name: "Sample Bluechip Fund", category: "Large Cap · Direct Growth", nav: 46.28, prev_nav: 46.1, return_1y: 14.8, risk: "Moderate", color: "#4263eb" },
  { id: "balanced", name: "Sample Balanced Advantage", category: "Hybrid · Direct Growth", nav: 31.72, prev_nav: 31.6, return_1y: 11.2, risk: "Moderately high", color: "#d97706" },
  { id: "small-cap", name: "Sample Small Cap Fund", category: "Small Cap · Direct Growth", nav: 62.14, prev_nav: 61.8, return_1y: 22.6, risk: "Very high", color: "#be4bdb" },
];

// Sample holdings: every figure (units, value, average price, XIRR, start date) is computed from the instalment records.
const NORMAL_HOLDING = { id: "holding-1", fund_id: "flexi-cap", sip: 2000, next_installment: "01 Dec", prev_nav: 22.9, ...holdingFromRecords(INSTALMENTS.normal, FUNDS[0].nav), instalments: INSTALMENTS.normal };
const DIP_HOLDING = { id: "holding-dip", fund_id: "flexi-cap", sip: 2000, next_installment: "01 Dec", prev_nav: 23.18, ...holdingFromRecords(INSTALMENTS.dip, FUNDS[0].nav), instalments: INSTALMENTS.dip };

export const HOLDING_COOKIE = "finsaar-holding";

export const summarize = (h, fund) => {
  const ret = h.current - h.invested;
  const nav = fund.nav;
  const prev = h.prev_nav ?? fund.prev_nav;
  const day = +(h.units * (nav - prev)).toFixed(2);
  const dayPct = +(((nav - prev) / prev) * 100).toFixed(2);
  return {
    invested: h.invested,
    current: h.current,
    units: h.units,
    total_return: ret,
    total_return_pct: +((ret / h.invested) * 100).toFixed(2),
    day_change: day,
    day_change_pct: dayPct,
    avg_nav: h.avg_nav || +(h.invested / h.units).toFixed(2),
    nav,
    xirr: h.xirr ?? null,
    dip: { day_drop: dayPct <= -1, below_invested: h.current < h.invested },
    units_story: unitsStory(h.instalments),
  };
};

const readCookie = (req, name) => {
  const raw = req.headers?.cookie || "";
  const hit = raw.split(";").map((c) => c.trim()).find((c) => c.startsWith(`${name}=`));
  if (!hit) return null;
  try {
    return JSON.parse(decodeURIComponent(hit.slice(name.length + 1)));
  } catch {
    return null;
  }
};

export const getPortfolio = (scenario, req) => {
  const saved = scenario === "normal" ? readCookie(req, HOLDING_COOKIE) : null;
  const holding = scenario === "dip" ? DIP_HOLDING : saved || NORMAL_HOLDING;
  const fund = FUNDS.find((f) => f.id === holding.fund_id) || FUNDS[0];
  return { holding, fund, funds: FUNDS, summary: summarize(holding, fund) };
};

// Facts the assistant may use. Every number in an answer must come from here.
export const factsFor = (portfolio) => {
  const { holding: h, summary: s, fund } = portfolio;
  return {
    fund_name: fund.name,
    fund_category: fund.category,
    fund_risk: fund.risk,
    prev_nav: h.prev_nav ?? fund.prev_nav,
    // Instalment records (sample holdings only); a holding added by hand has totals but no records.
    instalments: h.instalments || [],
    // How far today's NAV sits from the average price paid, rounded to a whole percent for plain speech.
    nav_vs_avg_pct: Math.round(Math.abs(((s.nav - s.avg_nav) / s.avg_nav) * 100)),
    // The units line (computed from the instalment records), and its numbers, so answers may quote them.
    units_story: s.units_story,
    units_latest: s.units_story?.units_latest,
    units_at_prev: s.units_story?.units_at_prev,
    latest_amount: s.units_story?.amount,
    invested: s.invested,
    current: s.current,
    total_return: s.total_return,
    total_return_pct: s.total_return_pct,
    units: s.units,
    avg_nav: s.avg_nav,
    nav: s.nav,
    xirr: s.xirr,
    day_change: s.day_change,
    day_change_pct: s.day_change_pct,
    sip: h.sip,
    installments: h.installments,
    next_installment: h.next_installment,
    started: h.started,
  };
};
