// The units line FinSaar leads with on a dip, computed in code from the instalment records
// (never by the model). Shared by the dashboard card, the dip sheet and the chat answers.

const rupees = (n) => `₹${Math.round(n).toLocaleString("en-IN")}`;

export const unitsStory = (records) => {
  if (!records?.length) return null;
  const latest = records[records.length - 1];
  const prev = records[records.length - 2];
  const totalUnits = +records.reduce((s, r) => s + r.units, 0).toFixed(2);
  const unitsLatest = Math.round(latest.amount / latest.nav);
  const unitsAtPrev = prev ? Math.round(latest.amount / prev.nav) : null;
  // Only when this month's price was lower than last month's is there a "bought more" line to show.
  const cheaper = Boolean(prev) && latest.nav < prev.nav;
  const total = totalUnits.toFixed(2);
  const amount = rupees(latest.amount);
  return {
    cheaper,
    amount: latest.amount,
    units_latest: unitsLatest,
    units_at_prev: unitsAtPrev,
    total_units: totalUnits,
    en: cheaper
      ? `This month your ${amount} bought ${unitsLatest} units. At last month's price, it would have bought ${unitsAtPrev}. You now own ${total} units; none were lost.`
      : `You now own ${total} units; none were lost. A lower price changes what they're worth today, not how many you have.`,
    hi: cheaper
      ? `Is mahine aapke ${amount} se ${unitsLatest} units aaye. Pichle mahine ke daam par ${unitsAtPrev} aate. Ab aapke paas ${total} units hain; koi unit kam nahi hua (none were lost).`
      : `Ab aapke paas ${total} units hain; koi unit kam nahi hua (none were lost). Kam daam se aaj unki value badalti hai, units ki ginti nahi.`,
  };
};
