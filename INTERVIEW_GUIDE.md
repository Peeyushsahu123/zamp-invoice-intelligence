# Interview Guide — Invoice Intelligence

## Architecture & Data Flow

### High-Level Flow
```
PDF Upload → Text Extraction → LLM/Fallback Extraction → PO Matching
           → Validation Engine (7 rules) → Decision Engine → Dashboard
```

### Key Architectural Decisions

1. **Modular Monolith, Not Microservices**
   - All logic in one FastAPI app for simplicity and interview clarity
   - Services are isolated in separate modules (extraction, validation, decision, matching)
   - Swapping AI providers requires changing only `ai_provider.py`

2. **Synchronous Processing Pipeline**
   - Invoice processing runs synchronously in the request handler
   - No background workers, message queues, or WebSockets needed
   - Each stage updates the database with real timestamps
   - Frontend polls `/api/runs/{id}` for progress (simple, reliable)

3. **SQLite Instead of PostgreSQL**
   - Zero configuration, file-based, portable
   - Perfect for demo and interview — no Docker required
   - Schema and queries are standard SQL, trivially migrated to Postgres

### Role of AI vs. Deterministic Rules

| Component | AI | Deterministic |
|-----------|-----|---------------|
| Text extraction from PDF | ✗ | ✓ (PyMuPDF) |
| Structured data extraction | ✓ (LLM) | ✓ (Regex fallback) |
| PO matching | ✗ | ✓ |
| Field validation | ✗ | ✓ |
| Financial checks | ✗ | ✓ |
| Final decision | ✗ | ✓ |

**Key Design Principle**: AI handles unstructured-to-structured conversion (the "messy" part). All financial decisions are deterministic — an LLM never decides whether to approve or reject an invoice. This is deliberate: financial controls must be auditable and predictable.

### Database Design

```
vendors (4 rows)
├── purchase_orders (5 rows)
│
invoices (created per upload)
├── processing_runs
│   ├── stages (JSON: timestamped pipeline stages)
│   ├── extracted_data (JSON: invoice fields)
│   ├── validation_results (JSON: rule outcomes)
│   ├── decision (JSON: final verdict)
│   └── matched_po_id (FK → purchase_orders)
│
├── validation_results (relational, per rule per run)
│
settings (key/value for configurable thresholds)
```

**Why JSON columns for stages/results?** These are event-sourced snapshots of a processing run. They're always read as a unit and never queried individually. JSON keeps the schema simple without losing data richness.

### Validation Logic

7 rules, each as a standalone function returning `ValidationOutcome(passed, message, severity)`:

| # | Rule | Severity on Failure | What It Checks |
|---|------|---------------------|----------------|
| 1 | Required Fields | Warning | invoice_number, vendor_name, total_amount present |
| 2 | Duplicate Detection | Critical | Same invoice# + vendor already exists with APPROVED decision |
| 3 | Vendor Verification | Critical (suspended), Warning (unknown) | Vendor in system and not suspended |
| 4 | PO Matching | Warning | PO reference exists and vendor matches |
| 5 | Arithmetic Check | Warning | subtotal + tax = total (within $0.01) |
| 6 | Amount Tolerance | Critical (>2× tolerance), Warning | Invoice total vs PO amount (default 2%) |
| 7 | Cumulative Balance | Critical | Sum of approved invoices against PO doesn't exceed limit |

**Decision precedence:**
1. Any critical failure → **REJECTED**
2. Any warning → **REVIEW_REQUIRED**
3. All pass → **APPROVED**

### Edge Cases

| Scenario | What Happens | Why It Matters |
|----------|--------------|----------------|
| Duplicate invoice | Detected by matching invoice# + vendor against approved runs | Prevents double payment |
| Over-tolerance amount | Invoice $26,510 vs PO $25,000 (6% over, tolerance is 2%) | Financial control |
| Missing PO reference | Flags for review, doesn't auto-reject | Legitimate invoices sometimes lack PO |
| Suspended vendor | Hard rejection regardless of amounts | Compliance requirement |
| Cumulative overbilling | Two invoices against $8,500 PO totaling $9,500 | Prevents split-billing fraud |
| Bad math | subtotal + tax ≠ total → review | Catches data entry or extraction errors |

### Technology Choices & Tradeoffs

| Choice | Why | Tradeoff |
|--------|-----|----------|
| FastAPI | Async-ready, auto-docs, Pydantic integration | Python ecosystem limits |
| SQLite | Zero-config, portable, demo-friendly | No concurrent writes at scale |
| Vanilla JS frontend | No Node.js dependency, instant startup | No component library, more manual code |
| PyMuPDF | Fast, reliable PDF text extraction | Not OCR-capable for scanned PDFs |
| Regex fallback | Works without API keys, deterministic | Only handles known invoice formats |
| Synchronous processing | Simple, reliable, debuggable | Would need async/workers for >100 concurrent users |

### Known Limitations

