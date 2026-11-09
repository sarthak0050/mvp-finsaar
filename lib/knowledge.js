// The investor-education knowledge base FinSaar retrieves definitions from. Written in our own
// plain words, based on the topics AMFI and SEBI investor education cover; each entry links to the source.

const AMFI = { name: "AMFI investor education", url: "https://www.amfiindia.com/investor-corner" };
const SEBI = { name: "SEBI investor site", url: "https://investor.sebi.gov.in" };

export const KNOWLEDGE = [
  {
    id: "nav",
    title: "What NAV means",
    topics: ["nav", "units", "loss", "avg"],
    keywords: ["nav", "net asset value", "price", "keemat", "daam", "kam kyun", "gir", "down"],
    text: "NAV (net asset value) is the price of one unit of a mutual fund on a given day. It is worked out after the market closes from the value of everything the fund holds, so it changes every business day.",
    source: AMFI,
  },
  {
    id: "units",
    title: "How instalments buy units",
    topics: ["units", "holding", "instalment", "loss"],
    keywords: ["unit", "units", "kitne", "how many", "bought", "mile", "badh", "going up", "instalment", "kisht"],
    text: "Each instalment buys units at that day's NAV: units = amount ÷ NAV. When NAV is lower, the same amount buys more units. The number of units you hold only goes down if you redeem (sell) some.",
    source: AMFI,
  },
  {
    id: "sip",
    title: "How a SIP works",
    topics: ["instalment", "overview"],
    keywords: ["sip", "monthly", "instalment", "installment", "date", "kisht", "har mahine"],
    text: "A SIP (systematic investment plan) puts a fixed amount into the fund on a fixed date each month, buying units at that date's NAV.",
    source: AMFI,
  },
  {
    id: "xirr",
    title: "What XIRR means",
    topics: ["xirr"],
    keywords: ["xirr", "return", "yearly", "per year", "annual", "minus", "saal"],
    text: "XIRR is a return per year that takes into account the date and size of every instalment. Over a short period, a small change in value can show up as a large yearly figure, because it is scaled up to a full year.",
    source: AMFI,
  },
  {
    id: "total-return",
    title: "Total return",
    topics: ["xirr", "loss", "holding"],
    keywords: ["total return", "return", "profit", "loss", "gain", "nuksaan", "fayda", "kamaya"],
    text: "Total return compares today's value with the total amount you have put in. It is not a per-year figure, so it can look very different from XIRR.",
    source: AMFI,
  },
  {
    id: "average-price",
    title: "Average price paid per unit",
    topics: ["avg", "loss", "units"],
    keywords: ["average", "avg", "buy price", "paid", "cost"],
    text: "The average price you paid per unit is the total amount invested divided by the total units. Comparing it with today's NAV shows whether your units are worth more or less than what you paid for them.",
    source: AMFI,
  },
  {
    id: "unrealised",
    title: "A loss only on paper",
    topics: ["loss"],
    keywords: ["doob", "lost", "loss", "gone", "gaya", "nuksaan", "paisa"],
    text: "When value falls, the loss stays only on paper until units are redeemed: you still own the same number of units, and only their price has changed.",
    source: AMFI,
  },
  {
    id: "sip-options",
    title: "SIP options: continue, pause, skip, stop",
    topics: ["options"],
    keywords: ["stop", "pause", "skip", "continue", "band", "rok", "sell", "redeem", "switch"],
    text: "Continue keeps instalments going. Pause stops new instalments for a set period. Skip misses one instalment. Stop ends future instalments. In every case the units already bought remain in the fund unless you redeem them. For personal advice, speak to a SEBI-registered investment adviser.",
    source: SEBI,
  },
  {
    id: "market-linked",
    title: "Market-linked returns",
    topics: ["future"],
    keywords: ["recover", "future", "will", "next", "predict", "jayega", "hoga", "market"],
    text: "Mutual fund values are market-linked. Past returns do not indicate future returns, and no one can know what a fund's NAV will be in the future.",
    source: AMFI,
  },
  {
    id: "riskometer",
    title: "The riskometer",
    topics: ["funds"],
    keywords: ["risk", "riskometer", "safe", "risky", "volatile"],
    text: "Every mutual fund scheme shows a riskometer level, from low to very high, describing how much its value can move up and down.",
    source: AMFI,
  },
];
