"""Matcher to correlate OCR results with Bank SMS notifications."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.bank_sms import BankSMS

@dataclass
class SMSMatchResult:
    matched_sms_id: Optional[int]
    is_matched: bool
    confidence: float
    mismatch_reason: Optional[str]

def match_sms(db: Session, amount: Optional[Decimal], reference: Optional[str]) -> SMSMatchResult:
    """Attempt to find a matching SMS for the given payment."""
    if amount is None:
        return SMSMatchResult(None, False, 0.0, "No readable amount from slip")
        
    # We first try to find by exact amount and reference
    query = select(BankSMS).where(BankSMS.parsed_amount_lkr == amount)
    if reference:
        query = query.where(BankSMS.parsed_reference == reference)
        
    sms_candidates = db.scalars(query).all()
    
    if len(sms_candidates) == 1:
        return SMSMatchResult(sms_candidates[0].id, True, 1.0, None)
    
    if len(sms_candidates) > 1:
        return SMSMatchResult(sms_candidates[0].id, True, 0.8, "Multiple matching SMS for amount and reference")
        
    # Fallback to match just amount if reference is missing or didn't match
    if reference:
        query_amt_only = select(BankSMS).where(BankSMS.parsed_amount_lkr == amount)
        sms_candidates_amt = db.scalars(query_amt_only).all()
        if len(sms_candidates_amt) == 1:
            return SMSMatchResult(sms_candidates_amt[0].id, True, 0.6, "Matched amount but reference missing/mismatched")
        elif len(sms_candidates_amt) > 1:
            return SMSMatchResult(None, False, 0.2, "Multiple SMS with same amount, cannot distinguish without reference")
            
    return SMSMatchResult(None, False, 0.0, "No matching bank SMS found for this amount")
