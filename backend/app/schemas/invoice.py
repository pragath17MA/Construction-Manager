from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

class InvoiceItemBase(BaseModel):
    description: str
    quantity: Decimal = Field(default=Decimal("0.0"))
    unit_price: Decimal = Field(default=Decimal("0.0"))
    total_price: Decimal = Field(default=Decimal("0.0"))
    material_id: Optional[int] = None

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItemResponse(InvoiceItemBase):
    id: int
    invoice_id: int

    model_config = ConfigDict(from_attributes=True)

class InvoiceComparisonResponse(BaseModel):
    id: int
    invoice_id: int
    project_id: int
    item_id: int
    budgeted_amount: Decimal
    actual_amount: Decimal
    variance: Decimal
    analysis_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OCRLogResponse(BaseModel):
    id: int
    invoice_id: int
    log_level: str
    message: str
    processing_time_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InvoiceResponse(BaseModel):
    id: int
    project_id: int
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    vendor_name: Optional[str] = None
    vendor_gst: Optional[str] = None
    total_amount: Decimal
    tax_amount: Decimal
    status: str
    ocr_raw_text: Optional[str] = None
    image_path: Optional[str] = None
    confidence_score: Decimal
    is_duplicate: bool
    duplicate_parent_id: Optional[int] = None
    created_at: datetime
    items: List[InvoiceItemResponse] = []
    comparisons: List[InvoiceComparisonResponse] = []

    model_config = ConfigDict(from_attributes=True)

class InvoiceAnalysisRequest(BaseModel):
    invoice_id: int

class InvoiceAnalysisResponse(BaseModel):
    invoice_id: int
    is_duplicate: bool
    duplicate_warning: Optional[str] = None
    fraud_risk_score: Decimal = Field(default=Decimal("0.0"))
    fraud_risk_details: List[str] = []
    budget_variance_alerts: List[str] = []
    ai_fraud_recommendations: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class InvoiceReportResponse(BaseModel):
    invoice_id: int
    project_name: str
    vendor_name: Optional[str] = None
    total_amount: Decimal
    is_duplicate: bool
    fraud_risk_score: Decimal
    alerts_count: int
    report_notes: str
