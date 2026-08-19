from decimal import Decimal
from app.verification.cheap_checks import CheapCheckResult, QualityMetrics
from app.verification.ocr_service import OCRResult
from app.verification.sms_matcher import SMSMatchResult
from app.verification.decision_engine import evaluate

def test_decision_approved_on_valid_match():
    t0 = CheapCheckResult("sha", "phash", [], False, False, False, False, False, QualityMetrics(100, 100, False, False), [])
    t1 = OCRResult("Rs 25000 Ref 839201", Decimal("25000.00"), "100200300", "839201", True)
    t2 = SMSMatchResult(1, True, 1.0, None)

    res = evaluate(t0, t1, t2)
    assert res.decision == "APPROVED"
    assert res.confidence == 0.95

def test_decision_rejected_on_exact_duplicate():
    t0 = CheapCheckResult("sha", "phash", [1], True, False, False, False, False, QualityMetrics(100, 100, False, False), ["EXACT_DUPLICATE"])
    t1 = OCRResult("Rs 25000", Decimal("25000.00"), None, None, True)
    t2 = SMSMatchResult(1, True, 1.0, None)

    res = evaluate(t0, t1, t2)
    assert res.decision == "REJECTED"
    assert "duplicate" in res.internal_reason.lower()
    assert "EXACT_DUPLICATE" in res.flags

def test_decision_rejected_on_amount_mismatch():
    t0 = CheapCheckResult("sha", "phash", [], False, False, True, False, False, QualityMetrics(100, 100, False, False), ["AMOUNT_MISMATCH"])
    t1 = OCRResult("Rs 10000", Decimal("10000.00"), None, None, True)
    t2 = SMSMatchResult(None, False, 0.0, "No SMS")

    res = evaluate(t0, t1, t2)
    assert res.decision == "REJECTED"
    assert "AMOUNT_MISMATCH" in res.flags

def test_decision_needs_verification_on_blur():
    t0 = CheapCheckResult("sha", "phash", [], False, False, False, False, False, QualityMetrics(20, 5, True, False), ["LOW_QUALITY_BLUR"])
    t1 = OCRResult("", None, None, None, False)
    t2 = SMSMatchResult(None, False, 0.0, "No SMS")

    res = evaluate(t0, t1, t2)
    assert res.decision == "NEEDS_VERIFICATION"
    assert "LOW_QUALITY_BLUR" in res.flags

def test_decision_needs_verification_when_no_sms():
    t0 = CheapCheckResult("sha", "phash", [], False, False, False, False, False, QualityMetrics(100, 100, False, False), [])
    t1 = OCRResult("Rs 25000", Decimal("25000.00"), "100200300", "839201", True)
    t2 = SMSMatchResult(None, False, 0.0, "No matching SMS")

    res = evaluate(t0, t1, t2)
    assert res.decision == "NEEDS_VERIFICATION"
    assert "NO_SMS_MATCH" in res.flags
