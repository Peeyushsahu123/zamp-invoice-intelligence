"""Decision engine – produces a final decision based on validation results."""
from dataclasses import dataclass, field, asdict
from app.models import DecisionStatus
from app.services.validation import ValidationOutcome
from app.services.matching import MatchResult


@dataclass
class Decision:
    status: str  # DecisionStatus value
    explanation: str
    validation_outcomes: list[dict] = field(default_factory=list)
    invoice_values: dict = field(default_factory=dict)
    po_values: dict = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    recommended_action: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def make_decision(
    validation_results: list[ValidationOutcome],
    extracted_data: dict,
    match_result: MatchResult,
    settings: dict,
) -> Decision:
    """Produce a decision based on validation outcomes.

    Decision precedence:
    1. If any CRITICAL validation failed -> REJECTED
    2. If any WARNING validation failed -> REVIEW_REQUIRED
    3. If all pass -> APPROVED
    """
    critical_failures: list[str] = []
    warnings: list[str] = []
    all_outcomes = [v.to_dict() for v in validation_results]

    for v in validation_results:
        if not v.passed:
            if v.severity == "critical":
                critical_failures.append(v.message)
            else:
                warnings.append(v.message)

    # Build invoice/PO value summaries
    invoice_values = {
        "invoice_number": extracted_data.get("invoice_number"),
        "vendor_name": extracted_data.get("vendor_name"),
        "subtotal": extracted_data.get("subtotal"),
        "tax_amount": extracted_data.get("tax_amount"),
        "total_amount": extracted_data.get("total_amount"),
        "po_reference": extracted_data.get("po_reference"),
    }
    po_values = match_result.to_dict() if match_result else {}

    # Decision logic
    if critical_failures:
        return Decision(
            status=DecisionStatus.REJECTED.value,
            explanation="Invoice rejected due to critical validation failures",
            validation_outcomes=all_outcomes,
            invoice_values=invoice_values,
            po_values=po_values,
            reasons=critical_failures,
            recommended_action="Review and resolve critical issues before resubmitting",
        )

    if warnings:
        return Decision(
            status=DecisionStatus.REVIEW_REQUIRED.value,
            explanation="Invoice requires manual review due to validation warnings",
            validation_outcomes=all_outcomes,
            invoice_values=invoice_values,
            po_values=po_values,
            reasons=warnings,
            recommended_action="Manual review recommended for flagged items",
        )

    return Decision(
        status=DecisionStatus.APPROVED.value,
        explanation="All validations passed – invoice approved for payment",
        validation_outcomes=all_outcomes,
        invoice_values=invoice_values,
        po_values=po_values,
        reasons=["All validation checks passed"],
        recommended_action="Proceed with payment processing",
    )
