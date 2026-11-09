import { useState } from "react";
import { ArrowUpRight, BookOpen, ChevronDown, Info, X } from "lucide-react";
import { inr } from "./format";

const whyFor = ({ dip: { day_drop, below_invested } }) =>
  [day_drop && "NAV moved 1% or more in a day", below_invested && "today's value is under the amount invested"].filter(Boolean).join(" and ");

const dipCopy = (s) => {
  const { below_invested } = s.dip;
  const value = `${inr(s.current)} today on ${inr(s.invested)} invested (${s.total_return_pct < 0 ? "−" : "+"}${Math.abs(s.total_return_pct).toFixed(2)}%).`;
  // Lead with units (computed in code from the instalment records); value comes second.
  if (s.units_story) return { title: "Your dip, in units", body: s.units_story.en, sub: value, why: whyFor(s) };
  const title = below_invested ? "A quick look at your SIP today" : "Your fund's NAV moved today";
  const body = `${value} NAV changes every day; your ${s.units.toFixed(2)} units stay the same.`;
  return { title, body, why: whyFor(s) };
};

export const DipCard = ({ summary, onUnderstand, testPrefix }) => {
  const [showWhy, setShowWhy] = useState(false);
  const { day_drop, below_invested } = summary.dip;
  if (!day_drop && !below_invested) {
    return (
      <div className="dip-rule" data-testid={`${testPrefix}-dip-rule-note`}>
        <Info size={15} />
        <span>FinSaar explains your SIP here when NAV moves 1% or more in a day, or today's value is under the amount invested.</span>
      </div>
    );
  }
  const c = dipCopy(summary);
  return (
    <div className="dip-alert" data-testid={`${testPrefix}-dip-card`}>
      <div className="dip-text">
        <span className="dip-badge">FinSaar</span>
        <p className="dip-title" data-testid={`${testPrefix}-dip-title`}>{c.title}</p>
        <span className={c.sub ? "dip-hero" : undefined} data-testid={`${testPrefix}-dip-body`}>{c.body}</span>
        {c.sub && <small className="dip-sub" data-testid={`${testPrefix}-dip-value`}>{c.sub}</small>}
        <button className="dip-why" data-testid={`${testPrefix}-dip-why-button`} onClick={() => setShowWhy(!showWhy)}>Why am I seeing this? <ChevronDown size={12} className={showWhy ? "flip" : ""} /></button>
        {showWhy && <small data-testid={`${testPrefix}-dip-reason`}>FinSaar shows this when {c.why}. It's an explanation, not a signal to act.</small>}
      </div>
      <button data-testid={`${testPrefix}-dip-understand-button`} onClick={onUnderstand}>Understand this <ArrowUpRight size={14} /></button>
    </div>
  );
};

const Step = ({ n, title, children }) => (
  <li className="dip-step"><span>{n}</span><div><b>{title}</b><p>{children}</p></div></li>
);

export const DipSheet = ({ summary: s, onClose, openChat }) => {
  // Computed here, never by the model: how far today's NAV sits below the average price paid.
  const dip = s.total_return < 0 && s.nav < s.avg_nav;
  const belowPct = Math.round(((s.avg_nav - s.nav) / s.avg_nav) * 100);
  const prompts = ["Iska matlab paisa doob gaya?", "Why are my units going up but value going down?", "Should I stop my SIP?"];
  return (
    <div className="sheet-overlay">
      <div className="explain-sheet dip-sheet" data-testid="dip-sheet">
        <div className="sheet-handle" />
        <button className="sheet-close" data-testid="close-dip-sheet-button" onClick={onClose}><X size={18} /></button>
        <span className="eyebrow">UNDERSTAND TODAY'S VALUE</span>
        <h2>What changed, and what didn't</h2>
        {s.units_story && <p className="dip-units-hero" data-testid="dip-sheet-units">{s.units_story.en}</p>}
        <ol className="dip-steps">
          <Step n="1" title="What changed">{dip ? `Today's NAV is ₹${s.nav.toFixed(2)}, about ${belowPct}% below the ₹${s.avg_nav.toFixed(2)} you paid on average per unit, so your units are worth ${inr(s.total_return)} less today.` : `Today's NAV is ₹${s.nav.toFixed(2)}; you paid ₹${s.avg_nav.toFixed(2)} on average per unit.`}</Step>
          <Step n="2" title="What you still own">You still own all {s.units.toFixed(2)} units. A NAV change moves their price, not how many you have.</Step>
          <Step n="3" title="What the number means">{`At today's NAV your units are worth ${inr(s.current)} on ${inr(s.invested)} invested. This changes only when NAV changes, and becomes final only if units are redeemed.`}</Step>
          <Step n="4" title="Your choices">Continue, pause, skip or stop are options for any SIP. FinSaar won't pick one for you; the decision is yours.</Step>
        </ol>
        <div className="source-note"><BookOpen size={15} /><span><b>Based on</b>Your SIP data · learn more at <a href="https://www.amfiindia.com/investor-corner" target="_blank" rel="noreferrer" data-testid="dip-amfi-link">AMFI</a> and <a href="https://investor.sebi.gov.in" target="_blank" rel="noreferrer" data-testid="dip-sebi-link">SEBI investor site</a></span></div>
        <div className="dip-prompts">{prompts.map((q, i) => <button key={q} data-testid={`dip-prompt-${i}`} onClick={() => openChat(q)}>{q}</button>)}</div>
        <p className="advice-note">Educational only. Not investment advice.</p>
      </div>
    </div>
  );
};
