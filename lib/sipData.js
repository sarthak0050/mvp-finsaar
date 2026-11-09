// The user's SIP transaction records (the data FinSaar retrieves from), and every summary
// number derived from them in code: units, invested, average price, value and XIRR.

// Valuation date for the prototype snapshot, fixed so the numbers stay reproducible.
export const AS_OF = "2026-11-07";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const label = (iso) => { const [y, m, d] = iso.split("-"); return `${d} ${MONTHS[Number(m) - 1]} ${y}`; };

const record = (n, iso, nav, amount = 2000) => ({
  n,
  iso,
  date: label(iso),
  amount,
  nav,
  units: +(amount / nav).toFixed(3),
});

// NAV on each instalment date. Dip day: NAV slid from July to November; regular day: it rose.
export const INSTALMENTS = {
  dip: [record(1, "2026-07-01", 25.62), record(2, "2026-08-01", 24.95), record(3, "2026-09-01", 24.31), record(4, "2026-10-01", 23.74), record(5, "2026-11-01", 22.88)],
  normal: [record(1, "2026-07-01", 21.38), record(2, "2026-08-01", 21.8), record(3, "2026-09-01", 22.05), record(4, "2026-10-01", 22.41), record(5, "2026-11-01", 22.86)],
};

const days = (a, b) => (new Date(`${b}T00:00:00Z`) - new Date(`${a}T00:00:00Z`)) / 86400000;

// XIRR: the yearly rate at which all instalments, grown to the valuation date, equal today's value.
export const xirr = (records, currentValue, asOf = AS_OF) => {
  const flows = [...records.map((r) => [r.iso, -r.amount]), [asOf, currentValue]];
  const npv = (rate) => flows.reduce((sum, [d, amt]) => sum + amt / (1 + rate) ** (days(flows[0][0], d) / 365), 0);
  let lo = -0.99, hi = 10;
  for (let i = 0; i < 200; i++) {
    const mid = (lo + hi) / 2;
    if (npv(mid) > 0) lo = mid; else hi = mid;
  }
  return +(((lo + hi) / 2) * 100).toFixed(1);
};

export const holdingFromRecords = (records, nav) => {
  const units = +records.reduce((s, r) => s + r.units, 0).toFixed(2);
  const invested = records.reduce((s, r) => s + r.amount, 0);
  const current = Math.round(units * nav);
  return {
    invested,
    current,
    units,
    avg_nav: +(invested / units).toFixed(2),
    installments: records.length,
    started: records[0].date,
    xirr: xirr(records, current),
  };
};
