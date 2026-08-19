"""Engine that combines all tier outputs to produce a final decision."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from app.verification.cheap_checks import CheapCheckResult
from app.verification.ocr_service import OCRResult
from app.verification.sms_matcher import SMSMatchResult


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
    sms: SMSMatchResult,
    expected_amount: Optional[Decimal] = None,
    expected_account: Optional[str] = None
) -> FinalDecision:
    """Evaluate all evidence across Tier 0, Tier 1, and Tier 2 to make an explainable decision."""
    flags = list(cheap.flags)

    # 1. Tier 0 & Hashing Rejections (Exact Duplicates & Near-Duplicates)
    if cheap.exact_duplicate:
        return FinalDecision(
            "REJECTED",
            "Exact duplicate image submitted.",
            "This payment appears to have already been used for another order. Please send the correct payment slip.",
            0.99,
            flags if "EXACT_DUPLICATE" in flags else flags + ["EXACT_DUPLICATE"]
        )

    if cheap.near_duplicate_ids or "NEAR_DUPLICATE_IMAGE" in flags:
        parent_id = cheap.near_duplicate_ids[0] if cheap.near_duplicate_ids else "historical"
        return FinalDecision(
            "REJECTED",
            f"Altered/cropped copy of a previously submitted payment slip (matches Submission #{parent_id}).",
            "This payment appears to have already been used for another order. Please send the correct payment slip.",
            0.95,
            flags if "NEAR_DUPLICATE_IMAGE" in flags else flags + ["NEAR_DUPLICATE_IMAGE"]
        )

    if cheap.old_payment:
        return FinalDecision(
            "REJECTED",
            "Payment is too old to be accepted (>30 days).",
            "This payment is too old to be accepted for a new order. Please provide a recent payment slip.",
            0.90,
            flags if "OLD_PAYMENT" in flags else flags + ["OLD_PAYMENT"]
        )

    # 2. Quality Filter (Unreadable / Pitch Dark)
    if cheap.quality.blurry or cheap.quality.too_dark or not ocr.is_readable:
        return FinalDecision(
            "NEEDS_VERIFICATION",
            "Image is blurry/dark or OCR could not read text.",
            "We couldn't clearly read the payment slip. Please send a clearer image of the complete slip.",
            0.10,
            flags + ["UNREADABLE_IMAGE"] if "UNREADABLE_IMAGE" not in flags else flags
        )

    # 3. Parameter Validation: Amount Mismatch
    # Check both cheap input flags and OCR extracted amount
    if cheap.amount_mismatch or (ocr.extracted_amount is not None and expected_amount is not None and ocr.extracted_amount != expected_amount):
        return FinalDecision(
            "REJECTED",
            f"Payment amount (Rs. {ocr.extracted_amount}) does not match expected order amount (Rs. {expected_amount}).",
            "The payment amount does not match your order. Please check the payment and send the correct slip.",
            0.95,
            flags if "AMOUNT_MISMATCH" in flags else flags + ["AMOUNT_MISMATCH"]
        )

    # 4. Parameter Validation: Account Mismatch
    if cheap.account_mismatch or (ocr.extracted_account_no is not None and expected_account is not None):
        clean_extracted = ocr.extracted_account_no.replace("-", "").replace(" ", "") if ocr.extracted_account_no else ""
        clean_expected = expected_account.replace("-", "").replace(" ", "") if expected_account else ""
        if clean_extracted and clean_expected and clean_extracted != clean_expected and not clean_extracted.endswith(clean_expected) and not clean_expected.endswith(clean_extracted):
            return FinalDecision(
                "REJECTED",
                f"Payment was made to account {ocr.extracted_account_no}, which does not belong to the business.",
                "The payment was made to an incorrect account. Please verify our bank details and send the correct slip.",
                0.95,
                flags if "ACCOUNT_MISMATCH" in flags else flags + ["ACCOUNT_MISMATCH"]
            )

    # 5. Reference Syntax Validation
    if cheap.suspicious_reference:
        return FinalDecision(
            "REJECTED",
            "Suspicious or malformed reference number.",
            "We could not verify this payment. Please verify your reference number and contact support.",
            0.85,
            flags if "SUSPICIOUS_REFERENCE" in flags else flags + ["SUSPICIOUS_REFERENCE"]
        )

    # 6. Tier 2: Bank SMS Evidence Correlation
    if sms.is_matched:
        if sms.confidence >= 0.8:
            return FinalDecision(
                "APPROVED",
                "SMS matched perfectly with amount and reference.",
                "Payment successfully verified! Your order is confirmed.",
                0.95,
                flags + ["SMS_VERIFIED"]
            )
        else:
            return FinalDecision(
                "NEEDS_VERIFICATION",
                f"SMS amount matched but reference had issues: {sms.mismatch_reason}",
                "We received a payment for this amount, but need to manually verify it belongs to your order. Please wait.",
                0.60,
                flags + ["PARTIAL_SMS_MATCH"]
            )

    # 7. No SMS Matched Yet (May be delayed by carrier)
    return FinalDecision(
        "NEEDS_VERIFICATION",
        "No matching SMS found yet. Payment might be delayed or evidence insufficient.",
        "The payment appears valid, but the transaction cannot currently be matched with a bank notification. Please wait.",
        0.40,
        flags + ["NO_SMS_MATCH"]
    )
