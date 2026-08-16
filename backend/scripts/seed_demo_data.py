"""Seed realistic Sri Lankan payment verification demo data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.db import Base, SessionLocal, engine
from app.models import BankSMS, Customer, Order, PaymentSubmission

BUSINESS_ACCOUNT = "XXXX1234"


def seed() -> None:
    """Insert demo customers, orders, historical submissions, and bank SMS evidence."""
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        session.query(PaymentSubmission).delete()
        session.query(BankSMS).delete()
        session.query(Order).delete()
        session.query(Customer).delete()

        customers = [
            Customer(name="Kasun Perera", phone="+94771234567"),
            Customer(name="Nimali Fernando", phone="+94779876543"),
            Customer(name="Sahan Jayasinghe", phone="+94770111222"),
        ]
        session.add_all(customers)
        session.flush()

        orders = [
            Order(
                external_order_id="ORD-LK-1001",
                customer_id=customers[0].id,
                expected_amount_lkr=Decimal("25000.00"),
                business_account_no=BUSINESS_ACCOUNT,
            ),
            Order(
                external_order_id="ORD-LK-1002",
                customer_id=customers[1].id,
                expected_amount_lkr=Decimal("25000.00"),
                business_account_no=BUSINESS_ACCOUNT,
            ),
            Order(
                external_order_id="ORD-LK-1003",
                customer_id=customers[2].id,
                expected_amount_lkr=Decimal("12350.00"),
                business_account_no=BUSINESS_ACCOUNT,
            ),
        ]
        session.add_all(orders)
        session.flush()

        now = datetime.now(timezone.utc)

        session.add_all(
            [
                PaymentSubmission(
                    order_id=orders[0].id,
                    customer_id=customers[0].id,
                    image_path="samples/slips/slip_839201.png",
                    image_sha256="a" * 64,
                    image_phash="ff00ff00aa55aa55",
                    submitted_amount_lkr=Decimal("25000.00"),
                    submitted_account_no=BUSINESS_ACCOUNT,
                    submitted_reference="839201",
                    submitted_paid_at=now - timedelta(hours=3),
                    status="APPROVED",
                    flags_json="[]",
                ),
                PaymentSubmission(
                    order_id=orders[2].id,
                    customer_id=customers[2].id,
                    image_path="samples/slips/slip_old_112233.png",
                    image_sha256="b" * 64,
                    image_phash="aa00bb11cc22dd33",
                    submitted_amount_lkr=Decimal("12350.00"),
                    submitted_account_no=BUSINESS_ACCOUNT,
                    submitted_reference="112233",
                    submitted_paid_at=now - timedelta(days=60),
                    status="REJECTED",
                    flags_json='["OLD_PAYMENT"]',
                ),
            ]
        )

        session.add_all(
            [
                BankSMS(
                    raw_text="BOC: Rs. 25,000.00 credited to A/C XXXX1234 on 2026-08-16 10:20. Ref 839201.",
                    parsed_amount_lkr=Decimal("25000.00"),
                    parsed_reference="839201",
                    parsed_account_no=BUSINESS_ACCOUNT,
                    received_at=now - timedelta(hours=3),
                    sender="BOC",
                ),
                BankSMS(
                    raw_text="HNB ALERT: LKR 12,350.00 CR to XXXX1234 at 2026-06-15 09:10 Ref:112233",
                    parsed_amount_lkr=Decimal("12350.00"),
                    parsed_reference="112233",
                    parsed_account_no=BUSINESS_ACCOUNT,
                    received_at=now - timedelta(days=60),
                    sender="HNB",
                ),
                BankSMS(
                    raw_text="COMBANK: Rs. 25,000.00 credited to A/C XXXX9876. Ref 998877.",
                    parsed_amount_lkr=Decimal("25000.00"),
                    parsed_reference="998877",
                    parsed_account_no="XXXX9876",
                    received_at=now - timedelta(hours=1),
                    sender="COMBANK",
                ),
            ]
        )

        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    seed()
