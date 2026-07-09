from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Date, Numeric, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    invoice_number = Column(String, nullable=True)
    invoice_date = Column(Date, nullable=True)
    vendor_name = Column(String, nullable=True)
    vendor_gst = Column(String, nullable=True)
    total_amount = Column(Numeric(precision=12, scale=2), default=0.0)
    tax_amount = Column(Numeric(precision=12, scale=2), default=0.0)
    status = Column(String, default="Pending") # Pending, Processing, Completed, Duplicate-Alert, Fraud-Alert, Error
    ocr_raw_text = Column(Text, nullable=True)
    image_path = Column(String, nullable=True)
    confidence_score = Column(Numeric(precision=5, scale=2), default=0.0)
    is_duplicate = Column(Boolean, default=False)
    duplicate_parent_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    comparisons = relationship("InvoiceComparison", back_populates="invoice", cascade="all, delete-orphan")
    ocr_logs = relationship("OCRLog", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    description = Column(String, nullable=False)
    quantity = Column(Numeric(precision=10, scale=2), default=0.0)
    unit_price = Column(Numeric(precision=12, scale=2), default=0.0)
    total_price = Column(Numeric(precision=12, scale=2), default=0.0)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    material = relationship("Material")

class InvoiceComparison(Base):
    __tablename__ = "invoice_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, ForeignKey("invoice_items.id", ondelete="CASCADE"), nullable=False)
    budgeted_amount = Column(Numeric(precision=12, scale=2), default=0.0)
    actual_amount = Column(Numeric(precision=12, scale=2), default=0.0)
    variance = Column(Numeric(precision=12, scale=2), default=0.0)
    analysis_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="comparisons")
    project = relationship("Project")
    item = relationship("InvoiceItem")

class OCRLog(Base):
    __tablename__ = "ocr_logs"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    log_level = Column(String, default="INFO") # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    processing_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="ocr_logs")
