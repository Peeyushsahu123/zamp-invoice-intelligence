"""PO matching service."""
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.models import PurchaseOrder, Vendor, VendorStatus


@dataclass
class MatchResult:
    matched: bool
    po: PurchaseOrder | None = None
    po_id: int | None = None
    po_amount: float | None = None
    confidence: str = "none"  # "high", "low", "none"
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "matched": self.matched,
            "po_id": self.po_id,
            "po_number": self.po.po_number if self.po else None,
            "po_amount": self.po_amount,
            "confidence": self.confidence,
            "issues": self.issues,
        }


def find_matching_po(po_reference: str | None, vendor_name: str | None, db: Session) -> MatchResult:
    """Find a matching PO for the invoice.

    1. Search POs by po_reference
    2. If found, verify vendor matches
    3. Check vendor approval status
    4. Return match result with confidence
    """
    if not po_reference:
        return MatchResult(
            matched=False,
            confidence="none",
            issues=["No PO reference provided on invoice"],
        )

    # Search by PO number
    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number == po_reference
    ).first()

    if not po:
        return MatchResult(
            matched=False,
            confidence="none",
            issues=[f"PO '{po_reference}' not found in system"],
        )

    issues: list[str] = []
    confidence = "high"

    # Verify vendor matches
    if vendor_name:
        vendor_match = (
            vendor_name.lower() in po.vendor.name.lower()
            or po.vendor.name.lower() in vendor_name.lower()
        )
        if not vendor_match:
            issues.append(
                f"Vendor mismatch: invoice from '{vendor_name}', PO belongs to '{po.vendor.name}'"
            )
            confidence = "low"

    # Check vendor status
    if po.vendor.status == VendorStatus.SUSPENDED:
        issues.append(f"Vendor '{po.vendor.name}' is SUSPENDED")

    if po.vendor.status == VendorStatus.PENDING:
        issues.append(f"Vendor '{po.vendor.name}' is PENDING approval")
        confidence = "low"

    return MatchResult(
        matched=True,
        po=po,
        po_id=po.id,
        po_amount=po.total_amount,
        confidence=confidence,
        issues=issues,
    )
