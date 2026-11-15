"""PDF text extraction and invoice data parsing."""
import re
import logging
from pathlib import Path

import fitz  # PyMuPDF

from app.services.ai_provider import AIProvider, AIProviderUnavailable

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file using PyMuPDF."""
    text_parts: list[str] = []
    doc = fitz.open(file_path)
    try:
        for page in doc:
            text_parts.append(page.get_text())
    finally:
        doc.close()
    return "\n".join(text_parts)


def parse_invoice_with_llm(text: str) -> dict:
    """Call AI provider for structured invoice data extraction.

    Raises AIProviderUnavailable if no API key is configured or the call fails.
    """
    provider = AIProvider()
    data = provider.extract_invoice_data(text)
    data["extraction_method"] = f"llm_{provider.provider}"
    return data


def parse_invoice_fallback(text: str) -> dict:
    """Regex-based deterministic fallback parser for invoice text.

    Works reliably with our sample invoice format (fpdf2 generated).
    Returns a dict with extracted fields and extraction_method='fallback_parser'.
    """
    data: dict = {
        "invoice_number": None,
        "vendor_name": None,
        "vendor_tax_id": None,
        "po_reference": None,
        "invoice_date": None,
        "currency": "USD",
        "subtotal": None,
        "tax_amount": None,
        "total_amount": None,
        "line_items": [],
        "extraction_method": "fallback_parser",
    }

    lines = text.split("\n")

    # Invoice number: INV-XXXX pattern
    m = re.search(r"(INV-[\w-]+)", text)
    if m:
        data["invoice_number"] = m.group(1)

    # Vendor name – try explicit labels first, then first non-empty line
    m = re.search(r"(?:From|Vendor|Supplier|Bill From)[:\s]*([^\n]+)", text, re.IGNORECASE)
    if m:
        data["vendor_name"] = m.group(1).strip()
    else:
        # In our PDF format, vendor name is the first line
        for line in lines:
            stripped = line.strip()
            if stripped and len(stripped) > 3 and not stripped.startswith("INVOICE"):
                data["vendor_name"] = stripped
                break

    # Tax ID
    m = re.search(r"(?:Tax\s*ID|TIN|EIN)[:\s]*([\w-]+)", text, re.IGNORECASE)
    if m:
        data["vendor_tax_id"] = m.group(1).strip()

    # PO reference: PO-XXXX pattern
    m = re.search(r"(PO-[\w-]+)", text)
    if m:
        data["po_reference"] = m.group(1)

    # Date – handle value on same line or next line
    date_patterns = [
        r"(?:Invoice\s*Date|Date)[:\s]*(\d{4}-\d{2}-\d{2})",
        r"(?:Invoice\s*Date|Date)[:\s]*(\d{1,2}/\d{1,2}/\d{4})",
        r"(?:Invoice\s*Date|Date)[:\s]*(\w+ \d{1,2},?\s*\d{4})",
    ]
    for pat in date_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            data["invoice_date"] = m.group(1).strip()
            break

    if not data["invoice_date"]:
        # Check for value on next line: "Invoice Date:\n2024-11-01"
        m = re.search(r"(?:Invoice\s*Date|Date)\s*:\s*\n\s*(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)
        if m:
            data["invoice_date"] = m.group(1).strip()

    # Currency
    if re.search(r"EUR|€", text):
        data["currency"] = "EUR"
    elif re.search(r"GBP|£", text):
        data["currency"] = "GBP"

    # Monetary amounts helper – handles value on same line or next line
    def find_amount(label_pattern: str) -> float | None:
        # Try same-line first
        m = re.search(label_pattern + r"[:\s]*\$?([\d,]+\.?\d*)", text, re.IGNORECASE)
        if m:
            val = m.group(1).replace(",", "").replace("$", "").replace("€", "").replace("£", "").strip()
            try:
                return float(val)
            except ValueError:
                pass

        # Try next-line: "Label:\n$1,234.56"
        m = re.search(label_pattern + r"\s*:\s*\n\s*\$?([\d,]+\.?\d*)", text, re.IGNORECASE)
        if m:
            val = m.group(1).replace(",", "").strip()
            try:
                return float(val)
            except ValueError:
                pass
        return None

    # Subtotal
    data["subtotal"] = find_amount(r"Subtotal")

    # Tax – match "Tax:" but not "Tax ID:"
    data["tax_amount"] = find_amount(r"Tax(?:\s*(?:Amount|\(\d+%\)))?\s*(?=:)")

    # Total
    total = find_amount(r"(?:Grand\s*)?Total\s*Due")
    if total is None:
        total = find_amount(r"(?:Grand\s*)?Total(?!\s*(?:Processed|invoices))")
    data["total_amount"] = total

    # If total equals subtotal, look more specifically
    if data["total_amount"] is not None and data["total_amount"] == data["subtotal"]:
        alt = find_amount(r"Total\s*Due")
        if alt and alt != data["subtotal"]:
            data["total_amount"] = alt

    # Line items – look for tabular rows on single line
    line_pattern = re.compile(
        r"^(.+?)\s+(\d+)\s+\$?([\d,]+\.?\d{2})\s+\$?([\d,]+\.?\d{2})\s*$",
        re.MULTILINE,
    )
    for m in line_pattern.finditer(text):
        desc = m.group(1).strip()
        if desc.lower() in ("description", "item", "product"):
            continue
        data["line_items"].append({
            "description": desc,
            "quantity": int(m.group(2)),
            "unit_price": float(m.group(3).replace(",", "")),
            "amount": float(m.group(4).replace(",", "")),
        })

    return data


def extract_invoice(file_path: str) -> dict:
    """Main extraction entry point.

    Tries LLM extraction first, falls back to regex parser if LLM is
    unavailable or fails.
    """
    text = extract_text_from_pdf(file_path)

    # Try LLM first
    try:
        data = parse_invoice_with_llm(text)
        logger.info("Invoice extracted via LLM")
        return data
    except AIProviderUnavailable as e:
        logger.info(f"LLM unavailable ({e}), using fallback parser")
    except Exception as e:
        logger.warning(f"LLM extraction failed ({e}), using fallback parser")

    # Fallback to regex parser
    data = parse_invoice_fallback(text)
    logger.info("Invoice extracted via fallback parser")
    return data
