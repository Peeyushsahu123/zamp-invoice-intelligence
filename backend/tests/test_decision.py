"""Tests for decision engine."""
import pytest
from app.services.validation import ValidationOutcome
from app.services.matching import MatchResult
from app.services.decision import make_decision
from app.models import DecisionStatus


class TestDecisionEngine:
    def _make_match(self, matched=True):
        return MatchResult(matched=matched, po_id=1, po_amount=5000.0)

    def test_all_pass_approved(self):
        results = [
            ValidationOutcome("required_fields", True, "All present"),
            ValidationOutcome("duplicate_check", True, "No duplicate"),
            ValidationOutcome("vendor_validation", True, "Vendor approved"),
            ValidationOutcome("po_match", True, "PO matched"),
            ValidationOutcome("arithmetic_check", True, "Math correct"),
            ValidationOutcome("amount_tolerance", True, "Within tolerance"),
        ]
        decision = make_decision(results, {"invoice_number": "INV-001", "total_amount": 4500}, self._make_match(), {})
        assert decision.status == DecisionStatus.APPROVED.value

    def test_critical_failure_rejected(self):
        results = [
            ValidationOutcome("required_fields", True, "OK"),
            ValidationOutcome("duplicate_check", False, "Duplicate found", severity="critical"),
        ]
        decision = make_decision(results, {"invoice_number": "INV-001"}, self._make_match(), {})
        assert decision.status == DecisionStatus.REJECTED.value
        assert "Duplicate" in decision.reasons[0]

    def test_warning_review_required(self):
        results = [
            ValidationOutcome("required_fields", True, "OK"),
            ValidationOutcome("po_match", False, "No PO found", severity="warning"),
        ]
        decision = make_decision(results, {"invoice_number": "INV-001"}, MatchResult(matched=False), {})
        assert decision.status == DecisionStatus.REVIEW_REQUIRED.value

    def test_suspended_vendor_rejected(self):
        results = [
            ValidationOutcome("vendor_validation", False, "Vendor suspended", severity="critical"),
        ]
        decision = make_decision(results, {"vendor_name": "QuickFix"}, self._make_match(), {})
        assert decision.status == DecisionStatus.REJECTED.value

    def test_decision_has_all_fields(self):
        results = [ValidationOutcome("required_fields", True, "OK")]
        decision = make_decision(
            results,
            {"invoice_number": "INV-001", "vendor_name": "Test", "total_amount": 100},
            self._make_match(),
            {},
        )
        d = decision.to_dict()
        assert "status" in d
        assert "explanation" in d
        assert "validation_outcomes" in d
        assert "invoice_values" in d
        assert "reasons" in d
        assert "recommended_action" in d

    def test_multiple_critical_all_listed(self):
        results = [
            ValidationOutcome("duplicate_check", False, "Duplicate", severity="critical"),
            ValidationOutcome("vendor_validation", False, "Suspended", severity="critical"),
        ]
        decision = make_decision(results, {}, MatchResult(matched=False), {})
        assert decision.status == DecisionStatus.REJECTED.value
        assert len(decision.reasons) == 2
