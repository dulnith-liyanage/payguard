"""Payment submission model for uploaded slip evidence."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PaymentSubmission(Base):
    """Stores each user-submitted payment slip and extracted metadata."""

    __tablename__ = "payment_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    image_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    image_phash: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    submitted_amount_lkr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    submitted_account_no: Mapped[str | None] = mapped_column(String(32), nullable=True)
    submitted_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submitted_paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="RECEIVED", nullable=False)
    flags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="submissions")
    customer = relationship("Customer")
    verification_result = relationship(
        "VerificationResult", back_populates="payment_submission", uselist=False, cascade="all, delete-orphan"
    )
