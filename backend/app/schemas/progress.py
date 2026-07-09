from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

# Milestone Schemas
class MilestoneBase(BaseModel):
    milestone_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    planned_end_date: date
    actual_end_date: Optional[date] = None
    completion_percentage: Decimal = Field(Decimal("0.0"), ge=0, le=100)
    status: str = Field("Planning", max_length=50) # Planning, On-Time, At-Risk, Delayed, Completed

class MilestoneCreate(MilestoneBase):
    project_id: int

class MilestoneResponse(MilestoneBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Daily Log Schemas
class DailyLogBase(BaseModel):
    log_date: date
    update_text: str = Field(..., min_length=5)
    image_path: Optional[str] = None

class DailyLogCreate(DailyLogBase):
    project_id: int

class DailyLogResponse(DailyLogBase):
    id: int
    project_id: int
    submitted_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Progress Report Schemas
class ProgressReportBase(BaseModel):
    report_type: str = Field(..., max_length=50) # Daily, Weekly, Monthly
    start_date: date
    end_date: date
    overall_completion_percentage: Decimal = Field(Decimal("0.0"), ge=0, le=100)
    milestones_completed_count: int = Field(0, ge=0)
    budget_spent_so_far: Decimal = Field(Decimal("0.0"), ge=0)
    resource_utilization_rate: Decimal = Field(Decimal("0.0"), ge=0, le=100)
    variance_status: str = Field("On-Track", max_length=50) # On-Track, Minor Variance, Critical Delay
    ai_summary: Optional[str] = None

class ProgressReportCreate(ProgressReportBase):
    project_id: int

class ProgressReportResponse(ProgressReportBase):
    id: int
    project_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProgressSummaryResponse(BaseModel):
    project_id: int
    overall_completion: Decimal
    planned_vs_actual_variance: int # variance in days
    milestones: List[MilestoneResponse]
    latest_logs: List[DailyLogResponse]
    reports: List[ProgressReportResponse]
    budget_spent: Decimal
    budget_limit: Decimal
    resource_utilization: Decimal
