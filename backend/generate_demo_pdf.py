import os
from pathlib import Path
from app.services.pdf_generator import generate_invoice_pdf

target_paths = [
    Path(r"C:\Users\sahup\.gemini\antigravity\scratch\invoice-intelligence\demo_invoice_to_upload.pdf"),
    Path(r"C:\Users\sahup\Downloads\demo_invoice_to_upload.pdf") if os.path.exists(r"C:\Users\sahup\Downloads") else None
]

items = [
    {"description": "Ultra-Wide 34-inch Office Monitor", "quantity": 4, "unit_price": 600.00, "amount": 2400.00},
    {"description": "Mechanical Keyboards (Tactile)", "quantity": 15, "unit_price": 120.00, "amount": 1800.00},
    {"description": "Ergonomic Desk Wrist Rests", "quantity": 10, "unit_price": 30.00, "amount": 300.00},
]

for p in target_paths:
    if p:
        generate_invoice_pdf(
            output_path=str(p),
            vendor_name="Acme Office Supplies",
            vendor_address="123 Supply Lane, Commerce City, CO 80022",
            tax_id="TAX-ACME-001",
            invoice_number="INV-2024-LIVE-99",
            invoice_date="2024-11-12",
            po_reference="PO-2024-001",
            bill_to_name="Globex Corporation",
            bill_to_address="500 Enterprise Blvd, Austin, TX 78701",
            line_items=items,
            subtotal=4500.00,
            tax=450.00,
            total=4950.00,
            currency="USD"
        )
        print("Generated PDF at:", p)
