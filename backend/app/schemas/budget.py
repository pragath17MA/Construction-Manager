from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class MaterialInputItem(BaseModel):
    material: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)

class LaborInputItem(BaseModel):
    worker_type: str = Field(..., min_length=1, max_length=255)
    worker_count: int = Field(..., gt=0)
    daily_rate: Decimal = Field(..., gt=0)
    days: int = Field(..., gt=0)

class EquipmentInputItem(BaseModel):
    equipment_name: str = Field(..., min_length=1, max_length=255)
    daily_rate: Decimal = Field(..., gt=0)
    days_used: int = Field(..., gt=0)

class BudgetEstimateRequest(BaseModel):
    project_id: int
    area_sqft: Decimal = Field(..., gt=0)
    currency: str = Field("INR", min_length=3, max_length=3)
    materials: List[MaterialInputItem]
    labor: List[LaborInputItem]
    equipment: List[EquipmentInputItem]

class BudgetItemResponse(BaseModel):
    id: int
    budget_id: int
    category: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal

    model_config = ConfigDict(from_attributes=True)

class BudgetResponse(BaseModel):
    id: int
    project_id: int
    estimated_cost: Decimal
    optimized_cost: Decimal
    currency: str
    ai_summary: Optional[str] = None
    ai_recommendations: Optional[str] = None
    created_at: datetime
    items: List[BudgetItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

class LaborCostResponse(BaseModel):
    id: int
    project_id: int
    worker_type: str
    worker_count: int
    daily_rate: Decimal
    days: int
    total_cost: Decimal

    model_config = ConfigDict(from_attributes=True)

class EquipmentCostResponse(BaseModel):
    id: int
    project_id: int
    equipment_name: str
    days_used: int
    daily_rate: Decimal
    total_cost: Decimal

    model_config = ConfigDict(from_attributes=True)

class BudgetDetailResponse(BaseModel):
    budget: BudgetResponse
    labor_costs: List[LaborCostResponse]
    equipment_costs: List[EquipmentCostResponse]

class BudgetItemUpdate(BaseModel):
    id: Optional[int] = None
    category: str
    description: str
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)

class BudgetUpdateRequest(BaseModel):
    estimated_cost: Optional[Decimal] = Field(None, gt=0)
    optimized_cost: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    items: Optional[List[BudgetItemUpdate]] = None

class PaginatedBudgets(BaseModel):
    total: int
    items: List[BudgetResponse]
    page: int
    size: int
