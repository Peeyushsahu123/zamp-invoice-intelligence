"""Invoice upload and processing endpoints."""
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database import get_db
from app import config
from app.models import Invoice, ProcessingRun, RunStatus, Settings
from app.schemas import UploadResponse
from app.services.extraction import extract_invoice
from app.services.validation import run_all_validations
from app.services.matching import find_matching_po
from app.services.decision import make_decision

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _get_settings(db: Session) -> dict:
    """Load settings as a dict."""
    settings = db.query(Settings).all()
    return {s.key: s.value for s in settings}


def _update_stage(run: ProcessingRun, name: str, status: str, details: str | None = None):
    """Update a stage in the run's stages list."""
    now = datetime.now(timezone.utc).isoformat()
    stages = [dict(s) for s in (run.stages or [])]

    # Check if stage already exists
    found = False
    for s in stages:
        if s["name"] == name:
            s["status"] = status
            if status in ("completed", "failed"):
                s["completed_at"] = now
            if details:
                s["details"] = details
            found = True
            break

    if not found:
        stage = {"name": name, "status": status, "started_at": now}
        if status in ("completed", "failed"):
            stage["completed_at"] = now
        if details:
            stage["details"] = details
        stages.append(stage)

    run.stages = stages
    flag_modified(run, "stages")


def _process_invoice(file_path: str, db: Session) -> dict:
    """Core processing pipeline - runs extraction, validation, matching, decision."""
    # Create invoice record
    invoice = Invoice(file_path=file_path)
    db.add(invoice)
    db.flush()

    # Create processing run
    run = ProcessingRun(
        invoice_id=invoice.id,
        status=RunStatus.PENDING,
        stages=[],
    )
    db.add(run)
    db.flush()

    try:
        # Stage 1: Extraction
        _update_stage(run, "Document Upload", "completed", "PDF received and validated")
        run.status = RunStatus.EXTRACTING
        _update_stage(run, "Text Extraction", "running")
        db.commit()

        extracted = extract_invoice(file_path)
        extraction_method = extracted.pop("extraction_method", "fallback_parser")
        run.extraction_method = extraction_method
        run.extracted_data = extracted

        # Update invoice record with extracted data
        invoice.invoice_number = extracted.get("invoice_number")
        invoice.vendor_name = extracted.get("vendor_name")
        invoice.vendor_tax_id = extracted.get("vendor_tax_id")
        invoice.po_reference = extracted.get("po_reference")
        invoice.invoice_date = extracted.get("invoice_date")
        invoice.currency = extracted.get("currency", "USD")
        invoice.subtotal = extracted.get("subtotal")
        invoice.tax_amount = extracted.get("tax_amount")
        invoice.total_amount = extracted.get("total_amount")
        invoice.line_items = extracted.get("line_items")

        method_label = "AI (LLM)" if "llm" in extraction_method else "Pattern Parser (Fallback)"
        _update_stage(run, "Text Extraction", "completed", f"Extracted via {method_label}")

        # Stage 2: Matching
        run.status = RunStatus.MATCHING
        _update_stage(run, "PO Matching", "running")
        db.commit()

        match_result = find_matching_po(
            extracted.get("po_reference"),
            extracted.get("vendor_name"),
            db,
        )
        if match_result.matched:
            run.matched_po_id = match_result.po_id
            _update_stage(run, "PO Matching", "completed",
                         f"Matched {match_result.po.po_number} (confidence: {match_result.confidence})")
        else:
            issues_str = "; ".join(match_result.issues) if match_result.issues else "No PO reference"
            _update_stage(run, "PO Matching", "completed", f"No match: {issues_str}")

        # Stage 3: Validation
        run.status = RunStatus.VALIDATING
        _update_stage(run, "Validation", "running")
        db.commit()

        settings = _get_settings(db)
        validation_results = run_all_validations(
            extracted,
            db,
            settings,
            po_id=match_result.po_id,
            po_amount=match_result.po_amount,
            current_invoice_id=invoice.id,
        )
        run.validation_results = [v.to_dict() for v in validation_results]

        passed = sum(1 for v in validation_results if v.passed)
        total = len(validation_results)
        _update_stage(run, "Validation", "completed", f"{passed}/{total} checks passed")

        # Stage 4: Decision
        run.status = RunStatus.DECIDING
        _update_stage(run, "Decision", "running")
        db.commit()

        decision = make_decision(validation_results, extracted, match_result, settings)
        run.decision = decision.to_dict()

        _update_stage(run, "Decision", "completed", f"Result: {decision.status}")

        # Complete
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

        # Build response with matched PO info
        response = {
            "run_id": run.id,
            "id": run.id,
            "invoice_id": invoice.id,
            "status": run.status.value,
            "extraction_method": run.extraction_method,
            "stages": run.stages,
            "extracted_data": run.extracted_data,
            "validation_results": run.validation_results,
            "decision": run.decision,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        }

        if match_result.matched and match_result.po:
            po = match_result.po
            # Calculate committed amount
            from app.services.validation import validate_cumulative_po_balance
            committed = 0.0
            from app.models import ProcessingRun as PR, DecisionStatus
            approved_runs = (
                db.query(PR)
                .filter(PR.matched_po_id == po.id, PR.decision.isnot(None))
                .all()
            )
            for ar in approved_runs:
                if ar.decision and ar.decision.get("status") == DecisionStatus.APPROVED.value:
                    inv = db.query(Invoice).filter(Invoice.id == ar.invoice_id).first()
                    if inv and inv.total_amount:
                        committed += inv.total_amount

            response["matched_po"] = {
                "po_number": po.po_number,
                "vendor_name": po.vendor.name if po.vendor else None,
                "total_amount": po.total_amount,
                "committed_amount": committed,
                "remaining_amount": po.total_amount - committed,
                "status": po.status.value,
            }

        return response

    except Exception as e:
        _update_stage(run, run.status.value if run.status else "processing", "failed", str(e))
        run.status = RunStatus.FAILED
        run.error_message = str(e)
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise


