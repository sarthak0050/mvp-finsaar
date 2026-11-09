import { INSTALMENTS } from "../../lib/sipData.js";
import { unitsStory } from "../../lib/unitsStory.js";

export const SAMPLE_FUNDS = [
  { id: "flexi-cap", name: "Sample Flexi Cap Fund", category: "Flexi Cap · Direct Growth", nav: 23.06, return_1y: 18.4, risk: "Moderately high", color: "#087f5b" },
  { id: "bluechip", name: "Sample Bluechip Fund", category: "Large Cap · Direct Growth", nav: 46.28, return_1y: 14.8, risk: "Moderate", color: "#4263eb" },
  { id: "balanced", name: "Sample Balanced Advantage", category: "Hybrid · Direct Growth", nav: 31.72, return_1y: 11.2, risk: "Moderately high", color: "#d97706" },
  { id: "small-cap", name: "Sample Small Cap Fund", category: "Small Cap · Direct Growth", nav: 62.14, return_1y: 22.6, risk: "Very high", color: "#be4bdb" },
];

// Offline fallback only. Mirrors the server's figures, which are computed from the instalment records (lib/sipData.js).
const NORMAL_HOLDING = { id: "holding-1", fund_id: "flexi-cap", invested: 10000, current: 10440, units: 452.73, avg_nav: 22.09, sip: 2000, installments: 5, next_installment: "01 Dec", started: "01 Jul 2026", xirr: 26.0, prev_nav: 22.90 };
const DIP_HOLDING = { id: "holding-dip", fund_id: "flexi-cap", invested: 10000, current: 9504, units: 412.15, avg_nav: 24.26, sip: 2000, installments: 5, next_installment: "01 Dec", started: "01 Jul 2026", xirr: -24.3, prev_nav: 23.18 };

const summarize = (h) => {
  const ret = h.current - h.invested;
  const nav = SAMPLE_FUNDS[0].nav;
  const day = +(h.units * (nav - h.prev_nav)).toFixed(2);
  const dayPct = +((nav - h.prev_nav) / h.prev_nav * 100).toFixed(2);
  return { invested: h.invested, current: h.current, units: h.units, total_return: ret, total_return_pct: +(ret / h.invested * 100).toFixed(2), day_change: day, day_change_pct: dayPct, avg_nav: h.avg_nav || +(h.invested / h.units).toFixed(2), nav, xirr: h.xirr, dip: { day_drop: dayPct <= -1, below_invested: h.current < h.invested } };
};

export const SAMPLE_PORTFOLIOS = {
  normal: { holding: NORMAL_HOLDING, fund: SAMPLE_FUNDS[0], funds: SAMPLE_FUNDS, summary: { ...summarize(NORMAL_HOLDING), units_story: unitsStory(INSTALMENTS.normal) } },
  dip: { holding: DIP_HOLDING, fund: SAMPLE_FUNDS[0], funds: SAMPLE_FUNDS, summary: { ...summarize(DIP_HOLDING), units_story: unitsStory(INSTALMENTS.dip) } },
};
