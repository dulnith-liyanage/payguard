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
    c1 = Customer(id=1, name="John Doe", phone="+94771234567")
    c2 = Customer(id=2, name="Jane Smith", phone="+94779876543")
    c3 = Customer(id=3, name="Fraudster", phone="+94770000000")
    db.add_all([c1, c2, c3])
    db.commit()

    now = datetime.now(timezone.utc)

    # 2. Base Orders (1 through 7 mapping 1-to-1 with demo test cases)
    o1 = Order(id=1, customer_id=c1.id, expected_amount_lkr=Decimal("25000.00"), external_order_id="ORD-1", business_account_no="100200300")
    o2 = Order(id=2, customer_id=c2.id, expected_amount_lkr=Decimal("15000.00"), external_order_id="ORD-2", business_account_no="100200300")
    o3 = Order(id=3, customer_id=c3.id, expected_amount_lkr=Decimal("25000.00"), external_order_id="ORD-3", business_account_no="100200300")
    o4 = Order(id=4, customer_id=c1.id, expected_amount_lkr=Decimal("25000.00"), external_order_id="ORD-4", business_account_no="100200300")
    o5 = Order(id=5, customer_id=c1.id, expected_amount_lkr=Decimal("25000.00"), external_order_id="ORD-5", business_account_no="100200300")
    o6 = Order(id=6, customer_id=c2.id, expected_amount_lkr=Decimal("5000.00"), external_order_id="ORD-6", business_account_no="100200300")
    o7 = Order(id=7, customer_id=c2.id, expected_amount_lkr=Decimal("5000.00"), external_order_id="ORD-7", business_account_no="100200300")
    db.add_all([o1, o2, o3, o4, o5, o6, o7])
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
    db.add_all([sms1, sms2])
    db.commit()

    # 4. Optional Pre-seeded Submission Examples
    if with_examples:
        p1 = PaymentSubmission(
            order_id=o1.id,
            customer_id=c1.id,
            image_path="/images/1_valid_payment.jpg",
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
            SMSMatchResult(sms1.id, True, 1.0, None),
            expected_amount=o1.expected_amount_lkr,
            expected_account=o1.business_account_no
        )
        vr1 = VerificationResult(
            payment_submission_id=p1.id, decision=res1.decision, internal_reason=res1.internal_reason, 
            customer_message=res1.customer_message, confidence_score=res1.confidence, evidence_json=json.dumps({"flags": res1.flags})
        )
        db.add(vr1)
        db.commit()

    db.close()
    if with_examples:
        print("Database seeded with demo submission examples.")
    else:
        print("Database initialized clean (Orders 1-7 ready, 0 submissions).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-examples", action="store_true", help="Seed with mock payment submission history")
    args = parser.parse_args()
    seed_db(with_examples=args.with_examples)
