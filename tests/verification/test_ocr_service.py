from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from app.verification.ocr_service import run_ocr
import os

def _create_slip(text: str) -> bytes:
    img = Image.new('RGB', (800, 300), color='white')
    draw = ImageDraw.Draw(img)
    # Try system font if available for crisp text rendering
    font = None
    for font_path in ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf", "/System/Library/Fonts/SFNSMono.ttf"]:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, 28)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    draw.text((40, 40), text, fill='black', font=font)
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def test_ocr_extracts_amount_and_reference():
    img_bytes = _create_slip("Payment Receipt\nTotal Amount: 25,000.00\nAccount: 100200300\nRef: 839201")
    result = run_ocr(img_bytes)
    assert result.is_readable is True
    assert result.extracted_amount == Decimal("25000.00")
    assert result.extracted_account_no == "100200300"
    assert result.extracted_reference == "839201"

def test_ocr_extracts_hyphenated_account():
    img_bytes = _create_slip("Successful Transfer\nAccount: 000-0000-000\nReference: TXN998877\nTotal Amount 19.00")
    result = run_ocr(img_bytes)
    assert result.is_readable is True
    assert result.extracted_amount == Decimal("19.00")
    assert result.extracted_account_no == "000-0000-000"
    assert result.extracted_reference == "TXN998877"

def test_ocr_handles_blank_image():
    img = Image.new('RGB', (100, 100), color='white')
    buf = BytesIO()
    img.save(buf, format='PNG')
    result = run_ocr(buf.getvalue())
    assert result.is_readable is False
    assert result.extracted_amount is None
