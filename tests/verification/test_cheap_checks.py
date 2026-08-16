from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO

from PIL import Image

from app.verification.cheap_checks import (
    CheapCheckContext,
    CheapCheckInput,
    compute_phash,
    compute_sha256,
    run_tier0_checks,
)


def _make_slip_image(text_marker: str) -> bytes:
    image = Image.new("RGB", (320, 180), "white")
    pixels = image.load()
    for x in range(20, 300):
        for y in range(30, 150):
            if (x + y + len(text_marker)) % 9 == 0:
                pixels[x, y] = (20, 20, 20)
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _slightly_modified_image(image_bytes: bytes) -> bytes:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image.putpixel((10, 10), (210, 210, 210))
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_detects_exact_duplicate_by_sha256() -> None:
    image_bytes = _make_slip_image("839201")
    sha = compute_sha256(image_bytes)

    result = run_tier0_checks(
        CheapCheckInput(
            image_bytes=image_bytes,
            expected_amount_lkr=Decimal("25000.00"),
            expected_account_no="XXXX1234",
        ),
        CheapCheckContext(known_sha256={sha}, known_phashes={}),
    )

    assert result.exact_duplicate is True
    assert "EXACT_DUPLICATE" in result.flags


def test_detects_near_duplicate_by_phash() -> None:
    image_a = _make_slip_image("839201")
    image_b = _slightly_modified_image(image_a)

    phash_a = compute_phash(image_a)

    result = run_tier0_checks(
        CheapCheckInput(
            image_bytes=image_b,
            expected_amount_lkr=Decimal("25000.00"),
            expected_account_no="XXXX1234",
        ),
        CheapCheckContext(known_sha256=set(), known_phashes={phash_a: 101}),
        near_duplicate_threshold=3,
    )

    assert result.exact_duplicate is False
    assert 101 in result.near_duplicate_ids
    assert "NEAR_DUPLICATE_IMAGE" in result.flags


def test_flags_amount_account_and_old_payment_mismatch() -> None:
    image_bytes = _make_slip_image("112233")

    result = run_tier0_checks(
        CheapCheckInput(
            image_bytes=image_bytes,
            expected_amount_lkr=Decimal("25000.00"),
            expected_account_no="XXXX1234",
            submitted_amount_lkr=Decimal("24000.00"),
            submitted_account_no="XXXX9876",
            submitted_paid_at=datetime.now(timezone.utc) - timedelta(days=45),
        ),
        CheapCheckContext(),
        max_payment_age_days=30,
    )

    assert result.amount_mismatch is True
    assert result.account_mismatch is True
    assert result.old_payment is True
    assert "AMOUNT_MISMATCH" in result.flags
    assert "ACCOUNT_MISMATCH" in result.flags
    assert "OLD_PAYMENT" in result.flags
