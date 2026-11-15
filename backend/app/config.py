"""Application configuration."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'invoice_intelligence.db'}")
UPLOAD_DIR = BASE_DIR / "uploads"
SAMPLE_INVOICES_DIR = BASE_DIR / "sample_invoices"
STATIC_DIR = BASE_DIR / "app" / "static"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_INVOICES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
