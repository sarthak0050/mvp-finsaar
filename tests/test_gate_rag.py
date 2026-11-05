import calc
import gate
import rag

S = calc.compute()
NUMS = calc.allowed_numbers(S)
SRC = ["Your SIP data", "K2 · Units", "K4 · Current value vs amount invested"]


def g(text, sources=("K2",), level="beginner", path="answer"):
    return gate.run_gate(text, list(sources), NUMS, SRC, level, path)


def test_good_english_answer_passes():
    r = g("You invested ₹10,000. Today your 412.15 units are worth ₹9,504, so the value is ₹496 "
          "below what you put in (−4.96%). Your XIRR is −18.5% a year.")
    assert r.passed, r.reasons


def test_good_hinglish_and_rounding_passes():
    r = g("Aapne ₹10,000 lagaye. Aaj value lagbhag ₹9,500 hai, yaani ₹496 kam. Aapke 412 units "
          "abhi bhi aapke hain. NAV 23.06 hai. Started 5 Jun 2026, 5 months ago.")
    assert r.passed, r.reasons


def test_made_up_number_fails():
    r = g("Your value is ₹9,800 and XIRR is −12%.")
    assert not r.passed
    assert "Numbers match" in r.reasons[0]


def test_advice_fails_english_and_hinglish():
    assert not g("You should stay invested.").passed
    assert not g("Abhi SIP band kar do.").passed
    assert not g("Continue karo, sab theek hai.").passed


def test_prediction_fails_but_negated_ok():
    assert not g("Don't worry, it will recover soon.").passed
    assert g("No one can say whether it will recover.").passed


def test_fear_fails():
    assert not g("This is a huge loss, act now.").passed


def test_grounded():
    assert not g("Your units are yours.", sources=()).passed
    assert not g("Your units are yours.", sources=("K7",)).passed
    assert g("Your units are yours.", sources=("Your SIP data",)).passed


def test_length():
    long = " ".join(["word"] * 90)
    assert not g(long).passed
    assert g(long, level="basics").passed


def test_decline_needs_decision_line():
    assert not g("Pause stops instalments for a while.", path="decline").passed
    assert g("Pause stops instalments for a while. The decision is yours.", path="decline").passed


def test_keyword_retrieval():
    chunks = rag.load_chunks()
    assert len(chunks) == 11 and all(c.source for c in chunks)
    s = rag.keyword_scores("What does XIRR mean for my SIP?", chunks)
    assert chunks[max(range(len(s)), key=s.__getitem__)].id == "K5"
    s = rag.keyword_scores("Should I stop my SIP?", chunks)
    assert chunks[max(range(len(s)), key=s.__getitem__)].id == "K8"


def test_advice_negated_is_ok_but_real_advice_still_fails():
    assert g("I cannot tell you whether to continue your SIP. The decision is yours.").passed
    assert g("These options do not sell your existing units.").passed
    assert not g("I can't say for sure, but you should continue your SIP.").passed
    assert not g("Don't worry. You should stay invested.").passed
    assert not g("Main nahi bata sakta lekin SIP band kar do.").passed


def test_buy_more_units_is_description_not_advice():
    import pipeline
    assert pipeline.classify("Why did my 5 Oct 2026 instalment buy more units?") == "answer"
    assert pipeline.classify("Should I invest more?") == "decline"
    assert pipeline.classify("Kya main SIP band kar du?") == "decline"
    assert pipeline.classify("What will my SIP be worth next year?") == "uncertain"
    assert g("A lower NAV lets the same ₹2,000 buy more units.").passed
    assert not g("NAV is low, so invest more now.").passed
