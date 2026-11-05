"""All FinSaar calculations. The AI never calculates; every number it may use comes from here."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "sip.json"


@dataclass
class Instalment:
    date: date
    amount: float
    nav: float
    units: float


@dataclass
class SipSummary:
    fund: str
    category: str
    monthly_amount: float
    instalments: list[Instalment]
    today: date
    current_nav: float
    invested: float
    total_units: float
    avg_nav: float
    current_value: float
    gain: float            # negative = loss
    gain_pct: float        # absolute return, %
    xirr_pct: float        # annualised, %
    nav_drop: float = field(default=0.0)      # avg buy NAV - today's NAV
    nav_drop_pct: float = field(default=0.0)  # that drop as % of avg buy NAV

    @property
    def n_instalments(self) -> int:
        return len(self.instalments)

    @property
    def is_down(self) -> bool:
        return self.current_value < self.invested


# ---------- core maths ----------

def xirr(cashflows: list[tuple[date, float]]) -> float:
    """Annualised return (as a fraction) for dated cashflows, Actual/365. Bisection: robust, no deps."""
    t0 = min(d for d, _ in cashflows)

    def npv(rate: float) -> float:
        return sum(a / (1 + rate) ** ((d - t0).days / 365.0) for d, a in cashflows)

    lo, hi = -0.9999, 10.0
    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        raise ValueError("XIRR has no solution in range")
    for _ in range(300):
        mid = (lo + hi) / 2
        f_mid = npv(mid)
        if abs(f_mid) < 1e-9:
            break
        if (f_mid > 0) == (f_lo > 0):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
    return (lo + hi) / 2


def load_sip(path: Path | str = DATA_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compute(sip: dict | None = None) -> SipSummary:
    sip = sip or load_sip()
    insts = [
        Instalment(date.fromisoformat(i["date"]), float(i["amount"]), float(i["nav"]),
                   float(i["amount"]) / float(i["nav"]))
        for i in sip["instalments"]
    ]
    today = date.fromisoformat(sip["today"]["date"])
    cur_nav = float(sip["today"]["nav"])
    invested = sum(i.amount for i in insts)
    units = sum(i.units for i in insts)
    avg_nav = invested / units
    value = units * cur_nav
    gain = value - invested
    flows = [(i.date, -i.amount) for i in insts] + [(today, value)]
    return SipSummary(
        fund=sip["fund"], category=sip.get("category", ""), monthly_amount=float(sip["monthly_amount"]),
        instalments=insts, today=today, current_nav=cur_nav, invested=invested, total_units=units,
        avg_nav=avg_nav, current_value=value, gain=gain, gain_pct=gain / invested * 100,
        xirr_pct=xirr(flows) * 100, nav_drop=avg_nav - cur_nav,
        nav_drop_pct=(avg_nav - cur_nav) / avg_nav * 100,
    )


# ---------- formatting (Indian digit grouping) ----------

def _group_indian(n: int) -> str:
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


def inr(x: float, decimals: int = 0) -> str:
    """₹ amount, sign-free (callers say 'below' / 'loss' in words)."""
    x = abs(x)
    if decimals == 0:
        return "₹" + _group_indian(int(math.floor(x + 0.5)))
    whole = int(math.floor(x))
    frac = f"{x - whole:.{decimals}f}"[1:]
    if frac.startswith(".") and float(frac) >= 1:  # rounding overflow guard
        whole, frac = whole + 1, "." + "0" * decimals
    return "₹" + _group_indian(whole) + frac


def signed_pct(x: float, decimals: int = 1) -> str:
    sign = "−" if x < 0 else "+"
    return f"{sign}{abs(x):.{decimals}f}%"


def fmt_date(d: date) -> str:
    return f"{d.day} {d.strftime('%b %Y')}"


# ---------- what the AI and the gate are allowed to see ----------

def facts_block(s: SipSummary) -> str:
    """The 'SIP facts' block sent to the AI. Every number here is pre-computed."""
    status = "below" if s.is_down else "above"
    lines = [
        f"Fund: {s.fund}",
        f"Monthly SIP: {inr(s.monthly_amount)}; instalments so far: {s.n_instalments} "
        f"({fmt_date(s.instalments[0].date)} to {fmt_date(s.instalments[-1].date)})",
        f"Total invested: {inr(s.invested)}",
        f"Units held: {s.total_units:.2f} (about {round(s.total_units)})",
        f"Average buy NAV: {inr(s.avg_nav, 2)}",
        f"Today's NAV ({fmt_date(s.today)}): {inr(s.current_nav, 2)}",
        f"Today's NAV is {inr(s.nav_drop, 2)} ({abs(s.nav_drop_pct):.2f}%) "
        f"{'below' if s.nav_drop > 0 else 'above'} the average buy NAV",
        f"Current value: {inr(s.current_value)} (exact {inr(s.current_value, 2)})",
        f"Current value is {inr(s.gain)} {status} the amount invested "
        f"(absolute return {signed_pct(s.gain_pct, 2)}, about {signed_pct(s.gain_pct, 0)})",
        f"XIRR (annualised return): {signed_pct(s.xirr_pct, 1)} per year",
        "Each instalment:",
    ]
    for i in s.instalments:
        lines.append(f"  - {fmt_date(i.date)}: {inr(i.amount)} at NAV {i.nav:.2f} bought {i.units:.2f} units")
    return "\n".join(lines)


def allowed_numbers(s: SipSummary) -> list[float]:
    """Every magnitude an answer may quote. Signs are carried by words, so magnitudes only."""
    vals = [s.monthly_amount, s.invested, s.total_units, s.avg_nav, s.current_nav, s.current_value,
            abs(s.gain), abs(s.gain_pct), abs(s.xirr_pct), abs(s.nav_drop), abs(s.nav_drop_pct),
            float(s.n_instalments)]
    for i in s.instalments:
        vals += [i.amount, i.nav, i.units]
    return vals


def numbers_summary(s: SipSummary) -> list[tuple[str, str]]:
    """Plain numbers for fallbacks and the SIP screen (label, value)."""
    word = "Below invested by" if s.is_down else "Above invested by"
    return [
        ("Invested", inr(s.invested)),
        ("Current value", inr(s.current_value)),
        (word, f"{inr(s.gain)} ({signed_pct(s.gain_pct, 2)})"),
        ("Units", f"{s.total_units:.2f}"),
        ("Average buy NAV", inr(s.avg_nav, 2)),
        (f"Today's NAV ({fmt_date(s.today)})", inr(s.current_nav, 2)),
        ("XIRR", signed_pct(s.xirr_pct, 1)),
    ]


if __name__ == "__main__":
    print(facts_block(compute()))
