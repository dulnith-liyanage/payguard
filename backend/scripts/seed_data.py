"""Seed database with test scenarios."""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db import engine, Base, SessionLocal
from app.models import Customer, Order, PaymentSubmission, BankSMS, VerificationResult
from app.verification.cheap_checks import CheapCheckResult, QualityMetrics
from app.verification.ocr_service import OCRResult
from app.verification.sms_matcher import SMSMatchResult
from app.verification.decision_engine import evaluate

def seed_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Create customers
    c1 = Customer(name="John Doe", phone="+94771234567")
    c2 = Customer(name="Jane Smith", phone="+94779876543")
    c3 = Customer(name="Fraudster", phone="+94770000000")
    db.add_all([c1, c2, c3])
    db.commit()

    now = datetime.utcnow()

    # Scenario 1: Valid Payment
    o1 = Order(customer_id=c1.id, expected_amount_lkr=Decimal("25000.00"), external_order_id="EXT1", business_account_no="100200300")
    db.add(o1)
    db.commit()
    
    sms1 = BankSMS(
        raw_text="Rs. 25,000 credited to A/C 100200300. Ref 839201.",
        parsed_amount_lkr=Decimal("25000.00"),
        parsed_reference="839201",
        parsed_account_no="100200300",
        received_at=now - timedelta(minutes=5),
        sender="Bank"
    )
    db.add(sms1)
    
    p1 = PaymentSubmission(
        order_id=o1.id,
        customer_id=c1.id,
        image_path="/images/slip1.jpg",
        image_sha256="hash1",
        image_phash="ffffffffffffffff",
        submitted_amount_lkr=Decimal("25000.00"),
        submitted_account_no="100200300",
        status="PROCESSED"
    )
    db.add(p1)
    db.commit()
    
    # Run evaluation
    res1 = evaluate(
        CheapCheckResult("hash1", "ffffffffffffffff", [], False, False, False, False, False, QualityMetrics(100, 100, False, False), []),
        OCRResult("Rs 25000 Ref 839201 A/C 100200300", Decimal("25000"), "100200300", "839201", True),
        SMSMatchResult(sms1.id, True, 1.0, None)
    )
    vr1 = VerificationResult(
        payment_submission_id=p1.id, decision=res1.decision, internal_reason=res1.internal_reason, 
        customer_message=res1.customer_message, confidence_score=res1.confidence, evidence_json=json.dumps({"flags": res1.flags})
    )
    db.add(vr1)

    # Scenario 2: Wrong Amount
    o2 = Order(customer_id=c2.id, expected_amount_lkr=Decimal("15000.00"), external_order_id="EXT2", business_account_no="100200300")
    db.add(o2)
    db.commit()
    
    p2 = PaymentSubmission(
        order_id=o2.id, customer_id=c2.id, image_path="/images/slip2.jpg", image_sha256="hash2", image_phash="eeeeeeeeeeeeeeee",
        submitted_amount_lkr=Decimal("10000.00"), submitted_account_no="100200300", status="PROCESSED"
    )
    db.add(p2)
    db.commit()
    
    res2 = evaluate(
        CheapCheckResult("hash2", "eeeeeeeeeeeeeeee", [], False, False, True, False, False, QualityMetrics(100, 100, False, False), ["AMOUNT_MISMATCH"]),
        OCRResult("Rs 10000 Ref 111111 A/C 100200300", Decimal("10000"), "100200300", "111111", True),
        SMSMatchResult(None, False, 0.0, "No SMS")
    )
    vr2 = VerificationResult(
        payment_submission_id=p2.id, decision=res2.decision, internal_reason=res2.internal_reason,
        customer_message=res2.customer_message, confidence_score=res2.confidence, evidence_json=json.dumps({"flags": res2.flags})
    )
    db.add(vr2)

    # Scenario 3: Duplicate Payment
    o3 = Order(customer_id=c3.id, expected_amount_lkr=Decimal("25000.00"), external_order_id="EXT3", business_account_no="100200300")
    db.add(o3)
    db.commit()
    
    p3 = PaymentSubmission(
        order_id=o3.id, customer_id=c3.id, image_path="/images/slip1_copy.jpg", image_sha256="hash1", image_phash="ffffffffffffffff",
        submitted_amount_lkr=Decimal("25000.00"), submitted_account_no="100200300", status="PROCESSED"
    )
    db.add(p3)
    db.commit()
    
    res3 = evaluate(
        CheapCheckResult("hash1", "ffffffffffffffff", [p1.id], True, False, False, False, False, QualityMetrics(100, 100, False, False), ["EXACT_DUPLICATE"]),
        OCRResult("Rs 25000 Ref 839201", Decimal("25000"), None, "839201", True),
        SMSMatchResult(sms1.id, True, 1.0, None)
    )
    vr3 = VerificationResult(
        payment_submission_id=p3.id, decision=res3.decision, internal_reason=res3.internal_reason,
        customer_message=res3.customer_message, confidence_score=res3.confidence, evidence_json=json.dumps({"flags": res3.flags, "duplicate_of": p1.id})
    )
    db.add(vr3)
    
    # Scenario 4: Unclear slip
    o4 = Order(customer_id=c2.id, expected_amount_lkr=Decimal("5000.00"), external_order_id="EXT4", business_account_no="100200300")
    db.add(o4)
    db.commit()
    
    p4 = PaymentSubmission(
        order_id=o4.id, customer_id=c2.id, image_path="/images/blurry.jpg", image_sha256="hash4", image_phash="dddddddddddddddd",
        submitted_amount_lkr=Decimal("5000.00"), submitted_account_no="100200300", status="PROCESSED"
    )
    db.add(p4)
    db.commit()
    
    res4 = evaluate(
        CheapCheckResult("hash4", "dddddddddddddddd", [], False, False, False, False, False, QualityMetrics(20, 10, True, True), ["LOW_QUALITY_BLUR"]),
        OCRResult("", None, None, None, False),
        SMSMatchResult(None, False, 0.0, "No SMS")
    )
    vr4 = VerificationResult(
        payment_submission_id=p4.id, decision=res4.decision, internal_reason=res4.internal_reason,
        customer_message=res4.customer_message, confidence_score=res4.confidence, evidence_json=json.dumps({"flags": res4.flags})
    )
    db.add(vr4)

    db.commit()
    db.close()
    print("Database seeded.")

if __name__ == "__main__":
    seed_db()
