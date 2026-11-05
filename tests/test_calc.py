from datetime import date

import pytest

import calc


@pytest.fixture(scope="module")
def s():
    return calc.compute()


def test_invested(s):
    assert s.invested == 10000
    assert s.n_instalments == 5


def test_units(s):
    assert [round(i.units, 2) for i in s.instalments] == [83.33, 80.32, 81.30, 82.99, 84.21]
    assert s.total_units == pytest.approx(412.15, abs=0.01)


def test_avg_nav(s):
    assert s.avg_nav == pytest.approx(24.26, abs=0.005)


def test_value_and_loss(s):
    assert s.current_value == pytest.approx(9504.26, abs=0.01)
    assert s.gain == pytest.approx(-495.74, abs=0.01)
    assert s.gain_pct == pytest.approx(-4.96, abs=0.005)
    assert s.is_down


def test_xirr_is_computed(s):
    assert s.xirr_pct == pytest.approx(-18.5, abs=0.05)


def test_xirr_known_case():
    # 1000 out, 1100 back exactly one year later = +10%
    r = calc.xirr([(date(2025, 1, 1), -1000), (date(2026, 1, 1), 1100)])
    assert r == pytest.approx(0.10, abs=1e-6)


def test_formatting():
    assert calc.inr(9504.26) == "₹9,504"
    assert calc.inr(123456.7) == "₹1,23,457"
    assert calc.inr(24.2628, 2) == "₹24.26"
    assert calc.signed_pct(-18.472) == "−18.5%"


def test_facts_block_has_key_numbers(s):
    fb = calc.facts_block(s)
    for token in ["₹10,000", "412.15", "₹24.26", "₹23.06", "₹9,504", "₹496", "−18.5%"]:
        assert token in fb
