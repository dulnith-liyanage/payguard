"""Seed database with base customers, orders, and bank SMS (clean slate or with demo examples)."""
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db import engine, Base, SessionLocal
from app.models import Customer, Order, PaymentSubmission, BankSMS, VerificationResult
from app.verification.cheap_checks import CheapCheckResult, QualityMetrics
from app.verification.ocr_service import OCRResult
from app.verification.sms_matcher import SMSMatchResult
from app.verification.decision_engine import evaluate

def seed_db(with_examples: bool = False):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # 1. Base Customers
    c1 = Customer(name="John Doe", phone="+94771234567")
    c2 = Customer(name="Jane Smith", phone="+94779876543")
    c3 = Customer(name="Fraudster", phone="+94770000000")
    db.add_all([c1, c2, c3])
    db.commit()

    now = datetime.now(timezone.utc)

    # 2. Base Orders (Ready to receive real uploads)
    o1 = Order(customer_id=c1.id, expected_amount_lkr=Decimal("25000.00"), external_order_id="ORD-1", business_account_no="100200300")
    o2 = Order(customer_id=c2.id, expected_amount_lkr=Decimal("15000.00"), external_order_id="ORD-2", business_account_no="100200300")
    o3 = Order(customer_id=c3.id, expected_amount_lkr=Decimal("25000.00"), external_order_id="ORD-3", business_account_no="100200300")
    o4 = Order(customer_id=c2.id, expected_amount_lkr=Decimal("5000.00"), external_order_id="ORD-4", business_account_no="100200300")
    o5 = Order(customer_id=c1.id, expected_amount_lkr=Decimal("19.00"), external_order_id="ORD-5", business_account_no="000-0000-000")
    db.add_all([o1, o2, o3, o4, o5])
    db.commit()

    # 3. Base Bank SMS Notifications (Incoming ground truth evidence)
    sms1 = BankSMS(
        raw_text="Rs. 25,000 credited to A/C 100200300. Ref 839201.",
        parsed_amount_lkr=Decimal("25000.00"),
        parsed_reference="839201",
        parsed_account_no="100200300",
        received_at=now - timedelta(minutes=5),
        sender="Bank"
    )
    sms2 = BankSMS(
        raw_text="Rs. 15,000 credited to A/C 100200300. Ref 111111.",
        parsed_amount_lkr=Decimal("15000.00"),
        parsed_reference="111111",
        parsed_account_no="100200300",
        received_at=now - timedelta(minutes=10),
        sender="Bank"
    )
    sms3 = BankSMS(
        raw_text="Transfer 19.00 credited to A/C 000-0000-000 Ref 1436527485963.",
        parsed_amount_lkr=Decimal("19.00"),
        parsed_reference="1436527485963",
        parsed_account_no="000-0000-000",
        received_at=now - timedelta(minutes=2),
        sender="Bank"
    )
    db.add_all([sms1, sms2, sms3])
    db.commit()

    # 4. Optional Pre-seeded Submission Examples
    if with_examples:
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
    if with_examples:
        print("Database seeded with demo submission examples.")
    else:
        print("Database initialized clean (0 submissions). Ready for fresh uploads!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-examples", action="store_true", help="Seed with mock payment submission history")
    args = parser.parse_args()
    seed_db(with_examples=args.with_examples)
