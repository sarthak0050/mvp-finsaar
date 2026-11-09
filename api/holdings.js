import { FUNDS, HOLDING_COOKIE, getPortfolio } from "../lib/portfolio.js";

const today = () => new Date().toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });

export default function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  const b = req.body || {};
  const invested = Number(b.invested);
  const current = Number(b.current);
  if (!(invested > 0) || !(current >= 0)) return res.status(422).json({ error: "invested and current must be positive numbers" });
  const holding = {
    id: `holding-${Math.random().toString(16).slice(2, 10)}`,
    fund_id: FUNDS.some((f) => f.id === b.fund_id) ? b.fund_id : "flexi-cap",
    invested,
    current,
    sip: Number(b.sip) || 2000,
    units: Number(b.units) || 452.73,
    installments: Number(b.installments) || 6,
    next_installment: "01 Dec",
    started: today(),
  };
  res.setHeader("Set-Cookie", `${HOLDING_COOKIE}=${encodeURIComponent(JSON.stringify(holding))}; Path=/; Max-Age=31536000; SameSite=Lax; HttpOnly`);
  res.status(200).json(getPortfolio("normal", { headers: { cookie: `${HOLDING_COOKIE}=${encodeURIComponent(JSON.stringify(holding))}` } }));
}
