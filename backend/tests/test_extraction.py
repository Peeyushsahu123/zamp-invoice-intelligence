"""Tests for extraction service."""
import pytest
from pathlib import Path


class TestFallbackParser:
    def test_normal_invoice(self, sample_invoice_dir):
        from app.services.extraction import extract_text_from_pdf, parse_invoice_fallback

        text = extract_text_from_pdf(str(sample_invoice_dir / "invoice_normal.pdf"))
        assert len(text) > 50

        data = parse_invoice_fallback(text)
        assert data["invoice_number"] == "INV-2024-001"
        assert data["po_reference"] == "PO-2024-001"
        assert data["extraction_method"] == "fallback_parser"
        assert "Acme" in (data["vendor_name"] or "")
        # Check amounts are extracted
        assert data["total_amount"] is not None
        assert data["total_amount"] > 0

    def test_no_po_invoice(self, sample_invoice_dir):
        from app.services.extraction import extract_text_from_pdf, parse_invoice_fallback

        text = extract_text_from_pdf(str(sample_invoice_dir / "invoice_no_po.pdf"))
        data = parse_invoice_fallback(text)
        assert data["invoice_number"] == "INV-2024-003"
        assert data["po_reference"] is None

    def test_extract_invoice_full_pipeline(self, sample_invoice_dir):
        """Test the full extraction pipeline (should use fallback since no API key)."""
        from app.services.extraction import extract_invoice

        data = extract_invoice(str(sample_invoice_dir / "invoice_normal.pdf"))
        assert "extraction_method" in data
        assert data["extraction_method"] == "fallback_parser"
        assert data["invoice_number"] == "INV-2024-001"

    def test_text_extraction(self, sample_invoice_dir):
        from app.services.extraction import extract_text_from_pdf

        text = extract_text_from_pdf(str(sample_invoice_dir / "invoice_normal.pdf"))
        assert "INV-2024-001" in text
        assert "PO-2024-001" in text
        assert "Acme" in text

    def test_bad_math_invoice(self, sample_invoice_dir):
        from app.services.extraction import extract_text_from_pdf, parse_invoice_fallback

        text = extract_text_from_pdf(str(sample_invoice_dir / "invoice_bad_math.pdf"))
        data = parse_invoice_fallback(text)
        assert data["invoice_number"] == "INV-2024-008"
        assert data["subtotal"] == 300.0
        assert data["tax_amount"] == 30.0
        assert data["total_amount"] == 350.0  # Wrong math, but that's what the PDF says
