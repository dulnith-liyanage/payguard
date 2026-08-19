import os
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUTPUT_DIR = "/Users/dulnithliyanage/Academics/payguard/backend/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Find crisp TrueType font
FONT_TITLE = None
FONT_BODY = None
FONT_BOLD = None
for fp in ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Geneva.ttf"]:
    if os.path.exists(fp):
        try:
            FONT_TITLE = ImageFont.truetype(fp, 32)
            FONT_BOLD = ImageFont.truetype(fp, 26)
            FONT_BODY = ImageFont.truetype(fp, 22)
            break
        except Exception:
            pass

if FONT_TITLE is None:
    FONT_TITLE = ImageFont.load_default()
    FONT_BOLD = ImageFont.load_default()
    FONT_BODY = ImageFont.load_default()

def draw_commercial_bank(filename, amount_str="Rs. 25,000.00", account_str="100200300", ref_str="839201", payer="John Doe", crop_offset=0):
    w, h = 750, 520
    img = Image.new("RGB", (w, h), "#f8fafc")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (w - 20, h - 20)], fill="#ffffff", outline="#cbd5e1", width=2)
    draw.rectangle([(20, 20), (w - 20, 90)], fill="#1e3a8a")
    draw.text((40, 36), "COMMERCIAL BANK", fill="#ffffff", font=FONT_TITLE)
    draw.text((40, 110), "✓ TRANSFER SUCCESSFUL", fill="#16a34a", font=FONT_BOLD)
    draw.line([(40, 150), (w - 40, 150)], fill="#e2e8f0", width=2)
    
    rows = [
        ("Total Amount:", amount_str),
        ("Account No:", account_str),
        ("Reference No:", ref_str),
        ("Date & Time:", "2026-08-19 10:15:30"),
        ("Paid By:", payer),
    ]
    y = 175
    for label, val in rows:
        draw.text((45, y), label, fill="#64748b", font=FONT_BODY)
        draw.text((260, y), val, fill="#0f172a", font=FONT_BOLD if "Amount" in label or "Account" in label else FONT_BODY)
        y += 48
    draw.line([(40, y + 10), (w - 40, y + 10)], fill="#e2e8f0", width=1)
    draw.text((45, y + 22), "Official Bank E-Receipt • Retain for verification", fill="#94a3b8", font=FONT_BODY)

    if crop_offset > 0:
        cropped = img.crop((crop_offset, crop_offset, w - crop_offset, h - crop_offset))
        img = cropped.resize((w, h), Image.Resampling.BICUBIC)

    img.save(os.path.join(OUTPUT_DIR, filename), quality=98)

def draw_boc(filename, amount_str="Rs. 10,000.00", account_str="100200300", ref_str="111111", payer="Jane Smith"):
    w, h = 750, 520
    img = Image.new("RGB", (w, h), "#fefce8")
    draw = ImageDraw.Draw(img)
    # Left vertical color bar
    draw.rectangle([(20, 20), (70, h - 20)], fill="#ca8a04")
    draw.rectangle([(70, 20), (w - 20, h - 20)], fill="#ffffff", outline="#fde047", width=2)
    
    draw.text((100, 40), "BANK OF CEYLON (BOC)", fill="#854d0e", font=FONT_TITLE)
    draw.text((100, 90), "Transaction Confirmation Notice", fill="#713f12", font=FONT_BODY)
    draw.line([(100, 130), (w - 40, 130)], fill="#fde047", width=2)

    rows = [
        ("Total Amount:", amount_str),
        ("Account No:", account_str),
        ("Reference No:", ref_str),
        ("Date & Time:", "2026-08-19 09:30:00"),
        ("Customer:", payer),
    ]
    y = 155
    for label, val in rows:
        draw.text((100, y), label, fill="#a16207", font=FONT_BODY)
        draw.text((310, y), val, fill="#0f172a", font=FONT_BOLD if "Amount" in label or "Account" in label else FONT_BODY)
        y += 48
    draw.line([(100, y + 10), (w - 40, y + 10)], fill="#fde047", width=1)
    draw.text((100, y + 22), "Bank of Ceylon • Bankers to the Nation", fill="#a16207", font=FONT_BODY)
    img.save(os.path.join(OUTPUT_DIR, filename), quality=98)

def draw_hnb(filename, amount_str="Rs. 25,000.00", account_str="999888777", ref_str="223344", payer="Fraudster"):
    w, h = 750, 520
    img = Image.new("RGB", (w, h), "#ecfeff")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(30, 30), (w - 30, h - 30)], fill="#ffffff", outline="#06b6d4", width=3)
    draw.rectangle([(30, 30), (w - 30, 85)], fill="#0891b2")
    draw.text((50, 42), "HATTON NATIONAL BANK (HNB)", fill="#ffffff", font=FONT_TITLE)
    
    rows = [
        ("Total Amount:", amount_str),
        ("Account No:", account_str),
        ("Reference No:", ref_str),
        ("Date & Time:", "2026-08-19 11:20:15"),
        ("Remitter:", payer),
    ]
    y = 150
    for label, val in rows:
        draw.text((60, y), label, fill="#0e7490", font=FONT_BODY)
        draw.text((280, y), val, fill="#0f172a", font=FONT_BOLD if "Amount" in label or "Account" in label else FONT_BODY)
        y += 48
    img.save(os.path.join(OUTPUT_DIR, filename), quality=98)

