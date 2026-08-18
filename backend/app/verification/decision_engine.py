"""Engine that combines all tier outputs to produce a final decision."""
from dataclasses import dataclass
from app.verification.cheap_checks import CheapCheckResult
from app.verification.ocr_service import OCRResult
from app.verification.sms_matcher import SMSMatchResult
import json

@dataclass
class FinalDecision:
    decision: str  # "APPROVED", "REJECTED", "NEEDS_VERIFICATION"
    internal_reason: str
    customer_message: str
    confidence: float
    flags: list[str]

def evaluate(
    cheap: CheapCheckResult,
    ocr: OCRResult,
    sms: SMSMatchResult
) -> FinalDecision:
    """Evaluate all evidence to make a final decision."""
    flags = list(cheap.flags)
    
    # Tier 0 Rejections (Fraud/Quality)
    if cheap.exact_duplicate:
        return FinalDecision(
            "REJECTED",
            "Exact duplicate image submitted.",
            "This payment appears to have already been used for another order. Please send the correct payment slip.",
            0.99,
            flags
        )
        
    if cheap.account_mismatch:
        return FinalDecision(
            "REJECTED",
            "Payment sent to wrong account.",
            "The payment was made to an incorrect account. Please verify our account details.",
            0.95,
            flags
        )
        
    if cheap.amount_mismatch:
        return FinalDecision(
            "REJECTED",
            "Payment amount does not match expected order amount.",
            "The payment amount does not match your order. Please check the payment and send the correct slip.",
            0.95,
            flags
        )
        
    if cheap.old_payment:
        return FinalDecision(
            "REJECTED",
            "Payment is too old to be accepted.",
            "This payment is too old to be accepted for a new order. Please provide a recent payment slip.",
            0.9,
            flags
        )

    # If quality is so bad OCR can't run, ask for new image
    if cheap.quality.blurry or cheap.quality.too_dark or not ocr.is_readable:
        return FinalDecision(
            "NEEDS_VERIFICATION",
            "Image is blurry/dark or OCR could not read text.",
            "We couldn't clearly read the payment slip. Please send a clearer image of the complete slip.",
            0.1,
            flags + ["UNREADABLE_IMAGE"]
        )

    # Check OCR vs Expected
    if ocr.extracted_amount is not None and cheap.amount_mismatch is False:
        # OCR read an amount. It should match what the customer said they paid.
        # However, we rely more on the SMS match than just OCR for the final truth,
        # but if OCR is wildly off, we flag it.
        pass

    # Tier 2 - SMS Matching
    if sms.is_matched:
        # Confirmed payment!
        if sms.confidence >= 0.8:
            return FinalDecision(
                "APPROVED",
                "SMS matched perfectly with amount and reference.",
                "Payment successfully verified! Your order is confirmed.",
                0.95,
                flags + ["SMS_VERIFIED"]
            )
        else:
            # Matched amount but poor reference correlation
            return FinalDecision(
                "NEEDS_VERIFICATION",
                f"SMS amount matched but reference had issues: {sms.mismatch_reason}",
                "We received a payment for this amount, but need to manually verify it belongs to you. Please wait.",
                0.6,
                flags + ["PARTIAL_SMS_MATCH"]
            )
            
    # SMS not matched
    # It might just be delayed, or the OCR amount is wrong, or it's a fake slip
    if cheap.suspicious_reference:
        return FinalDecision(
            "REJECTED",
            "Suspicious reference and no matching SMS.",
            "We could not verify this payment. Please contact support.",
            0.8,
            flags + ["SUSPICIOUS_REFERENCE", "NO_SMS"]
        )

    return FinalDecision(
        "NEEDS_VERIFICATION",
        "No matching SMS found yet. Payment might be delayed or evidence insufficient.",
        "The payment appears valid, but the transaction cannot currently be matched with a bank notification. Please wait.",
        0.4,
        flags + ["NO_SMS_MATCH"]
    )
