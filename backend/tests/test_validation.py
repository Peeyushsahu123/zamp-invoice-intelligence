"""Tests for the validation engine."""
import pytest
from app.services.validation import (
    validate_required_fields,
    validate_duplicate_invoice,
    validate_vendor,
    validate_po_match,
    validate_arithmetic,
    validate_amount_tolerance,
    validate_cumulative_po_balance,
    run_all_validations,
)
from app.models import Invoice, ProcessingRun, RunStatus, DecisionStatus


class TestRequiredFields:
    def test_all_present(self):
        data = {"invoice_number": "INV-001", "vendor_name": "Acme", "total_amount": 100.0}
        result = validate_required_fields(data)
        assert result.passed is True

    def test_missing_invoice_number(self):
        data = {"vendor_name": "Acme", "total_amount": 100.0}
        result = validate_required_fields(data)
        assert result.passed is False
        assert "invoice_number" in result.message

    def test_missing_multiple(self):
        data = {"invoice_date": "2024-01-01"}
        result = validate_required_fields(data)
        assert result.passed is False
        assert "invoice_number" in result.message
        assert "vendor_name" in result.message


class TestDuplicateDetection:
    def test_no_duplicate(self, db_session):
        result = validate_duplicate_invoice("INV-NEW-001", "Acme Office Supplies", db_session)
        assert result.passed is True

    def test_duplicate_found(self, db_session):
        # Create an existing invoice and approved run
        inv = Invoice(invoice_number="INV-DUP-001", vendor_name="Acme Office Supplies",
                      total_amount=1000.0)
        db_session.add(inv)
        db_session.flush()
        run = ProcessingRun(
            invoice_id=inv.id, status=RunStatus.COMPLETED,
            decision={"status": DecisionStatus.APPROVED.value}
        )
        db_session.add(run)
        db_session.commit()

        result = validate_duplicate_invoice("INV-DUP-001", "Acme Office Supplies", db_session)
        assert result.passed is False
        assert result.severity == "critical"

    def test_no_invoice_number(self, db_session):
        result = validate_duplicate_invoice("", "Acme", db_session)
        assert result.passed is True


class TestVendorValidation:
    def test_approved_vendor(self, db_session):
        result = validate_vendor("Acme Office Supplies", db_session)
        assert result.passed is True

    def test_suspended_vendor(self, db_session):
        result = validate_vendor("QuickFix Maintenance", db_session)
        assert result.passed is False
        assert result.severity == "critical"

    def test_unknown_vendor(self, db_session):
        result = validate_vendor("Unknown Corp", db_session)
        assert result.passed is False
        assert result.severity == "warning"

    def test_no_vendor_name(self, db_session):
        result = validate_vendor("", db_session)
        assert result.passed is False


class TestPOMatch:
    def test_valid_match(self, db_session):
        result = validate_po_match("PO-2024-001", "Acme Office Supplies", db_session)
        assert result.passed is True

    def test_po_not_found(self, db_session):
        result = validate_po_match("PO-9999-999", "Acme", db_session)
        assert result.passed is False

    def test_no_po_reference(self, db_session):
        result = validate_po_match("", "Acme", db_session)
        assert result.passed is False
        assert result.severity == "warning"

    def test_vendor_mismatch(self, db_session):
        result = validate_po_match("PO-2024-001", "TechParts Global", db_session)
        assert result.passed is False


class TestArithmetic:
    def test_correct_arithmetic(self):
        result = validate_arithmetic(100.0, 10.0, 110.0)
        assert result.passed is True

    def test_arithmetic_mismatch(self):
        result = validate_arithmetic(300.0, 30.0, 350.0)
        assert result.passed is False
        assert "mismatch" in result.message.lower()

    def test_missing_values(self):
        result = validate_arithmetic(None, None, 100.0)
        assert result.passed is True  # Can't check, so pass

    def test_within_tolerance(self):
        result = validate_arithmetic(100.0, 10.0, 110.005, tolerance=0.01)
        assert result.passed is True


class TestAmountTolerance:
    def test_within_tolerance(self):
        result = validate_amount_tolerance(5050.0, 5000.0, 2.0)
        assert result.passed is True

    def test_exceeds_tolerance(self):
        result = validate_amount_tolerance(5500.0, 5000.0, 2.0)
        assert result.passed is False

    def test_exceeds_2x_tolerance_critical(self):
        result = validate_amount_tolerance(5300.0, 5000.0, 2.0)
        assert result.passed is False
        assert result.severity == "critical"

    def test_under_po_amount(self):
        result = validate_amount_tolerance(4000.0, 5000.0, 2.0)
        assert result.passed is True

    def test_missing_values(self):
        result = validate_amount_tolerance(None, 5000.0, 2.0)
        assert result.passed is True


class TestCumulativePOBalance:
    def test_first_invoice_ok(self, db_session):
        # PO-2024-004 is $8,500
        po = db_session.query(
            __import__("app.models", fromlist=["PurchaseOrder"]).PurchaseOrder
        ).filter_by(po_number="PO-2024-004").first()
        result = validate_cumulative_po_balance(po.id, 5000.0, db_session)
        assert result.passed is True

    def test_cumulative_exceeds(self, db_session):
        from app.models import PurchaseOrder
        po = db_session.query(PurchaseOrder).filter_by(po_number="PO-2024-004").first()

        # Create a prior approved invoice against this PO
        inv = Invoice(invoice_number="INV-PRIOR", vendor_name="TechParts Global",
                      total_amount=5000.0, po_reference="PO-2024-004")
        db_session.add(inv)
        db_session.flush()
        run = ProcessingRun(
            invoice_id=inv.id, status=RunStatus.COMPLETED, matched_po_id=po.id,
            decision={"status": DecisionStatus.APPROVED.value}
        )
        db_session.add(run)
        db_session.commit()

        # Now try to add $4,500 more (5000+4500=9500 > 8500*1.02=8670)
        result = validate_cumulative_po_balance(po.id, 4500.0, db_session)
        assert result.passed is False
        assert result.severity == "critical"

    def test_excludes_current_invoice(self, db_session):
        from app.models import PurchaseOrder
        po = db_session.query(PurchaseOrder).filter_by(po_number="PO-2024-004").first()

        inv = Invoice(invoice_number="INV-SELF", vendor_name="TechParts Global",
                      total_amount=5000.0, po_reference="PO-2024-004")
        db_session.add(inv)
        db_session.flush()
        run = ProcessingRun(
            invoice_id=inv.id, status=RunStatus.COMPLETED, matched_po_id=po.id,
            decision={"status": DecisionStatus.APPROVED.value}
        )
        db_session.add(run)
        db_session.commit()

        # Same invoice should not count against itself
        result = validate_cumulative_po_balance(po.id, 5000.0, db_session, current_invoice_id=inv.id)
        assert result.passed is True


class TestRunAllValidations:
    def test_normal_invoice(self, db_session):
        data = {
            "invoice_number": "INV-TEST-001",
            "vendor_name": "Acme Office Supplies",
            "total_amount": 4620.0,
            "subtotal": 4200.0,
            "tax_amount": 420.0,
            "po_reference": "PO-2024-001",
        }
        settings = {"tolerance_percent": "2.0"}
        results = run_all_validations(data, db_session, settings, po_id=1, po_amount=5000.0)
        assert all(r.passed for r in results)
