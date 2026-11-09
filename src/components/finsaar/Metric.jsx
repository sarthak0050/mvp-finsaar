import { CircleHelp } from "lucide-react";

export const Metric = ({ label, value, tone = "neutral", onClick }) => (
  <button className={`metric ${tone}`} data-testid={`metric-${label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-$/, "")}`} onClick={onClick}>
    <span>{label} <CircleHelp size={12} /></span>
    <strong>{value}</strong>
  </button>
);
