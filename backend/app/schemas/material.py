from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

# Material Schemas
class MaterialBase(BaseModel):
    material_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=50)
    unit_price: Decimal = Field(..., gt=0)

class MaterialCreate(MaterialBase):
    project_id: int

class MaterialResponse(MaterialBase):
    id: int
    project_id: int
    total_cost: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Inventory Schemas
class InventoryBase(BaseModel):
    material_name: str = Field(..., min_length=1, max_length=255)
    quantity_available: Decimal = Field(..., ge=0)
    quantity_reserved: Decimal = Field(0.0, ge=0)
    unit: str = Field(..., min_length=1, max_length=50)
    warehouse_capacity: Decimal = Field(..., gt=0)

class InventoryCreate(InventoryBase):
    pass

class InventoryResponse(InventoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class InventoryUpdateRequest(BaseModel):
    material_name: str = Field(..., min_length=1, max_length=255)
    quantity_change: Decimal = Field(...)  # Can be positive (adding stock) or negative (drawing stock)

# Supplier Schemas
class SupplierBase(BaseModel):
    supplier_name: str = Field(..., min_length=1, max_length=255)
    rating: Decimal = Field(5.0, ge=1.0, le=5.0)
    contact_info: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    active: bool = Field(True)

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# PurchaseOrder Schemas
class PurchaseOrderBase(BaseModel):
    project_id: int
    supplier_id: int
    material_name: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    total_cost: Decimal
    status: str
    ordered_at: datetime
    supplier: SupplierResponse

    model_config = ConfigDict(from_attributes=True)

# AI Material Estimator Agent Request/Response
class MaterialEstimateRequest(BaseModel):
    project_id: int
    area_sqft: Decimal = Field(..., gt=0)
    floors: int = Field(1, gt=0)
    building_type: str = Field("Residential", min_length=1, max_length=100) # Residential, Commercial, Industrial
    rooms: int = Field(1, ge=0)
    timeline_months: int = Field(6, gt=0)
    budget: Decimal = Field(1000000.0, gt=0)
    project_category: str = Field("Residential", min_length=1, max_length=100)

class SupplierRecommendation(BaseModel):
    material_name: str
    supplier_id: int
    supplier_name: str
    rating: Decimal
    unit_price: Decimal
    availability_status: str

class MaterialEstimateResponse(BaseModel):
    project_id: int
    materials: List[MaterialResponse]
    low_stock_warnings: List[str]
    supplier_recommendations: List[SupplierRecommendation]
    optimization_summary: str
