# Demo Script — 5-Minute Live Demo

## Pre-Demo Setup

```bash
cd backend
python -m uvicorn app.main:app --port 8000
# Open http://localhost:8000 in Chrome
```

Ensure the database is fresh (delete `invoice_intelligence.db` if you want a clean demo).

---

## Demo Flow (5 minutes)

### Part 1: Dashboard Overview (30 seconds)

1. Open the app — show the **Dashboard** with zero metrics
2. Point out: "These are live counts from the database — not hardcoded numbers"
3. Show the **Vendors & POs** page — 4 vendors, 5 purchase orders
4. Note QuickFix is SUSPENDED

---

### Part 2: Happy Path — Normal Invoice (90 seconds)

1. Go to **Process Invoice**
2. Click **"Normal Invoice (Acme)"** from sample invoices
3. Watch the **Processing Stages** timeline light up in real-time:
   - ✅ Document Upload
   - ✅ Text Extraction → "Extracted via Pattern Parser (Fallback)"
   - ✅ PO Matching → "Matched PO-2024-001 (confidence: high)"
   - ✅ Validation → "7/7 checks passed"
   - ✅ Decision → "Result: APPROVED"
4. Show the **Extracted Invoice Data** panel:
   - "All fields extracted: INV-2024-001, Acme Office Supplies, $4,620 total"
   - Point out the extraction method badge
5. Show the **Validation Checklist** — all green checks
6. Show the **Matched PO** panel — PO-2024-001, $5,000, remaining balance
7. Show the **Decision Panel** — "APPROVED: All validations passed"
8. Return to **Dashboard** — metrics updated: 1 processed, 1 approved

---

### Part 3: Edge Case — Suspended Vendor (60 seconds)

1. Go to **Process Invoice**
2. Click **"Suspended Vendor (QuickFix)"**
3. Watch processing complete
4. Show the **Decision Panel** — RED, **REJECTED**
5. Show **Validation Checklist**:
   - ✅ Required fields
   - ❌ **Vendor Validation** — "QuickFix Maintenance is SUSPENDED" (critical)
   - ✅ PO matched (PO-2024-005)
6. Explain: "Even though the PO exists and amounts match, the vendor's suspended status is a critical failure — automatic rejection. This is a deterministic rule, not an AI judgment."

---

### Part 4: Edge Case — Cumulative Overbilling (90 seconds)

1. Click **"Partial Invoice 1 (PO-004)"** — TechParts, $4,950 against $8,500 PO
2. Show it's **APPROVED** — $4,950 is within the $8,500 PO limit
3. Now click **"Partial Invoice 2 - Overbills"** — TechParts, $3,960
4. Show it's **REJECTED**:
   - ❌ **Cumulative PO Balance** — "Cumulative total $8,910 exceeds PO limit $8,500"
5. Explain: "The system tracks how much has already been billed against each PO. The first invoice was approved and committed $4,950. Adding $3,960 would bring the total to $8,910, exceeding the $8,500 limit plus 2% tolerance ($8,670). This prevents split-billing fraud."
6. Show **Vendors & POs** page — PO-2024-004 now shows committed amount

---

### Part 5: History & Explainability (30 seconds)

1. Go to **Run History**
2. Show all 3 processed invoices with status badges
3. Click on the rejected cumulative invoice
4. Show full detail view: stages, extracted data, validation checklist, PO info, decision
5. "Every decision is fully traceable — you can see exactly which rule failed, what the actual values were, and what action to take."

---

## Key Points to Make During Demo

- **"This is actually running"** — not a mockup. Real PDF parsing, real database queries, real validation logic.
- **"AI extracts, rules decide"** — AI handles the messy part (understanding invoice formats), but financial decisions are deterministic and auditable.
- **"Every decision is explainable"** — specific rules, specific values, specific thresholds.
- **"Configurable thresholds"** — show the Settings page, change tolerance to 5%, re-run.
- **"Edge cases prove the system"** — duplicate detection, cumulative billing, vendor status — these are the scenarios where a real AP team makes Friday-afternoon mistakes.

---

## If Asked: Additional Edge Cases

Run these if the interviewer asks or time permits:

| Sample | What It Demonstrates |
|--------|---------------------|
| Over Tolerance | Invoice $26,510 vs PO $25,000 → REJECTED (6% > 2%) |
| Missing PO | No PO reference → REVIEW_REQUIRED (not rejected) |
| Arithmetic Error | subtotal+tax ≠ total → REVIEW_REQUIRED |
| Duplicate | Process normal invoice again → REJECTED (duplicate detected) |
