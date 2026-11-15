"""Generate realistic sample invoice PDFs using fpdf2."""
from fpdf import FPDF
from pathlib import Path
import os


class InvoicePDF(FPDF):
    """Custom PDF class for professional invoice generation."""

    def header_block(self, vendor_name: str, vendor_address: str, tax_id: str):
        self.set_font("Helvetica", "B", 18)
        self.cell(0, 10, vendor_name, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, vendor_address, new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, f"Tax ID: {tax_id}", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def invoice_meta(self, fields: dict):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, "INVOICE", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.set_font("Helvetica", "", 10)
        for key, val in fields.items():
            if val is not None:
                self.cell(45, 6, f"{key}:", new_x="RIGHT")
                self.cell(0, 6, str(val), new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def bill_to(self, name: str, address: str):
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, "Bill To:", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 5, name, new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, address, new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def line_items_table(self, items: list[dict]):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(240, 240, 245)
        self.cell(80, 7, "Description", border=1, fill=True)
        self.cell(25, 7, "Qty", border=1, align="C", fill=True)
        self.cell(35, 7, "Unit Price", border=1, align="R", fill=True)
        self.cell(40, 7, "Amount", border=1, align="R", fill=True, new_x="LMARGIN", new_y="NEXT")

        self.set_font("Helvetica", "", 9)
        for item in items:
            self.cell(80, 6, item["description"][:42], border=1)
            self.cell(25, 6, str(item["quantity"]), border=1, align="C")
            self.cell(35, 6, f"${item['unit_price']:,.2f}", border=1, align="R")
            self.cell(40, 6, f"${item['amount']:,.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def totals_section(self, subtotal: float, tax: float, total: float, currency: str = "USD"):
        sym = "$" if currency == "USD" else ("EUR " if currency == "EUR" else "GBP ")
        x_start = 130
        self.set_font("Helvetica", "", 10)
        self.set_x(x_start)
        self.cell(30, 6, "Subtotal:", align="R")
        self.cell(30, 6, f"{sym}{subtotal:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_x(x_start)
        self.cell(30, 6, "Tax:", align="R")
        self.cell(30, 6, f"{sym}{tax:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_x(x_start)
        self.set_font("Helvetica", "B", 11)
        self.cell(30, 7, "Total Due:", align="R")
        self.cell(30, 7, f"{sym}{total:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")


def generate_invoice_pdf(
    output_path: str,
    vendor_name: str,
    vendor_address: str,
    tax_id: str,
    invoice_number: str,
    invoice_date: str,
    po_reference: str | None,
    bill_to_name: str,
    bill_to_address: str,
    line_items: list[dict],
    subtotal: float,
    tax: float,
    total: float,
    currency: str = "USD",
):
    pdf = InvoicePDF()
    pdf.add_page()
    pdf.header_block(vendor_name, vendor_address, tax_id)
    meta = {"Invoice Number": invoice_number, "Invoice Date": invoice_date}
    if po_reference:
        meta["PO Reference"] = po_reference
    meta["Currency"] = currency
    pdf.invoice_meta(meta)
    pdf.bill_to(bill_to_name, bill_to_address)
    pdf.line_items_table(line_items)
    pdf.totals_section(subtotal, tax, total, currency)
    pdf.output(str(output_path))


def generate_all_samples(output_dir: str | Path):
    """Generate all sample invoice PDFs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    bill_to = ("Globex Corporation", "500 Enterprise Blvd, Austin, TX 78701")

    samples = [
        {
            "filename": "invoice_normal.pdf",
            "label": "Normal Invoice (Acme)",
            "description": "Clean invoice within PO tolerance - should be APPROVED",
            "vendor_name": "Acme Office Supplies",
            "vendor_address": "123 Supply Lane, Commerce City, CO 80022",
            "tax_id": "TAX-ACME-001",
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-11-01",
            "po_reference": "PO-2024-001",
            "line_items": [
                {"description": "Premium Copy Paper (10 reams)", "quantity": 10, "unit_price": 45.00, "amount": 450.00},
                {"description": "Ink Cartridges (Color Set)", "quantity": 5, "unit_price": 120.00, "amount": 600.00},
                {"description": "Office Chairs (Ergonomic)", "quantity": 3, "unit_price": 850.00, "amount": 2550.00},
                {"description": "Standing Desk Converter", "quantity": 2, "unit_price": 300.00, "amount": 600.00},
            ],
            "subtotal": 4200.00,
            "tax": 420.00,
            "total": 4620.00,
        },
        {
            "filename": "invoice_over_tolerance.pdf",
            "label": "Over Tolerance (TechParts)",
            "description": "Exceeds PO amount by >6% - should be REJECTED",
            "vendor_name": "TechParts Global",
            "vendor_address": "456 Silicon Ave, San Jose, CA 95131",
            "tax_id": "TAX-TECH-002",
            "invoice_number": "INV-2024-002",
            "invoice_date": "2024-11-05",
            "po_reference": "PO-2024-002",
            "line_items": [
                {"description": "Server CPU (Xeon Platinum)", "quantity": 4, "unit_price": 3500.00, "amount": 14000.00},
                {"description": "ECC RAM 128GB Kit", "quantity": 4, "unit_price": 1200.00, "amount": 4800.00},
                {"description": "NVMe SSD 2TB Enterprise", "quantity": 8, "unit_price": 450.00, "amount": 3600.00},
                {"description": "Rack Mount Kit", "quantity": 2, "unit_price": 650.00, "amount": 1300.00},
                {"description": "Express Shipping", "quantity": 1, "unit_price": 400.00, "amount": 400.00},
            ],
            "subtotal": 24100.00,
            "tax": 2410.00,
            "total": 26510.00,
        },
        {
            "filename": "invoice_no_po.pdf",
            "label": "Missing PO (CloudServe)",
            "description": "No PO reference - should be REVIEW_REQUIRED",
            "vendor_name": "CloudServe Solutions",
            "vendor_address": "789 Cloud Blvd, Seattle, WA 98101",
            "tax_id": "TAX-CLOUD-003",
            "invoice_number": "INV-2024-003",
            "invoice_date": "2024-11-10",
            "po_reference": None,
            "line_items": [
                {"description": "Cloud Compute (Nov 2024)", "quantity": 1, "unit_price": 2800.00, "amount": 2800.00},
                {"description": "Data Transfer (500GB)", "quantity": 1, "unit_price": 200.00, "amount": 200.00},
                {"description": "Support Plan (Premium)", "quantity": 1, "unit_price": 180.00, "amount": 180.00},
            ],
            "subtotal": 3180.00,
            "tax": 318.00,
            "total": 3498.00,
        },
        {
            "filename": "invoice_duplicate.pdf",
            "label": "Duplicate Invoice",
            "description": "Same INV-2024-001 from Acme - should be REJECTED after first is processed",
            "vendor_name": "Acme Office Supplies",
            "vendor_address": "123 Supply Lane, Commerce City, CO 80022",
            "tax_id": "TAX-ACME-001",
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-11-01",
            "po_reference": "PO-2024-001",
            "line_items": [
                {"description": "Premium Copy Paper (10 reams)", "quantity": 10, "unit_price": 45.00, "amount": 450.00},
                {"description": "Ink Cartridges (Color Set)", "quantity": 5, "unit_price": 120.00, "amount": 600.00},
                {"description": "Office Chairs (Ergonomic)", "quantity": 3, "unit_price": 850.00, "amount": 2550.00},
                {"description": "Standing Desk Converter", "quantity": 2, "unit_price": 300.00, "amount": 600.00},
            ],
            "subtotal": 4200.00,
            "tax": 420.00,
            "total": 4620.00,
        },
        {
            "filename": "invoice_suspended_vendor.pdf",
            "label": "Suspended Vendor (QuickFix)",
            "description": "From suspended vendor - should be REJECTED",
            "vendor_name": "QuickFix Maintenance",
            "vendor_address": "321 Repair Road, Denver, CO 80201",
            "tax_id": "TAX-QUICK-004",
            "invoice_number": "INV-2024-005",
            "invoice_date": "2024-11-12",
            "po_reference": "PO-2024-005",
            "line_items": [
                {"description": "HVAC Repair Service", "quantity": 1, "unit_price": 1200.00, "amount": 1200.00},
                {"description": "Replacement Parts", "quantity": 1, "unit_price": 850.00, "amount": 850.00},
                {"description": "Labor (8 hours)", "quantity": 8, "unit_price": 75.00, "amount": 600.00},
            ],
            "subtotal": 2650.00,
            "tax": 159.00,
            "total": 2809.00,
        },
        {
            "filename": "invoice_cumulative.pdf",
            "label": "Partial Invoice 1 (PO-2024-004)",
            "description": "First invoice against PO-2024-004 ($8,500) - $5,000 - should be APPROVED",
            "vendor_name": "TechParts Global",
            "vendor_address": "456 Silicon Ave, San Jose, CA 95131",
            "tax_id": "TAX-TECH-002",
            "invoice_number": "INV-2024-006",
            "invoice_date": "2024-11-15",
            "po_reference": "PO-2024-004",
            "line_items": [
                {"description": "Managed Switch 48-Port", "quantity": 2, "unit_price": 1500.00, "amount": 3000.00},
                {"description": "SFP+ Modules", "quantity": 10, "unit_price": 150.00, "amount": 1500.00},
            ],
            "subtotal": 4500.00,
            "tax": 450.00,
            "total": 4950.00,
        },
        {
            "filename": "invoice_cumulative_over.pdf",
            "label": "Partial Invoice 2 - Overbills PO",
            "description": "Second invoice against PO-2024-004 - cumulative exceeds PO - should be REJECTED",
            "vendor_name": "TechParts Global",
            "vendor_address": "456 Silicon Ave, San Jose, CA 95131",
            "tax_id": "TAX-TECH-002",
            "invoice_number": "INV-2024-007",
            "invoice_date": "2024-11-20",
            "po_reference": "PO-2024-004",
            "line_items": [
                {"description": "Wireless Access Points", "quantity": 5, "unit_price": 600.00, "amount": 3000.00},
                {"description": "PoE Injectors", "quantity": 5, "unit_price": 80.00, "amount": 400.00},
                {"description": "Cable Management Kit", "quantity": 1, "unit_price": 200.00, "amount": 200.00},
            ],
            "subtotal": 3600.00,
            "tax": 360.00,
            "total": 3960.00,
        },
        {
            "filename": "invoice_bad_math.pdf",
            "label": "Arithmetic Error Invoice",
            "description": "Subtotal + tax != total (300+30=330, but total says 350) - should be REVIEW_REQUIRED",
            "vendor_name": "Acme Office Supplies",
            "vendor_address": "123 Supply Lane, Commerce City, CO 80022",
            "tax_id": "TAX-ACME-001",
            "invoice_number": "INV-2024-008",
            "invoice_date": "2024-11-22",
            "po_reference": "PO-2024-001",
            "line_items": [
                {"description": "Printer Toner (Black)", "quantity": 3, "unit_price": 80.00, "amount": 240.00},
                {"description": "USB Flash Drives 64GB", "quantity": 6, "unit_price": 10.00, "amount": 60.00},
            ],
            "subtotal": 300.00,
            "tax": 30.00,
            "total": 350.00,
        },
    ]

    manifest = []
    for s in samples:
        path = output_dir / s["filename"]
        generate_invoice_pdf(
            output_path=str(path),
            vendor_name=s["vendor_name"],
            vendor_address=s["vendor_address"],
            tax_id=s["tax_id"],
            invoice_number=s["invoice_number"],
            invoice_date=s["invoice_date"],
            po_reference=s["po_reference"],
            bill_to_name=bill_to[0],
            bill_to_address=bill_to[1],
            line_items=s["line_items"],
            subtotal=s["subtotal"],
            tax=s["tax"],
            total=s["total"],
        )
        manifest.append({
            "filename": s["filename"],
            "label": s["label"],
            "description": s["description"],
        })

    return manifest


if __name__ == "__main__":
    from app.config import SAMPLE_INVOICES_DIR
    manifest = generate_all_samples(SAMPLE_INVOICES_DIR)
    for m in manifest:
        print(f"  Generated: {m['filename']} - {m['label']}")
