"""Vendor and Purchase Order endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Vendor, PurchaseOrder, ProcessingRun, Invoice, DecisionStatus

router = APIRouter(tags=["vendors"])


@router.get("/vendors")
def list_vendors(db: Session = Depends(get_db)):
    """List all vendors."""
    vendors = db.query(Vendor).order_by(Vendor.name).all()
    return [
        {
            "id": v.id,
            "name": v.name,
            "tax_id": v.tax_id,
            "status": v.status.value,
            "email": v.email,
            "address": v.address,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in vendors
    ]


@router.get("/purchase-orders")
def list_purchase_orders(db: Session = Depends(get_db)):
    """List all purchase orders with committed amounts."""
    pos = db.query(PurchaseOrder).order_by(PurchaseOrder.po_number).all()
    result = []
    for po in pos:
        # Calculate committed amount
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

        result.append({
            "id": po.id,
            "po_number": po.po_number,
            "vendor_id": po.vendor_id,
            "vendor_name": po.vendor.name if po.vendor else None,
            "description": po.description,
            "total_amount": po.total_amount,
            "currency": po.currency,
            "status": po.status.value,
            "tolerance_percent": po.tolerance_percent,
            "committed_amount": committed,
            "remaining_amount": po.total_amount - committed,
            "created_at": po.created_at.isoformat() if po.created_at else None,
        })
    return result