1. **No OCR**: Scanned/image PDFs require Tesseract (easy to add, not included)
2. **No authentication**: Real AP system needs role-based access
3. **No email ingestion**: Invoices arrive via upload only
4. **Single-thread processing**: Fine for demo, not for production load
5. **Frontend served by backend**: Production would use CDN/nginx
6. **Settings not per-PO**: Tolerance is global, not per-vendor/PO
7. **No approval workflow**: No "approve this review-required invoice" button

---

## Ten Likely Interview Questions & Answers

### Q1: Why did you choose deterministic rules over AI for the approval decision?

**A**: Financial controls must be auditable and predictable. If you ask "why was this invoice rejected?" the answer needs to be "because invoice total $26,510 exceeded PO amount $25,000 by 6.04%, which is above the 2% tolerance threshold." Not "the AI decided it looked risky." Every rejection has a traceable rule, configurable threshold, and specific data values. AI is great for extraction — understanding varied invoice formats — but not for compliance decisions.

### Q2: How does your system prevent duplicate payments?

**A**: The duplicate check queries for existing invoices with the same invoice number AND vendor name that have a processing run with an APPROVED or REVIEW_REQUIRED decision. This means: (a) you can re-upload a rejected invoice after fixing it, (b) same invoice number from different vendors isn't flagged, (c) only invoices that actually went through the pipeline count.

### Q3: Walk me through what happens when an invoice exceeds a PO's cumulative limit.

**A**: When two invoices are submitted against PO-2024-004 ($8,500): Invoice 1 for $4,950 is APPROVED. Invoice 2 for $3,960 would make cumulative total $8,910, exceeding $8,500 × 1.02 = $8,670. The `validate_cumulative_po_balance` function queries all APPROVED runs against that PO, sums their invoice totals, adds the new invoice, and compares against the PO limit + tolerance. It explicitly excludes the current invoice from the sum to avoid double-counting.

### Q4: What happens if the LLM API is unavailable?

**A**: The extraction service has a clear fallback chain: try LLM → if AIProviderUnavailable → use regex parser. The UI clearly shows which method was used ("🤖 AI Extracted" vs "📋 Pattern Parser"). The fallback handles our sample format reliably. In production, I'd add OCR as a middle tier and potentially cache LLM results.

### Q5: How would you scale this for 1000 invoices/day?

**A**: Three changes: (1) Replace SQLite with PostgreSQL for concurrent writes. (2) Add a background task queue (Celery/RQ) — currently synchronous, which works for demo but would timeout on slow LLM calls at scale. (3) Add a Redis cache for PO lookups and dashboard stats. The architecture already separates concerns, so these are infrastructure changes, not logic rewrites.

### Q6: Why didn't you use a framework like LangChain?

**A**: The AI integration here is a single LLM call with a structured prompt — no chains, agents, or retrieval needed. Adding LangChain would be a 200MB dependency for what amounts to 30 lines of HTTP code. The `AIProvider` class is ~150 lines, supports three providers, and is easy to understand in an interview. Framework overhead is justified when the problem is complex; here it would obscure a simple design.

### Q7: How do you handle vendor name matching across different invoice formats?

**A**: The PO matching service uses bidirectional substring matching: `vendor_name in po.vendor.name OR po.vendor.name in vendor_name`. This handles cases like "Acme" vs "Acme Office Supplies" or slight variations. In production, I'd add fuzzy matching (Levenshtein distance) and a vendor alias table. The current approach is reliable for known vendors while flagging edge cases for review.

### Q8: Explain your testing strategy.

**A**: Four test files covering different layers: (1) `test_validation.py` — unit tests for each of the 7 validation rules with isolated DB fixtures. (2) `test_extraction.py` — tests the fallback parser against generated PDFs. (3) `test_decision.py` — tests decision logic with synthetic validation outcomes. (4) `test_api.py` — integration tests using FastAPI TestClient with a fresh DB per test. Sample PDFs are generated programmatically (fpdf2), not checked into the repo.

### Q9: What's your confidence that this would work on invoices you haven't seen before?

**A**: With the LLM enabled, high confidence — the extraction prompt is detailed and GPT-4o handles varied invoice formats well. With the fallback parser alone, low confidence on novel formats but high confidence on our sample format. The architecture makes this explicitly visible: extraction method is displayed in the UI, and validation catches data quality issues regardless of extraction method. The honest answer is: AI extraction quality depends on the model, and the validation layer is the safety net.

### Q10: If you had another week, what would you add?

**A**: (1) **Approval workflow** — let reviewers approve REVIEW_REQUIRED invoices with comments. (2) **OCR integration** (Tesseract) for scanned PDFs. (3) **Email ingestion** — watch a mailbox, auto-process attachments. (4) **Vendor onboarding** — CRUD for vendors and POs through the UI. (5) **Audit log** — who approved what, when, with full decision history. These are all extensions of the existing architecture, not rewrites.
