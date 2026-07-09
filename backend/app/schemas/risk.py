from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class WeatherDataResponse(BaseModel):
    id: int
    project_id: int
    location: str
    temperature: Optional[Decimal] = None
    wind_speed: Optional[Decimal] = None
    precipitation: Optional[Decimal] = None
    humidity: Optional[Decimal] = None
    weather_description: Optional[str] = None
    alerts: Optional[str] = None
    cached_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DelayPredictionResponse(BaseModel):
    id: int
    project_id: int
    probability: Decimal
    predicted_delay_days: int
    variance_days: int
    root_causes: Optional[str] = None
    recovery_recommendations: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RiskResponse(BaseModel):
    id: int
    project_id: int
    risk_score: int
    delay_probability: Decimal
    executive_summary: Optional[str] = None
    
    # 8 Risk Categories
    weather_risk_severity: str
    material_risk_severity: str
    budget_risk_severity: str
    worker_risk_severity: str
    equipment_risk_severity: str
    supplier_risk_severity: str
    safety_risk_severity: str
    timeline_risk_severity: str
    
    ai_mitigation_suggestions: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RiskHistoryResponse(BaseModel):
    id: int
    project_id: int
    risk_score: int
    delay_probability: Decimal
    executive_summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RiskAnalysisRequest(BaseModel):
    project_id: int

class RiskAnalysisResponse(BaseModel):
    risk: RiskResponse
    delay_prediction: DelayPredictionResponse
    weather: Optional[WeatherDataResponse] = None
