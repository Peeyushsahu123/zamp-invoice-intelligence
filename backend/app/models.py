"""SQLAlchemy ORM models."""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class VendorStatus(str, enum.Enum):
    APPROVED = "approved"
    PENDING = "pending"
    SUSPENDED = "suspended"


class POStatus(str, enum.Enum):
    OPEN = "open"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    CLOSED = "closed"


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    MATCHING = "matching"
    DECIDING = "deciding"
    COMPLETED = "completed"
    FAILED = "failed"


class DecisionStatus(str, enum.Enum):
    APPROVED = "APPROVED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    tax_id = Column(String(50), unique=True, nullable=False)
    status = Column(SQLEnum(VendorStatus), default=VendorStatus.PENDING, nullable=False)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    description = Column(Text, nullable=True)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(SQLEnum(POStatus), default=POStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    tolerance_percent = Column(Float, default=2.0)

    vendor = relationship("Vendor", back_populates="purchase_orders")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), nullable=True, index=True)
    vendor_name = Column(String(255), nullable=True)
    vendor_tax_id = Column(String(50), nullable=True)
    po_reference = Column(String(50), nullable=True)
    invoice_date = Column(String(50), nullable=True)
    currency = Column(String(10), default="USD")
    subtotal = Column(Float, nullable=True)
    tax_amount = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True)
    line_items = Column(JSON, nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    processing_runs = relationship("ProcessingRun", back_populates="invoice")


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    status = Column(SQLEnum(RunStatus), default=RunStatus.PENDING, nullable=False)
    extraction_method = Column(String(50), nullable=True)
    stages = Column(JSON, nullable=True)  # list of {name, status, started_at, completed_at, details}
    extracted_data = Column(JSON, nullable=True)
    validation_results = Column(JSON, nullable=True)
    decision = Column(JSON, nullable=True)
    matched_po_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    invoice = relationship("Invoice", back_populates="processing_runs")
    validation_records = relationship("ValidationResult", back_populates="run")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("processing_runs.id"), nullable=False)
    rule_name = Column(String(100), nullable=False)
    passed = Column(Boolean, nullable=False)
    message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)

    run = relationship("ProcessingRun", back_populates="validation_records")


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