@router.post("/upload", response_model=None)
async def upload_invoice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process an invoice PDF."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Save uploaded file
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = file.filename.replace(" ", "_")
    file_path = config.UPLOAD_DIR / f"{timestamp}_{safe_name}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        result = _process_invoice(str(file_path), db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/process-sample/{filename}")
def process_sample_invoice(filename: str, db: Session = Depends(get_db)):
    """Process a sample invoice by filename."""
    sample_path = config.SAMPLE_INVOICES_DIR / filename
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample invoice '{filename}' not found")

    # Copy to uploads
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest = config.UPLOAD_DIR / f"{timestamp}_{filename}"
    shutil.copy2(sample_path, dest)

    try:
        result = _process_invoice(str(dest), db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/samples")
def list_sample_invoices():
    """List available sample invoices."""
    if not config.SAMPLE_INVOICES_DIR.exists():
        return []

    samples_info = [
        {"filename": "invoice_normal.pdf", "label": "Normal Invoice (Acme)", "description": "Clean invoice within PO tolerance - APPROVED"},
        {"filename": "invoice_over_tolerance.pdf", "label": "Over Tolerance (TechParts)", "description": "Exceeds PO by >6% - REJECTED"},
        {"filename": "invoice_no_po.pdf", "label": "Missing PO (CloudServe)", "description": "No PO reference - REVIEW_REQUIRED"},
        {"filename": "invoice_duplicate.pdf", "label": "Duplicate Invoice", "description": "Same INV-2024-001 - REJECTED (after first processed)"},
        {"filename": "invoice_suspended_vendor.pdf", "label": "Suspended Vendor (QuickFix)", "description": "Vendor is suspended - REJECTED"},
        {"filename": "invoice_cumulative.pdf", "label": "Partial Invoice 1 (PO-004)", "description": "First partial - APPROVED"},
        {"filename": "invoice_cumulative_over.pdf", "label": "Partial Invoice 2 - Overbills", "description": "Cumulative exceeds PO - REJECTED"},
        {"filename": "invoice_bad_math.pdf", "label": "Arithmetic Error", "description": "Subtotal+tax != total - REVIEW_REQUIRED"},
    ]

    result = []
    for info in samples_info:
        if (config.SAMPLE_INVOICES_DIR / info["filename"]).exists():
            result.append(info)
    return result
