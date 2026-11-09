import { getPortfolio } from "../lib/portfolio.js";

export default function handler(req, res) {
  const scenario = req.query.scenario === "normal" ? "normal" : "dip";
  res.setHeader("Cache-Control", "no-store");
  res.status(200).json(getPortfolio(scenario, req));
}
