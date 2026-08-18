"""Bank SMS model used as secondary payment evidence."""

from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BankSMS(Base):
    """Represents bank credit SMS notifications received by the business."""

    __tablename__ = "bank_sms"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_amount_lkr: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True, index=True)
    parsed_reference: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    parsed_account_no: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    sender: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
