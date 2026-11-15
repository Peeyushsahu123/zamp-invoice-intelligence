"""Validation engine – each rule returns a ValidationOutcome."""
from dataclasses import dataclass, field, asdict
from sqlalchemy.orm import Session

from app.models import Invoice, Vendor, PurchaseOrder, ProcessingRun, DecisionStatus, VendorStatus


@dataclass
class ValidationOutcome:
    rule_name: str
    passed: bool
    message: str
    details: dict = field(default_factory=dict)
    severity: str = "info"  # "critical", "warning", "info"

    def to_dict(self) -> dict:
        return asdict(self)


# ── Individual Validators ───────────────────────────────────────────────────

def validate_required_fields(extracted_data: dict) -> ValidationOutcome:
    """Check that essential fields are present."""
    required = ["invoice_number", "vendor_name", "total_amount"]
    missing = [f for f in required if not extracted_data.get(f)]

    if missing:
        return ValidationOutcome(
            rule_name="required_fields",
            passed=False,
            message=f"Missing required fields: {', '.join(missing)}",
            details={"missing_fields": missing},
            severity="warning",
        )
    return ValidationOutcome(
        rule_name="required_fields",
        passed=True,
        message="All required fields present",
    )


def validate_duplicate_invoice(invoice_number: str, vendor_name: str, db: Session) -> ValidationOutcome:
    """Check for duplicate invoice number from the same vendor."""
    if not invoice_number:
        return ValidationOutcome(
            rule_name="duplicate_check",
            passed=True,
            message="No invoice number to check for duplicates",
            severity="info",
        )

    # Look for existing APPROVED invoices with same number + vendor
    existing = (
        db.query(Invoice)
        .join(ProcessingRun, ProcessingRun.invoice_id == Invoice.id)
        .filter(
            Invoice.invoice_number == invoice_number,
            Invoice.vendor_name == vendor_name,
            ProcessingRun.decision.isnot(None),
        )
        .all()
    )

    # Check if any of the existing runs have a completed decision
    for inv in existing:
        for run in inv.processing_runs:
            if run.decision and run.decision.get("status") in [
                DecisionStatus.APPROVED.value,
                DecisionStatus.REVIEW_REQUIRED.value,
            ]:
                return ValidationOutcome(
                    rule_name="duplicate_check",
                    passed=False,
                    message=f"Duplicate invoice: {invoice_number} from {vendor_name} already exists",
                    details={"existing_invoice_id": inv.id},
                    severity="critical",
                )

    return ValidationOutcome(
        rule_name="duplicate_check",
        passed=True,
        message="No duplicate found",
    )


def validate_vendor(vendor_name: str, db: Session) -> ValidationOutcome:
    """Check vendor exists and is approved."""
    if not vendor_name:
        return ValidationOutcome(
            rule_name="vendor_validation",
            passed=False,
            message="No vendor name provided",
            severity="warning",
        )

    vendor = db.query(Vendor).filter(
        Vendor.name.ilike(f"%{vendor_name}%")
    ).first()

    if not vendor:
        return ValidationOutcome(
            rule_name="vendor_validation",
            passed=False,
            message=f"Vendor '{vendor_name}' not found in system",
            details={"vendor_name": vendor_name},
            severity="warning",
        )

    if vendor.status == VendorStatus.SUSPENDED:
        return ValidationOutcome(
            rule_name="vendor_validation",
            passed=False,
            message=f"Vendor '{vendor.name}' is SUSPENDED",
            details={"vendor_name": vendor.name, "vendor_status": vendor.status.value},
            severity="critical",
        )

    if vendor.status != VendorStatus.APPROVED:
        return ValidationOutcome(
            rule_name="vendor_validation",
            passed=False,
            message=f"Vendor '{vendor.name}' is not approved (status: {vendor.status.value})",
            details={"vendor_name": vendor.name, "vendor_status": vendor.status.value},
            severity="warning",
        )

    return ValidationOutcome(
        rule_name="vendor_validation",
        passed=True,
        message=f"Vendor '{vendor.name}' is approved",
        details={"vendor_name": vendor.name, "vendor_id": vendor.id},
    )


