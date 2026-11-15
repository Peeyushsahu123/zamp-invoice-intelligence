"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.seed import seed_database
from app.services.pdf_generator import generate_all_samples


@pytest.fixture
def client(tmp_path):
    """Create a test client with a fresh database."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed
    db = TestSession()
    seed_database(db)
    db.close()

    # Generate samples
    import app.config as cfg
    original_dir = cfg.SAMPLE_INVOICES_DIR
    cfg.SAMPLE_INVOICES_DIR = tmp_path / "samples"
    generate_all_samples(cfg.SAMPLE_INVOICES_DIR)

    yield TestClient(app)

    app.dependency_overrides.clear()
    cfg.SAMPLE_INVOICES_DIR = original_dir


class TestDashboardAPI:
    def test_stats_empty(self, client):
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] == 0
        assert data["approved_count"] == 0

    def test_stats_after_processing(self, client):
        # Process a normal invoice
        client.post("/api/invoices/process-sample/invoice_normal.pdf")
        response = client.get("/api/dashboard/stats")
        data = response.json()
        assert data["total_processed"] >= 1


class TestVendorsAPI:
    def test_list_vendors(self, client):
        response = client.get("/api/vendors")
        assert response.status_code == 200
        vendors = response.json()
        assert len(vendors) == 4
        names = [v["name"] for v in vendors]
        assert "Acme Office Supplies" in names

    def test_list_purchase_orders(self, client):
        response = client.get("/api/purchase-orders")
        assert response.status_code == 200
        pos = response.json()
        assert len(pos) == 5


class TestInvoiceUpload:
    def test_upload_normal_invoice(self, client, tmp_path):
        # Generate a test PDF
        from app.services.pdf_generator import generate_invoice_pdf
        pdf_path = tmp_path / "test_upload.pdf"
        generate_invoice_pdf(
            str(pdf_path), "Acme Office Supplies", "123 Lane", "TAX-ACME-001",
            "INV-UPLOAD-001", "2024-11-01", "PO-2024-001", "Test Co", "Address",
            [{"description": "Item", "quantity": 1, "unit_price": 100.0, "amount": 100.0}],
            100.0, 10.0, 110.0,
        )
        with open(pdf_path, "rb") as f:
            response = client.post("/api/invoices/upload", files={"file": ("test.pdf", f, "application/pdf")})
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["status"] == "completed"

    def test_reject_non_pdf(self, client):
        from io import BytesIO
        response = client.post("/api/invoices/upload",
                             files={"file": ("test.txt", BytesIO(b"not a pdf"), "text/plain")})
        assert response.status_code == 400


class TestProcessSample:
    def test_process_normal(self, client):
        response = client.post("/api/invoices/process-sample/invoice_normal.pdf")
        assert response.status_code == 200
        data = response.json()
        assert data["decision"]["status"] == "APPROVED"

    def test_process_suspended_vendor(self, client):
        response = client.post("/api/invoices/process-sample/invoice_suspended_vendor.pdf")
        assert response.status_code == 200
        data = response.json()
        assert data["decision"]["status"] == "REJECTED"

    def test_process_no_po(self, client):
        response = client.post("/api/invoices/process-sample/invoice_no_po.pdf")
        assert response.status_code == 200
        data = response.json()
        assert data["decision"]["status"] == "REVIEW_REQUIRED"

    def test_process_bad_math(self, client):
        response = client.post("/api/invoices/process-sample/invoice_bad_math.pdf")
        assert response.status_code == 200
        data = response.json()
        assert data["decision"]["status"] == "REVIEW_REQUIRED"

    def test_process_over_tolerance(self, client):
        response = client.post("/api/invoices/process-sample/invoice_over_tolerance.pdf")
        assert response.status_code == 200
        data = response.json()
        assert data["decision"]["status"] == "REJECTED"

    def test_process_nonexistent_sample(self, client):
        response = client.post("/api/invoices/process-sample/does_not_exist.pdf")
        assert response.status_code == 404


class TestRunsAPI:
    def test_list_runs_empty(self, client):
        response = client.get("/api/runs")
        assert response.status_code == 200
        assert response.json()["runs"] == []

    def test_get_run_after_processing(self, client):
        # Process an invoice first
        proc = client.post("/api/invoices/process-sample/invoice_normal.pdf")
        run_id = proc.json()["run_id"]

        response = client.get(f"/api/runs/{run_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert data["stages"] is not None
        assert len(data["stages"]) > 0

    def test_get_nonexistent_run(self, client):
        response = client.get("/api/runs/99999")
        assert response.status_code == 404

    def test_manual_decision_override(self, client):
        proc = client.post("/api/invoices/process-sample/invoice_no_po.pdf")
        run_id = proc.json()["run_id"]
        assert proc.json()["decision"]["status"] == "REVIEW_REQUIRED"

        # Manually approve
        res = client.post(f"/api/runs/{run_id}/manual-decision", json={
            "status": "APPROVED",
            "notes": "Verified vendor out-of-band"
        })
        assert res.status_code == 200
        assert res.json()["decision"]["status"] == "APPROVED"
        assert res.json()["decision"]["manual_override"] is True


class TestSettingsAPI:
    def test_get_settings(self, client):
        response = client.get("/api/settings")
        assert response.status_code == 200
        settings = response.json()
        assert len(settings) >= 3

    def test_update_settings(self, client):
        response = client.put("/api/settings", json={"tolerance_percent": "5.0"})
        assert response.status_code == 200
        assert "tolerance_percent" in response.json()["updated"]


class TestSampleInvoices:
    def test_list_samples(self, client):
        response = client.get("/api/invoices/samples")
        assert response.status_code == 200
        samples = response.json()
        assert len(samples) >= 1
