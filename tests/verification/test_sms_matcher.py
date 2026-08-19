from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models.bank_sms import BankSMS
from app.verification.sms_matcher import match_sms

def _create_test_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()

def test_sms_match_exact():
    db = _create_test_session()
    sms = BankSMS(
        raw_text="Credited Rs 25,000 Ref 839201",
        parsed_amount_lkr=Decimal("25000.00"),
        parsed_reference="839201",
        parsed_account_no="100200300",
        received_at=datetime.now(timezone.utc),
        sender="Bank"
    )
    db.add(sms)
    db.commit()

    result = match_sms(db, Decimal("25000.00"), "839201")
    assert result.is_matched is True
    assert result.confidence == 1.0
    assert result.matched_sms_id == sms.id

def test_sms_match_amount_only():
    db = _create_test_session()
    sms = BankSMS(
        raw_text="Credited Rs 15,000",
        parsed_amount_lkr=Decimal("15000.00"),
        parsed_reference=None,
        parsed_account_no="100200300",
        received_at=datetime.now(timezone.utc),
        sender="Bank"
    )
    db.add(sms)
    db.commit()

    result = match_sms(db, Decimal("15000.00"), "MISSING_REF")
    assert result.is_matched is True
    assert result.confidence == 0.6

def test_sms_no_match():
    db = _create_test_session()
    result = match_sms(db, Decimal("99999.00"), "NONEXISTENT")
    assert result.is_matched is False
    assert result.confidence == 0.0
