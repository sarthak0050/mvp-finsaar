import { ChevronRight, CircleHelp, MoreVertical, Plus, Sparkles, X } from "lucide-react";
import { DipCard } from "./DipCard";
import { Metric } from "./Metric";
import { inr, signedInr, signedInr2, signedPct, xirrText } from "./format";

const ContinueBanner = ({ lastTopic, openChat, onDismiss }) => {
  const go = () => (lastTopic ? openChat() : openChat("What is NAV and how does it affect my SIP?"));
  return (
    <div className="learning-banner clickable" role="button" tabIndex={0} data-testid="continue-learning-banner" onClick={go} onKeyDown={(e) => e.key === "Enter" && go()}>
      <div className="spark"><Sparkles size={17} /></div>
      <div>
        <b>{lastTopic ? "Continue where you left off" : "Start with the basics"}</b>
        <span data-testid="continue-learning-text">{lastTopic ? `Last time: ${lastTopic}. Continue?` : "What NAV means for your SIP"}</span>
      </div>
      <ChevronRight size={17} className="banner-arrow" />
      <button data-testid="dismiss-learning-button" aria-label="Dismiss" onClick={(e) => { e.stopPropagation(); onDismiss(); }}><X size={16} /></button>
    </div>
  );
};

const ScenarioSwitch = ({ scenario, setScenario }) => (
  <div className="scenario-switch" data-testid="scenario-switch">
    <span>Prototype scenario</span>
    <div>
      <button className={scenario === "normal" ? "active" : ""} data-testid="scenario-normal" onClick={() => setScenario("normal")}>Regular day</button>
      <button className={scenario === "dip" ? "active" : ""} data-testid="scenario-dip" onClick={() => setScenario("dip")}>Dip day</button>
    </div>
  </div>
);

export const Dashboard = (p) => {
  const s = p.summary;
  const neg = s.total_return < 0;
  return (
    <section className="page reveal">
      <div className="page-heading"><div><p className="eyebrow">YOUR MONEY, MADE CLEAR</p><p className="subline">Here’s what your SIPs are doing today.</p></div><button className="icon-button" data-testid="dashboard-more-button"><MoreVertical size={19} /></button></div>
      {p.returning && <ContinueBanner lastTopic={p.lastTopic} openChat={p.openChat} onDismiss={() => p.setReturning(false)} />}
      <ScenarioSwitch scenario={p.scenario} setScenario={p.setScenario} />
      <div className="section-head"><h2>Portfolio snapshot</h2><span data-testid="portfolio-date">As of today</span></div>
      <div className="snapshot">
        <div className="snapshot-top">
          <span>Current value <CircleHelp size={13} /></span>
          <strong data-testid="current-value">{inr(s.current)}</strong>
          {s.day_change != null && <em className={s.day_change < 0 ? "down" : ""} data-testid="day-change">1D returns {signedInr2(s.day_change)} ({signedPct(s.day_change_pct)})</em>}
        </div>
        <div className="metrics">
          <Metric label="Invested" value={inr(s.invested)} onClick={() => p.setExplain({ title: "Invested amount", body: "This is the total amount recorded as paid into your SIP so far.", source: "Your SIP transaction history" })} />
          <Metric label="Total returns" value={`${signedInr(s.total_return)} (${signedPct(s.total_return_pct)})`} tone={neg ? "negative" : "positive"} onClick={() => p.setExplain({ title: "Total returns", body: "This compares your current value with the amount invested. It does not predict what happens next.", source: "Your visible portfolio data" })} />
          <Metric label="XIRR (Active)" value={xirrText(s.xirr)} onClick={() => p.setExplain({ title: "XIRR", body: s.xirr == null ? "XIRR isn't available for this holding yet, because instalment dates are missing." : `XIRR is a per-year return that considers when each instalment went in. Yours is ${xirrText(s.xirr)}.`, source: "Investor education context · your SIP dates" })} />
        </div>
      </div>
      <DipCard summary={s} onUnderstand={p.openDip} testPrefix="dashboard" />
      <div className="section-head"><h2>Your holdings <span className="count">1</span></h2><button data-testid="holdings-sort-button">Current <ChevronRight size={14} /></button></div>
      <button className="fund-row" data-testid="holding-fund-row" onClick={() => p.openFund(p.fund)}>
        <div className="fund-avatar">S</div>
        <div className="fund-info"><b>{p.fund?.name}</b><span>SIP · {p.holding?.installments} instalments</span></div>
        <div className="fund-value"><b className={neg ? "down" : ""}>{inr(s.current)}</b><span>({inr(s.invested)})</span></div>
        <ChevronRight size={17} />
      </button>
      <button className="outline-action" data-testid="import-investments-button" onClick={() => p.setAddOpen(true)}><Plus size={16} /> Import or add investments</button>
      <button className="ask-strip" data-testid="dashboard-ask-button" onClick={() => p.openChat()}><Sparkles size={17} /><span><b>Have a question about your numbers?</b><small>Ask FinSaar in English or Hinglish.</small></span><ChevronRight size={17} /></button>
    </section>
  );
};
