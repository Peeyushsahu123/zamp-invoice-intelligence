"""Processing run history endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import desc

from app.database import get_db
from app.models import ProcessingRun, Invoice, PurchaseOrder, DecisionStatus

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("")
def list_runs(
    limit: int = Query(50, ge=1, le=200),
    search: str = Query("", description="Search by invoice number or vendor"),
    status: str = Query("", description="Filter by decision status"),
    db: Session = Depends(get_db),
):
    """List processing runs with optional filtering."""
    query = db.query(ProcessingRun).order_by(desc(ProcessingRun.created_at))

    if search:
        # Search in extracted_data JSON for invoice_number or vendor_name
        matching_invoice_ids = (
            db.query(Invoice.id)
            .filter(
                Invoice.invoice_number.ilike(f"%{search}%")
                | Invoice.vendor_name.ilike(f"%{search}%")
            )
            .all()
        )
        ids = [i[0] for i in matching_invoice_ids]
        if ids:
            query = query.filter(ProcessingRun.invoice_id.in_(ids))
        else:
            return {"runs": []}

    runs = query.limit(limit).all()

    result = []
    for r in runs:
        run_data = {
            "id": r.id,
            "invoice_id": r.invoice_id,
            "status": r.status.value if r.status else "unknown",
            "extraction_method": r.extraction_method,
            "extracted_data": r.extracted_data,
            "decision": r.decision,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }

        # Apply status filter
        if status and run_data.get("decision"):
            if run_data["decision"].get("status") != status:
                continue
        elif status and not run_data.get("decision"):
            continue

        result.append(run_data)

    return {"runs": result}


@router.get("/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    """Get full details of a processing run."""
    run = db.query(ProcessingRun).filter(ProcessingRun.id == run_id).first()
    if not run:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Run not found")

    result = {
        "id": run.id,
        "invoice_id": run.invoice_id,
        "status": run.status.value if run.status else "unknown",
        "extraction_method": run.extraction_method,
        "stages": run.stages,
        "extracted_data": run.extracted_data,
        "validation_results": run.validation_results,
        "decision": run.decision,
        "matched_po_id": run.matched_po_id,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "error_message": run.error_message,
    }

    # Add matched PO details
    if run.matched_po_id:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == run.matched_po_id).first()
        if po:
            # Calculate committed amount for this PO
            committed = 0.0
            approved_runs = (
                db.query(ProcessingRun)
                .filter(
                    ProcessingRun.matched_po_id == po.id,
                    ProcessingRun.decision.isnot(None),
                )
                .all()
            )
            for ar in approved_runs:
                if ar.decision and ar.decision.get("status") == DecisionStatus.APPROVED.value:
                    inv = db.query(Invoice).filter(Invoice.id == ar.invoice_id).first()
                    if inv and inv.total_amount:
                        committed += inv.total_amount

            result["matched_po"] = {
                "po_number": po.po_number,
                "vendor_name": po.vendor.name if po.vendor else None,
                "total_amount": po.total_amount,
                "committed_amount": committed,
                "remaining_amount": po.total_amount - committed,
                "status": po.status.value,
            }

    return result


@router.post("/{run_id}/manual-decision")
def manual_decision(run_id: int, payload: dict, db: Session = Depends(get_db)):
    """Allow an AP reviewer to manually verify and decide on a review-required run."""
    run = db.query(ProcessingRun).filter(ProcessingRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    new_status = payload.get("status", "APPROVED")
    notes = payload.get("notes", "Manually verified by AP Specialist")

    decision = dict(run.decision or {})
    decision["status"] = new_status
    decision["manual_override"] = True
    decision["manual_notes"] = notes
    decision["explanation"] = f"Manually verified: {notes}"
    decision["recommended_action"] = "Proceed with payment processing (Manual override)" if new_status == "APPROVED" else "Do not pay (Manual rejection)"
    run.decision = decision
    flag_modified(run, "decision")

    # Add stage to timeline
    from app.routes.invoices import _update_stage
    _update_stage(run, "Manual Verification", "completed", f"Status updated to {new_status}: {notes}")

    db.commit()
    return {"message": f"Run #{run_id} updated to {new_status}", "decision": run.decision}
