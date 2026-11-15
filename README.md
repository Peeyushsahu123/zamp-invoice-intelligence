# Invoice Intelligence — AI-Powered AP Automation

An intelligent invoice processing and approval system built for the Zamp AI Solutions Associate Case Study (PS-1). This application demonstrates genuine AI-powered business automation with deterministic financial controls.

## What It Does

1. **Accepts** vendor invoice PDFs via drag-and-drop or API
2. **Extracts** structured data using LLM (with deterministic fallback)
3. **Validates** against 7 configurable business rules
4. **Matches** invoices to purchase orders with vendor verification
5. **Decides** APPROVED / REVIEW_REQUIRED / REJECTED with full explanations
6. **Displays** real-time processing stages and results in a polished dashboard

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (SPA)                     │
│          HTML/JS served by FastAPI                   │
├─────────────────────────────────────────────────────┤
│                  FastAPI Backend                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Extraction│ │Validation│ │ Decision │            │
│  │ Pipeline  │→│  Engine  │→│  Engine  │            │
│  └──────────┘ └──────────┘ └──────────┘            │
│       │              │                              │
│  ┌────┴────┐  ┌──────┴──────┐                      │
│  │AI Provider│ │ PO Matching │                      │
│  │(isolated)│  │   Service   │                      │
│  └─────────┘  └─────────────┘                      │
├─────────────────────────────────────────────────────┤
│              SQLite + SQLAlchemy                     │
│  Vendors │ POs │ Invoices │ Runs │ Validations      │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- pip

### Setup & Run

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m uvicorn app.main:app --reload --port 8000

# Open in browser
# http://localhost:8000
```

### Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Optional: AI Extraction

Set one of these environment variables before starting the server:

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
export GEMINI_API_KEY=AI...
```

Without an API key, the system uses a deterministic pattern-based parser. The extraction method is clearly displayed in the UI.

## Sample Invoices

The system generates 8 sample invoices on startup to demonstrate all scenarios:

| Invoice | Scenario | Expected Decision |
|---------|----------|-------------------|
| Normal Invoice (Acme) | Clean invoice within PO tolerance | ✅ APPROVED |
| Over Tolerance (TechParts) | Exceeds PO by >6% | ❌ REJECTED |
| Missing PO (CloudServe) | No PO reference | ⚠️ REVIEW_REQUIRED |
| Duplicate Invoice | Same INV-2024-001 | ❌ REJECTED |
| Suspended Vendor (QuickFix) | Vendor is suspended | ❌ REJECTED |
| Partial Invoice 1 | First partial against PO-004 | ✅ APPROVED |
| Partial Invoice 2 | Cumulative exceeds PO | ❌ REJECTED |
| Arithmetic Error | subtotal+tax ≠ total | ⚠️ REVIEW_REQUIRED |

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite, Pydantic
- **Frontend**: Vanilla JS SPA with Tailwind CSS (served by FastAPI)
- **PDF Processing**: PyMuPDF (text extraction), fpdf2 (sample generation)
- **AI**: Pluggable LLM provider (OpenAI/Anthropic/Gemini), regex fallback
- **Testing**: pytest

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, lifespan, routes
│   ├── config.py             # Configuration
│   ├── database.py           # SQLAlchemy setup
│   ├── models.py             # ORM models (5 tables)
│   ├── schemas.py            # Pydantic schemas
│   ├── seed.py               # Demo data seeding
│   ├── routes/
│   │   ├── invoices.py       # Upload & processing
│   │   ├── dashboard.py      # Real-time stats
│   │   ├── runs.py           # Processing history
│   │   ├── vendors.py        # Vendor & PO management
│   │   └── settings.py       # Configuration API
│   ├── services/
│   │   ├── extraction.py     # PDF → text → structured data
│   │   ├── ai_provider.py    # Isolated LLM integration
│   │   ├── validation.py     # 7 validation rules
│   │   ├── matching.py       # PO matching service
│   │   ├── decision.py       # Deterministic decision engine
│   │   └── pdf_generator.py  # Sample invoice generator
│   └── static/               # Frontend SPA
└── tests/
    ├── conftest.py            # Fixtures with test DB
    ├── test_validation.py     # Validation rule tests
    ├── test_extraction.py     # Extraction pipeline tests
    ├── test_decision.py       # Decision engine tests
    └── test_api.py            # API integration tests
```

## License

Built for Zamp AI Solutions Associate Case Study evaluation.
