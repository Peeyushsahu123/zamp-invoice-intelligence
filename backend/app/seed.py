"""Seed the database with initial data."""
from sqlalchemy.orm import Session
from app.models import Vendor, PurchaseOrder, Settings, VendorStatus, POStatus


def seed_database(db: Session):
    """Seed the database with vendors, POs, and default settings if empty."""
    # Check if already seeded
    if db.query(Vendor).count() > 0:
        return

    # ── Vendors ─────────────────────────────────────────────────────────────
    vendors = [
        Vendor(
            name="Acme Office Supplies",
            tax_id="TAX-ACME-001",
            status=VendorStatus.APPROVED,
            email="billing@acmeoffice.com",
            address="123 Supply Lane, Commerce City, CO 80022",
        ),
        Vendor(
            name="TechParts Global",
            tax_id="TAX-TECH-002",
            status=VendorStatus.APPROVED,
            email="invoices@techparts.com",
            address="456 Silicon Ave, San Jose, CA 95131",
        ),
        Vendor(
            name="CloudServe Solutions",
            tax_id="TAX-CLOUD-003",
            status=VendorStatus.APPROVED,
            email="accounts@cloudserve.io",
            address="789 Cloud Blvd, Seattle, WA 98101",
        ),
        Vendor(
            name="QuickFix Maintenance",
            tax_id="TAX-QUICK-004",
            status=VendorStatus.SUSPENDED,
            email="service@quickfix.com",
            address="321 Repair Road, Denver, CO 80201",
        ),
    ]
    db.add_all(vendors)
    db.flush()

    # ── Purchase Orders ─────────────────────────────────────────────────────
    purchase_orders = [
        PurchaseOrder(
            po_number="PO-2024-001",
            vendor_id=vendors[0].id,
            description="Office Supplies",
            total_amount=5000.00,
            currency="USD",
            status=POStatus.OPEN,
            tolerance_percent=2.0,
        ),
        PurchaseOrder(
            po_number="PO-2024-002",
            vendor_id=vendors[1].id,
            description="Server Components",
            total_amount=25000.00,
            currency="USD",
            status=POStatus.OPEN,
            tolerance_percent=2.0,
        ),
        PurchaseOrder(
            po_number="PO-2024-003",
            vendor_id=vendors[2].id,
            description="Cloud Hosting Annual",
            total_amount=12000.00,
            currency="USD",
            status=POStatus.OPEN,
            tolerance_percent=2.0,
        ),
        PurchaseOrder(
            po_number="PO-2024-004",
            vendor_id=vendors[1].id,
            description="Network Equipment",
            total_amount=8500.00,
            currency="USD",
            status=POStatus.OPEN,
            tolerance_percent=2.0,
        ),
        PurchaseOrder(
            po_number="PO-2024-005",
            vendor_id=vendors[3].id,
            description="Building Maintenance",
            total_amount=3000.00,
            currency="USD",
            status=POStatus.OPEN,
            tolerance_percent=2.0,
        ),
    ]
    db.add_all(purchase_orders)

    # ── Default Settings ────────────────────────────────────────────────────
    settings = [
        Settings(
            key="tolerance_percent",
            value="2.0",
            description="Default tolerance percentage for PO amount matching",
        ),
        Settings(
            key="auto_approve_below",
            value="1000.00",
            description="Auto-approve invoices below this amount",
        ),
        Settings(
            key="require_po_match",
            value="true",
            description="Whether PO matching is required for approval",
        ),
    ]
    db.add_all(settings)
    db.commit()