def draw_peoples_bank(filename, amount_str="Rs. 5,000.00", account_str="100200300", ref_str="999999", blurry=True):
    w, h = 750, 520
    img = Image.new("RGB", (w, h), "#fff1f2")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(15, 15), (w - 15, h - 15)], fill="#ffffff", outline="#f43f5e", width=2)
    draw.rectangle([(15, 15), (w - 15, 80)], fill="#be123c")
    draw.text((35, 30), "PEOPLE'S BANK SRI LANKA", fill="#ffffff", font=FONT_TITLE)
    
    rows = [
        ("Total Amount:", amount_str),
        ("Account No:", account_str),
        ("Reference No:", ref_str),
        ("Date & Time:", "2026-08-19 08:45:00"),
    ]
    y = 150
    for label, val in rows:
        draw.text((45, y), label, fill="#9f1239", font=FONT_BODY)
        draw.text((260, y), val, fill="#0f172a", font=FONT_BOLD)
        y += 48

    if blurry:
        img = img.filter(ImageFilter.GaussianBlur(radius=8))

    img.save(os.path.join(OUTPUT_DIR, filename), quality=98)

def draw_sampath(filename, amount_str="Rs. 5,000.00", account_str="100200300", ref_str="554433", payer="Jane Smith"):
    w, h = 750, 520
    img = Image.new("RGB", (w, h), "#fff7ed")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(25, 25), (w - 25, h - 25)], fill="#ffffff", outline="#fb923c", width=2)
    draw.rectangle([(25, 25), (w - 25, 95)], fill="#ea580c")
    draw.text((45, 42), "SAMPATH BANK - VISHWA", fill="#ffffff", font=FONT_TITLE)
    draw.text((45, 115), "Funds Transfer Receipt", fill="#c2410c", font=FONT_BOLD)
    draw.line([(45, 150), (w - 45, 150)], fill="#fed7aa", width=2)

    rows = [
        ("Total Amount:", amount_str),
        ("Account No:", account_str),
        ("Reference No:", ref_str),
        ("Date & Time:", "2026-08-19 12:05:22"),
        ("Paid By:", payer),
    ]
    y = 175
    for label, val in rows:
        draw.text((50, y), label, fill="#9a3412", font=FONT_BODY)
        draw.text((270, y), val, fill="#0f172a", font=FONT_BOLD if "Amount" in label or "Account" in label else FONT_BODY)
        y += 48
    img.save(os.path.join(OUTPUT_DIR, filename), quality=98)

def generate_all():
    # 1. Valid Payment -> APPROVED
    draw_commercial_bank("1_valid_payment.jpg", amount_str="Rs. 25,000.00", account_str="100200300", ref_str="839201", payer="John Doe")
    draw_commercial_bank("slip1.jpg", amount_str="Rs. 25,000.00", account_str="100200300", ref_str="839201", payer="John Doe")

    # 2. Wrong Amount -> REJECTED (AMOUNT_MISMATCH)
    draw_boc("2_wrong_amount.jpg", amount_str="Rs. 10,000.00", account_str="100200300", ref_str="111111", payer="Jane Smith")
    draw_boc("slip2.jpg", amount_str="Rs. 10,000.00", account_str="100200300", ref_str="111111", payer="Jane Smith")

    # 3. Wrong Account -> REJECTED (ACCOUNT_MISMATCH)
    draw_hnb("3_wrong_account.jpg", amount_str="Rs. 25,000.00", account_str="999888777", ref_str="223344", payer="Fraudster")

    # 4. Duplicate Slip -> REJECTED (EXACT_DUPLICATE)
    shutil.copyfile(os.path.join(OUTPUT_DIR, "1_valid_payment.jpg"), os.path.join(OUTPUT_DIR, "4_duplicate_slip.jpg"))
    shutil.copyfile(os.path.join(OUTPUT_DIR, "1_valid_payment.jpg"), os.path.join(OUTPUT_DIR, "slip1_copy.jpg"))

    # 5. Reused / Cropped Slip -> REJECTED (NEAR_DUPLICATE_IMAGE)
    draw_commercial_bank("5_reused_cropped_slip.jpg", amount_str="Rs. 25,000.00", account_str="100200300", ref_str="839201", payer="John Doe", crop_offset=4)

    # 6. Unclear / Blurry Slip -> NEEDS_VERIFICATION (LOW_QUALITY_BLUR)
    draw_peoples_bank("6_unclear_blurry_slip.jpg", blurry=True)
    draw_peoples_bank("blurry.jpg", blurry=True)

    # 7. Missing Bank SMS -> NEEDS_VERIFICATION (NO_SMS_MATCH)
    draw_sampath("7_missing_bank_sms.jpg", amount_str="Rs. 5,000.00", account_str="100200300", ref_str="554433", payer="Jane Smith")

    print("Successfully generated all demo receipt templates with distinct visual bank branding!")

if __name__ == "__main__":
    generate_all()
