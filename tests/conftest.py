"""Common test fixtures for PayGuard."""
import pytest
from decimal import Decimal
from app.db import Base, engine, SessionLocal
from app.models import Customer, Order, BankSMS, PaymentSubmission, VerificationResult

@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Ensure at least one customer and order exists
        if not db.query(Customer).filter_by(id=1).first():
            c = Customer(id=1, name="Test Customer", phone="+94771234567")
            db.add(c)
            db.commit()
            
        if not db.query(Order).filter_by(id=1).first():
            o = Order(id=1, customer_id=1, expected_amount_lkr=Decimal("25000.00"), business_account_no="100200300", external_order_id="ORD-1")
            db.add(o)
            db.commit()
        yield
        # Clean up any submissions created during tests to avoid polluting the app DB
        db.query(VerificationResult).delete()
        db.query(PaymentSubmission).delete()
        db.commit()
    finally:
        db.close()
