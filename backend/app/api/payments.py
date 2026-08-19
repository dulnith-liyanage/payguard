from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Any
import os
import uuid
import json

from app.db import SessionLocal
from app.models import PaymentSubmission, Customer, Order, VerificationResult
from app.verification.cheap_checks import run_tier0_checks, CheapCheckInput, CheapCheckContext
from app.verification.ocr_service import run_ocr, OCRResult
from app.verification.sms_matcher import match_sms
from app.verification.decision_engine import evaluate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_payments(db: Session = Depends(get_db)) -> Any:
    """Get all payment submissions."""
    submissions = db.scalars(
        select(PaymentSubmission).order_by(PaymentSubmission.created_at.desc())
    ).all()
    
    results = []
    for sub in submissions:
        vr = db.scalar(select(VerificationResult).where(VerificationResult.payment_submission_id == sub.id))
        cust = db.scalar(select(Customer).where(Customer.id == sub.customer_id))
        results.append({
            "id": sub.id,
            "customer_name": cust.name if cust else "Unknown",
            "amount": sub.submitted_amount_lkr,
            "status": sub.status,
            "decision": vr.decision if vr else "PENDING",
            "created_at": sub.created_at
        })
    return results

@router.post("/upload")
async def upload_payment(
    order_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Any:
    """Handle a real-world payment slip upload and verify it."""
    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # 1. Read and save image
    image_bytes = await file.read()
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join("images", filename)
    os.makedirs("images", exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(image_bytes)
        
    image_url_path = f"/images/{filename}"
    
    # 2. Build Tier 0 Context
    existing_subs = db.scalars(select(PaymentSubmission)).all()
    known_sha256 = {sub.image_sha256 for sub in existing_subs if sub.image_sha256}
    known_phashes = {sub.image_phash: sub.id for sub in existing_subs if sub.image_phash}
    
    context = CheapCheckContext(known_sha256=known_sha256, known_phashes=known_phashes)
    check_input = CheapCheckInput(
        image_bytes=image_bytes,
        expected_amount_lkr=order.expected_amount_lkr,
        expected_account_no=order.business_account_no
    )
    
    # 3. Run Pipeline
    res0 = run_tier0_checks(check_input, context)
    
    if "EXACT_DUPLICATE" in res0.flags or "LOW_QUALITY_BLUR" in res0.flags or "LOW_QUALITY_DARK" in res0.flags:
        res1 = OCRResult("", None, None, None, False)
    else:
        res1 = run_ocr(image_bytes)
        
    res2 = match_sms(db, res1.extracted_amount, res1.extracted_reference)
    final_res = evaluate(
        res0,
        res1,
        res2,
        expected_amount=order.expected_amount_lkr,
        expected_account=order.business_account_no
    )
    
    # 4. Save to DB
    sub = PaymentSubmission(
        order_id=order_id,
        customer_id=order.customer_id,
        image_path=image_url_path,
        image_sha256=res0.sha256,
        image_phash=res0.phash,
        submitted_amount_lkr=res1.extracted_amount,
        submitted_account_no=res1.extracted_account_no,
        submitted_reference=res1.extracted_reference,
        status="PROCESSED"
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    duplicate_id = res0.near_duplicate_ids[0] if res0.near_duplicate_ids else None
    
    vr = VerificationResult(
        payment_submission_id=sub.id,
        decision=final_res.decision,
        internal_reason=final_res.internal_reason,
        customer_message=final_res.customer_message,
        confidence_score=final_res.confidence,
        evidence_json=json.dumps({"flags": final_res.flags, "duplicate_of": duplicate_id})
    )
    db.add(vr)
    db.commit()
    
    return {"status": "success", "payment_id": sub.id}

@router.get("/{payment_id}")
def get_payment_details(payment_id: int, db: Session = Depends(get_db)) -> Any:
    """Get full details of a submission."""
    sub = db.scalar(select(PaymentSubmission).where(PaymentSubmission.id == payment_id))
    if not sub:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    vr = db.scalar(select(VerificationResult).where(VerificationResult.payment_submission_id == sub.id))
    cust = db.scalar(select(Customer).where(Customer.id == sub.customer_id))
    order = db.scalar(select(Order).where(Order.id == sub.order_id))
    
    return {
        "id": sub.id,
        "image_path": sub.image_path,
        "customer": {
            "name": cust.name,
            "phone": cust.phone
        },
        "order": {
            "id": order.id,
            "expected_amount": order.expected_amount_lkr,
            "expected_account": order.business_account_no
        },
        "submitted": {
            "amount": sub.submitted_amount_lkr,
            "account_no": sub.submitted_account_no,
            "reference": sub.submitted_reference,
            "date": sub.submitted_paid_at
        },
        "verification": {
            "decision": vr.decision if vr else "PENDING",
            "internal_reason": vr.internal_reason if vr else "",
            "customer_message": vr.customer_message if vr else "",
            "confidence_score": vr.confidence_score if vr else 0.0,
            "evidence_json": vr.evidence_json if vr else "{}"
        }
    }
