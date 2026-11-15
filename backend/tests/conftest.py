"""Pytest configuration and fixtures."""
import os
import sys
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base
from app.models import Vendor, PurchaseOrder, Settings, VendorStatus, POStatus


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test data
    vendors = [
        Vendor(name="Acme Office Supplies", tax_id="TAX-ACME-001", status=VendorStatus.APPROVED,
               email="billing@acmeoffice.com"),
        Vendor(name="TechParts Global", tax_id="TAX-TECH-002", status=VendorStatus.APPROVED,
               email="invoices@techparts.com"),
        Vendor(name="CloudServe Solutions", tax_id="TAX-CLOUD-003", status=VendorStatus.APPROVED,
               email="accounts@cloudserve.io"),
        Vendor(name="QuickFix Maintenance", tax_id="TAX-QUICK-004", status=VendorStatus.SUSPENDED,
               email="service@quickfix.com"),
    ]
    session.add_all(vendors)
    session.flush()

    pos = [
        PurchaseOrder(po_number="PO-2024-001", vendor_id=vendors[0].id, description="Office Supplies",
                      total_amount=5000.00, currency="USD", status=POStatus.OPEN, tolerance_percent=2.0),
        PurchaseOrder(po_number="PO-2024-002", vendor_id=vendors[1].id, description="Server Components",
                      total_amount=25000.00, currency="USD", status=POStatus.OPEN, tolerance_percent=2.0),
        PurchaseOrder(po_number="PO-2024-003", vendor_id=vendors[2].id, description="Cloud Hosting",
                      total_amount=12000.00, currency="USD", status=POStatus.OPEN, tolerance_percent=2.0),
        PurchaseOrder(po_number="PO-2024-004", vendor_id=vendors[1].id, description="Network Equipment",
                      total_amount=8500.00, currency="USD", status=POStatus.OPEN, tolerance_percent=2.0),
        PurchaseOrder(po_number="PO-2024-005", vendor_id=vendors[3].id, description="Building Maintenance",
                      total_amount=3000.00, currency="USD", status=POStatus.OPEN, tolerance_percent=2.0),
    ]
    session.add_all(pos)

    settings = [
        Settings(key="tolerance_percent", value="2.0", description="Default tolerance %"),
        Settings(key="auto_approve_below", value="1000.00", description="Auto-approve below"),
        Settings(key="require_po_match", value="true", description="Require PO match"),
    ]
    session.add_all(settings)
    session.commit()

    yield session
    session.close()


@pytest.fixture
def sample_invoice_dir(tmp_path):
    """Create a temporary directory with sample invoice PDFs."""
    from app.services.pdf_generator import generate_all_samples
    generate_all_samples(tmp_path)
    return tmp_path
