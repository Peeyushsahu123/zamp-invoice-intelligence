"""FastAPI main application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import STATIC_DIR, SAMPLE_INVOICES_DIR
from app.database import create_tables, SessionLocal
from app.seed import seed_database
from app.services.pdf_generator import generate_all_samples

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Invoice Intelligence...")

    # Create tables
    create_tables()
    logger.info("Database tables created")

    # Seed data
    db = SessionLocal()
    try:
        seed_database(db)
        logger.info("Seed data loaded")
    finally:
        db.close()

    # Generate sample invoices
    try:
        manifest = generate_all_samples(SAMPLE_INVOICES_DIR)
        logger.info(f"Generated {len(manifest)} sample invoices")
    except Exception as e:
        logger.warning(f"Failed to generate sample invoices: {e}")

    yield
    logger.info("Shutting down Invoice Intelligence")


app = FastAPI(
    title="Invoice Intelligence",
    description="AI-powered invoice processing and approval system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
from app.routes import invoices, dashboard, runs, vendors, settings
app.include_router(invoices.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(vendors.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

# Static files (frontend)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the frontend SPA."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Invoice Intelligence API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "invoice-intelligence"}
