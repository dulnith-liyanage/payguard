"""Verification result model for final decision records."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class VerificationResult(Base):
    """Stores the output of the verification decision engine."""

    __tablename__ = "verification_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_submission_id: Mapped[int] = mapped_column(
        ForeignKey("payment_submissions.id"), nullable=False, unique=True, index=True
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    internal_reason: Mapped[str] = mapped_column(Text, nullable=False)
    customer_message: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    payment_submission = relationship("PaymentSubmission", back_populates="verification_result")
