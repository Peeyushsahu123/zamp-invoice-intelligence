"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Vendor schemas ──────────────────────────────────────────────────────────
class VendorOut(BaseModel):
    id: int
    name: str
    tax_id: str
    status: str
    email: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Purchase Order schemas ──────────────────────────────────────────────────
class PurchaseOrderOut(BaseModel):
    id: int
    po_number: str
    vendor_id: int
    description: Optional[str] = None
    total_amount: float
    currency: str = "USD"
    status: str
    created_at: Optional[datetime] = None
    tolerance_percent: float = 2.0
    vendor_name: Optional[str] = None
    remaining_balance: Optional[float] = None

    model_config = {"from_attributes": True}


# ── Invoice schemas ─────────────────────────────────────────────────────────
class InvoiceOut(BaseModel):
    id: int
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_tax_id: Optional[str] = None
    po_reference: Optional[str] = None
    invoice_date: Optional[str] = None
    currency: str = "USD"
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    line_items: Optional[list] = None
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Processing Run schemas ──────────────────────────────────────────────────
class StageInfo(BaseModel):
    name: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    details: Optional[dict] = None


class ValidationResultOut(BaseModel):
    id: int
    run_id: int
    rule_name: str
    passed: bool
    message: Optional[str] = None
    details: Optional[dict] = None

    model_config = {"from_attributes": True}


class ProcessingRunOut(BaseModel):
    id: int
    invoice_id: int
    status: str
    extraction_method: Optional[str] = None
    stages: Optional[list] = None
    extracted_data: Optional[dict] = None
    validation_results: Optional[list] = None
    decision: Optional[dict] = None
    matched_po_id: Optional[int] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    invoice: Optional[InvoiceOut] = None

    model_config = {"from_attributes": True}


class RunListOut(BaseModel):
    id: int
    invoice_id: int
    status: str
    extraction_method: Optional[str] = None
    decision: Optional[dict] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    invoice: Optional[InvoiceOut] = None

    model_config = {"from_attributes": True}


# ── Dashboard schemas ───────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_processed: int
    approved_count: int
    review_count: int
    rejected_count: int
    recent_runs: list


# ── Settings schemas ────────────────────────────────────────────────────────
class SettingOut(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    key: str
    value: str


class SettingsBulkUpdate(BaseModel):
    settings: list[SettingUpdate]


# ── Upload response ─────────────────────────────────────────────────────────
class UploadResponse(BaseModel):
    run_id: int
    invoice_id: int
    status: str
    decision: Optional[dict] = None
    message: str