def validate_po_match(po_reference: str, vendor_name: str, db: Session) -> ValidationOutcome:
    """Check if PO reference exists and matches vendor."""
    if not po_reference:
        return ValidationOutcome(
            rule_name="po_match",
            passed=False,
            message="No PO reference provided",
            details={"po_reference": None},
            severity="warning",
        )

    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number == po_reference
    ).first()

    if not po:
        return ValidationOutcome(
            rule_name="po_match",
            passed=False,
            message=f"PO '{po_reference}' not found",
            details={"po_reference": po_reference},
            severity="warning",
        )

    # Verify vendor matches
    if vendor_name and not po.vendor.name.lower().startswith(vendor_name.lower()[:5]):
        # More lenient matching – check if either contains part of the other
        if (vendor_name.lower() not in po.vendor.name.lower()
                and po.vendor.name.lower() not in vendor_name.lower()):
            return ValidationOutcome(
                rule_name="po_match",
                passed=False,
                message=f"PO vendor mismatch: PO belongs to '{po.vendor.name}', invoice from '{vendor_name}'",
                details={"po_vendor": po.vendor.name, "invoice_vendor": vendor_name},
                severity="warning",
            )

    return ValidationOutcome(
        rule_name="po_match",
        passed=True,
        message=f"PO '{po_reference}' matched successfully",
        details={"po_id": po.id, "po_amount": po.total_amount},
    )


def validate_arithmetic(subtotal: float | None, tax: float | None, total: float | None, tolerance: float = 0.01) -> ValidationOutcome:
    """Check that subtotal + tax = total within tolerance."""
    if subtotal is None or tax is None or total is None:
        return ValidationOutcome(
            rule_name="arithmetic_check",
            passed=True,
            message="Insufficient data for arithmetic check",
            details={"subtotal": subtotal, "tax": tax, "total": total},
            severity="info",
        )

    expected_total = subtotal + tax
    diff = abs(expected_total - total)

    if diff <= tolerance:
        return ValidationOutcome(
            rule_name="arithmetic_check",
            passed=True,
            message=f"Arithmetic correct: {subtotal} + {tax} = {total}",
            details={"subtotal": subtotal, "tax": tax, "total": total, "expected": expected_total},
        )

    return ValidationOutcome(
        rule_name="arithmetic_check",
        passed=False,
        message=f"Arithmetic mismatch: {subtotal} + {tax} = {expected_total}, but total is {total} (diff: {diff:.2f})",
        details={"subtotal": subtotal, "tax": tax, "total": total, "expected": expected_total, "difference": diff},
        severity="warning",
    )


def validate_amount_tolerance(
    invoice_total: float | None,
    po_amount: float | None,
    tolerance_pct: float = 2.0,
) -> ValidationOutcome:
    """Check if invoice amount is within tolerance of PO amount."""
    if invoice_total is None or po_amount is None:
        return ValidationOutcome(
            rule_name="amount_tolerance",
            passed=True,
            message="Insufficient data for amount tolerance check",
            severity="info",
        )

    tolerance_amount = po_amount * (tolerance_pct / 100.0)
    diff = invoice_total - po_amount
    pct_diff = (diff / po_amount) * 100 if po_amount else 0

    if invoice_total <= po_amount + tolerance_amount:
        return ValidationOutcome(
            rule_name="amount_tolerance",
            passed=True,
            message=f"Invoice amount ${invoice_total:.2f} is within tolerance of PO amount ${po_amount:.2f}",
            details={
                "invoice_total": invoice_total,
                "po_amount": po_amount,
                "tolerance_pct": tolerance_pct,
                "difference": diff,
                "pct_difference": round(pct_diff, 2),
            },
        )

    # Check if it exceeds by more than 2x tolerance (critical)
    if diff > tolerance_amount * 2:
        severity = "critical"
    else:
        severity = "warning"

    return ValidationOutcome(
        rule_name="amount_tolerance",
        passed=False,
        message=f"Invoice amount ${invoice_total:.2f} exceeds PO amount ${po_amount:.2f} by {pct_diff:.1f}% (tolerance: {tolerance_pct}%)",
        details={
            "invoice_total": invoice_total,
            "po_amount": po_amount,
            "tolerance_pct": tolerance_pct,
            "difference": diff,
            "pct_difference": round(pct_diff, 2),
        },
        severity=severity,
    )


