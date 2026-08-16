# PayGuard Cost Analysis (Tiered Verification)

## Why tiered processing
PayGuard minimizes cost by resolving the highest-volume cases with deterministic rules before escalating.

## Tier triggers
1. **Tier 0 (deterministic, local CPU)**
   - Always runs first.
   - Performs exact hash dedupe, perceptual near-duplicate checks, image quality checks, and sanity checks against known order fields.
   - If decisive (e.g., exact duplicate, wrong account, obviously reused old slip), stop here.
2. **Tier 1 (OCR, low cost)**
   - Runs only when Tier 0 does not produce a decisive outcome.
   - Extracts amount/date/reference/account fields for structured comparison.
3. **Tier 2 (AI vision, expensive)**
   - Runs only for unresolved ambiguous cases: low OCR confidence, manipulation suspicion, or conflicting evidence.
   - Results should be cached by image hash to avoid repeat cost.

## Approximate cost per 1,000 submissions (prototype assumptions)
- Tier 0: ~100% of submissions, local CPU → **~$0 incremental API cost**
- Tier 1 OCR: assume 35% require OCR, local Tesseract → **~$0 API cost** (compute only)
- Tier 2 AI vision: assume 8% escalation at $0.012 per image equivalent → **~$0.96 / 1,000**

Estimated blended external API spend: **under $1 per 1,000 submissions** with aggressive caching.
