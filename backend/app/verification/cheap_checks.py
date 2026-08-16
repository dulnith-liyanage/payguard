"""Tier 0 deterministic checks: hashes, image quality, and sanity rules.

Tier trigger policy:
- Tier 0 always runs first because it is low-cost (CPU-only, local).
- If Tier 0 finds exact duplicates, hard account mismatch, or severe quality failure,
  we can decide without OCR/AI.
- Only unresolved cases should proceed to Tier 1 OCR.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
import re

import imagehash
from PIL import Image, ImageFilter, ImageStat


@dataclass
class QualityMetrics:
    """Image quality metrics used to decide if OCR is likely to succeed."""

    brightness: float
    contrast: float
    blurry: bool
    too_dark: bool


@dataclass
class CheapCheckInput:
    """Inputs for deterministic payment sanity checks."""

    image_bytes: bytes
    expected_amount_lkr: Decimal
    expected_account_no: str
    submitted_amount_lkr: Decimal | None = None
    submitted_account_no: str | None = None
    submitted_reference: str | None = None
    submitted_paid_at: datetime | None = None


@dataclass
class CheapCheckContext:
    """Prior known hash values for duplicate detection."""

    known_sha256: set[str] = field(default_factory=set)
    known_phashes: dict[str, int] = field(default_factory=dict)


@dataclass
class CheapCheckResult:
    """Tier 0 outputs for downstream decisioning."""

    sha256: str
    phash: str
    near_duplicate_ids: list[int]
    exact_duplicate: bool
    account_mismatch: bool
    amount_mismatch: bool
    suspicious_reference: bool
    old_payment: bool
    quality: QualityMetrics
    flags: list[str]


def compute_sha256(image_bytes: bytes) -> str:
    """Compute exact content hash for strict dedupe."""
    return hashlib.sha256(image_bytes).hexdigest()


def compute_phash(image_bytes: bytes) -> str:
    """Compute perceptual hash to detect same transaction in altered screenshots."""
    with Image.open(BytesIO(image_bytes)) as image:
        return str(imagehash.phash(image))


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Compute Hamming distance between two hex-like perceptual hashes."""
    return imagehash.hex_to_hash(hash_a) - imagehash.hex_to_hash(hash_b)


def assess_quality(image_bytes: bytes) -> QualityMetrics:
    """Estimate quality cheaply using grayscale statistics and edge energy."""
    with Image.open(BytesIO(image_bytes)) as image:
        gray = image.convert("L")
        stat = ImageStat.Stat(gray)
        brightness = float(stat.mean[0])
        contrast = float(stat.stddev[0])

        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        edge_energy = float(edge_stat.mean[0])

    too_dark = brightness < 45.0
    blurry = edge_energy < 12.0 and contrast < 25.0
    return QualityMetrics(
        brightness=round(brightness, 2),
        contrast=round(contrast, 2),
        blurry=blurry,
        too_dark=too_dark,
    )


def run_tier0_checks(
    check_input: CheapCheckInput,
    context: CheapCheckContext,
    near_duplicate_threshold: int = 6,
    max_payment_age_days: int = 30,
) -> CheapCheckResult:
    """Run Tier 0 checks before OCR/AI escalation."""
    sha256 = compute_sha256(check_input.image_bytes)
    phash = compute_phash(check_input.image_bytes)
    quality = assess_quality(check_input.image_bytes)

    exact_duplicate = sha256 in context.known_sha256
    near_duplicate_ids = [
        submission_id
        for known_phash, submission_id in context.known_phashes.items()
        if hamming_distance(phash, known_phash) <= near_duplicate_threshold
    ]

    amount_mismatch = (
        check_input.submitted_amount_lkr is not None
        and check_input.submitted_amount_lkr != check_input.expected_amount_lkr
    )
    account_mismatch = (
        check_input.submitted_account_no is not None
        and check_input.submitted_account_no != check_input.expected_account_no
    )
    suspicious_reference = False
    if check_input.submitted_reference is not None:
        normalized_reference = check_input.submitted_reference.strip().replace(" ", "")
        suspicious_reference = not bool(re.fullmatch(r"[A-Za-z0-9]{4,20}", normalized_reference))

    old_payment = False
    if check_input.submitted_paid_at is not None:
        now = datetime.now(timezone.utc)
        paid_at = check_input.submitted_paid_at
        if paid_at.tzinfo is None:
            paid_at = paid_at.replace(tzinfo=timezone.utc)
        age_days = (now - paid_at).days
        old_payment = age_days > max_payment_age_days

    flags: list[str] = []
    if exact_duplicate:
        flags.append("EXACT_DUPLICATE")
    if near_duplicate_ids:
        flags.append("NEAR_DUPLICATE_IMAGE")
    if amount_mismatch:
        flags.append("AMOUNT_MISMATCH")
    if account_mismatch:
        flags.append("ACCOUNT_MISMATCH")
    if suspicious_reference:
        flags.append("SUSPICIOUS_REFERENCE")
    if old_payment:
        flags.append("OLD_PAYMENT")
    if quality.blurry:
        flags.append("LOW_QUALITY_BLUR")
    if quality.too_dark:
        flags.append("LOW_QUALITY_DARK")

    return CheapCheckResult(
        sha256=sha256,
        phash=phash,
        near_duplicate_ids=near_duplicate_ids,
        exact_duplicate=exact_duplicate,
        account_mismatch=account_mismatch,
        amount_mismatch=amount_mismatch,
        suspicious_reference=suspicious_reference,
        old_payment=old_payment,
        quality=quality,
        flags=flags,
    )