def validate_cumulative_po_balance(
    po_id: int,
    invoice_total: float,
    db: Session,
    current_invoice_id: int | None = None,
) -> ValidationOutcome:
    """Check if cumulative invoices against a PO exceed the PO amount.

    Only counts APPROVED invoices toward the committed total.
    Does NOT double-count the current invoice.
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        return ValidationOutcome(
            rule_name="cumulative_po_balance",
            passed=True,
            message="PO not found for balance check",
            severity="info",
        )

    # Sum totals of all APPROVED invoices against this PO (excluding current)
    approved_runs = (
        db.query(ProcessingRun)
        .join(Invoice, Invoice.id == ProcessingRun.invoice_id)
        .filter(
            ProcessingRun.matched_po_id == po_id,
            ProcessingRun.decision.isnot(None),
        )
        .all()
    )

    committed_total = 0.0
    for run in approved_runs:
        # Skip current invoice to avoid double-counting
        if current_invoice_id and run.invoice_id == current_invoice_id:
            continue
        if run.decision and run.decision.get("status") == DecisionStatus.APPROVED.value:
            inv = db.query(Invoice).filter(Invoice.id == run.invoice_id).first()
            if inv and inv.total_amount:
                committed_total += inv.total_amount

    remaining = po.total_amount - committed_total
    new_total = committed_total + invoice_total

    if new_total <= po.total_amount * (1 + po.tolerance_percent / 100.0):
        return ValidationOutcome(
            rule_name="cumulative_po_balance",
            passed=True,
            message=f"Cumulative total ${new_total:.2f} within PO limit ${po.total_amount:.2f} (remaining: ${remaining:.2f})",
            details={
                "po_amount": po.total_amount,
                "committed_total": committed_total,
                "invoice_total": invoice_total,
                "new_cumulative_total": new_total,
                "remaining_before": remaining,
            },
        )

    return ValidationOutcome(
        rule_name="cumulative_po_balance",
        passed=False,
        message=f"Cumulative overbilling: ${new_total:.2f} exceeds PO limit ${po.total_amount:.2f} (already committed: ${committed_total:.2f})",
        details={
            "po_amount": po.total_amount,
            "committed_total": committed_total,
            "invoice_total": invoice_total,
            "new_cumulative_total": new_total,
            "remaining_before": remaining,
        },
        severity="critical",
    )


def run_all_validations(
    extracted_data: dict,
    db: Session,
    settings: dict,
    po_id: int | None = None,
    po_amount: float | None = None,
    current_invoice_id: int | None = None,
) -> list[ValidationOutcome]:
    """Run all validation rules and return list of outcomes."""
    tolerance_pct = float(settings.get("tolerance_percent", 2.0))

    results: list[ValidationOutcome] = []

    # 1. Required fields
    results.append(validate_required_fields(extracted_data))

    # 2. Duplicate check
    results.append(validate_duplicate_invoice(
        extracted_data.get("invoice_number", ""),
        extracted_data.get("vendor_name", ""),
        db,
    ))

    # 3. Vendor validation
    results.append(validate_vendor(extracted_data.get("vendor_name", ""), db))

    # 4. PO match
    results.append(validate_po_match(
        extracted_data.get("po_reference", ""),
        extracted_data.get("vendor_name", ""),
        db,
    ))

    # 5. Arithmetic check
    results.append(validate_arithmetic(
        extracted_data.get("subtotal"),
        extracted_data.get("tax_amount"),
        extracted_data.get("total_amount"),
    ))

    # 6. Amount tolerance (if PO found)
    if po_amount is not None:
        results.append(validate_amount_tolerance(
            extracted_data.get("total_amount"),
            po_amount,
            tolerance_pct,
        ))

    # 7. Cumulative PO balance (if PO found)
    if po_id is not None and extracted_data.get("total_amount") is not None:
        results.append(validate_cumulative_po_balance(
            po_id,
            extracted_data["total_amount"],
            db,
            current_invoice_id=current_invoice_id,
        ))

    return results
