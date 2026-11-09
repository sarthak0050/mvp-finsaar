import { loadLatestRun } from "../../lib/evalStore.js";

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  res.status(200).json({ run: await loadLatestRun() });
}
