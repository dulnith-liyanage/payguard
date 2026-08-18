"""Tier 1 OCR service using Tesseract."""
import re
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from io import BytesIO
from PIL import Image
import pytesseract
import logging

logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    raw_text: str
    extracted_amount: Decimal | None
    extracted_account_no: str | None
    extracted_reference: str | None
    is_readable: bool

def run_ocr(image_bytes: bytes) -> OCRResult:
    """Extract text from the payment slip and attempt to parse key fields."""
    try:
        image = Image.open(BytesIO(image_bytes))
        # Simple preprocessing to improve OCR accuracy
        image = image.convert('L')
        
        # Run Tesseract
        text = pytesseract.image_to_string(image)
        
        # Clean text
        text = text.replace('\n', ' ').strip()
        is_readable = len(text) > 10
        
        if not is_readable:
            return OCRResult(raw_text=text, extracted_amount=None, extracted_account_no=None, extracted_reference=None, is_readable=False)
            
        # Very basic regex heuristics for demo purposes
        # Amounts typically follow LKR, Rs, Rs., or just a number with commas and .00
        # Try to find "Total Amount" or "Total" specifically first
        amount = None
        total_match = re.search(r'(?:Total\s*Amount|Total)\s*(?:Rs\.?|LKR)?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
        if total_match:
            try:
                amount_str = total_match.group(1).replace(',', '')
                amount = Decimal(amount_str)
            except:
                pass
                
        if not amount:
            amount_match = re.search(r'(?:Rs\.?|LKR|Amount)\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
            if amount_match:
                try:
                    amount_str = amount_match.group(1).replace(',', '')
                    amount = Decimal(amount_str)
                except:
                    pass
                
        # Reference might be labeled "Ref", "Reference", etc.
        ref_match = re.search(r'(?:Ref|Reference|Txn|Transaction)(?:\s*No\.?|\s*ID)?[\s:]+([A-Za-z0-9]+)', text, re.IGNORECASE)
        reference = ref_match.group(1) if ref_match else None
        
        # Account number might be labeled A/C, Account
        acc_match = re.search(r'(?:A/C|Account)(?:\s*No\.?)?[\s:]*([0-9X*\-]{4,20})', text, re.IGNORECASE)

        account_no = acc_match.group(1) if acc_match else None

        return OCRResult(
            raw_text=text,
            extracted_amount=amount,
            extracted_account_no=account_no,
            extracted_reference=reference,
            is_readable=True
        )
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return OCRResult(raw_text="", extracted_amount=None, extracted_account_no=None, extracted_reference=None, is_readable=False)
