from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, EmailStr

# Worker Skill Schemas
class WorkerSkillBase(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=255)
    proficiency_level: str = Field("Intermediate", min_length=1, max_length=50) # Beginner, Intermediate, Expert

class WorkerSkillCreate(WorkerSkillBase):
    worker_id: int

class WorkerSkillResponse(WorkerSkillBase):
    id: int
    worker_id: int

    model_config = ConfigDict(from_attributes=True)

# Worker Schemas
class WorkerBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=50)
    role_title: str = Field(..., min_length=1, max_length=100) # Mason, Electrician, Plumber, Supervisor, Operator, Carpenter, Painter, Contractor, Engineer
    worker_type: str = Field(..., min_length=1, max_length=100) # Skilled, Semi-Skilled, Unskilled
    wage_rate: Decimal = Field(..., gt=0)
    active: bool = Field(True)

class WorkerCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=50)
    role_title: str = Field(..., min_length=1, max_length=100)
    worker_type: str = Field(..., min_length=1, max_length=100)
    wage_rate: Decimal = Field(..., gt=0)
    skills: List[WorkerSkillBase] = []

class WorkerResponse(WorkerBase):
    id: int
    skills: List[WorkerSkillResponse] = []

    model_config = ConfigDict(from_attributes=True)

# Worker Schedule Schemas
class WorkerScheduleBase(BaseModel):
    worker_id: int
    project_id: int
    start_date: date
    end_date: date
    shift_type: str = Field("Day", min_length=1, max_length=50) # Day, Night

class WorkerScheduleCreate(WorkerScheduleBase):
    pass

class WorkerScheduleResponse(WorkerScheduleBase):
    id: int
    assigned_at: datetime
    worker: WorkerResponse

    model_config = ConfigDict(from_attributes=True)

# Attendance Schemas
class AttendanceBase(BaseModel):
    worker_id: int
    date: date
    status: str = Field(..., min_length=1, max_length=50) # Present, Absent, Late
    hours_worked: Decimal = Field(8.0, ge=0, le=24)
    overtime_hours: Decimal = Field(0.0, ge=0, le=24)

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceResponse(AttendanceBase):
    id: int
    worker: WorkerResponse

    model_config = ConfigDict(from_attributes=True)

# Leave Request Schemas
class LeaveRequestBase(BaseModel):
    worker_id: int
    start_date: date
    end_date: date
    leave_type: str = Field(..., min_length=1, max_length=50) # Sick, Casual, Earned
    reason: Optional[str] = Field(None, max_length=1000)

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestResponse(LeaveRequestBase):
    id: int
    status: str # Pending, Approved, Rejected
    worker: WorkerResponse

    model_config = ConfigDict(from_attributes=True)

class LeaveApprovalRequest(BaseModel):
    status: str = Field(..., min_length=1, max_length=50) # Approved, Rejected

# Shift Plan Schemas
class ShiftPlanBase(BaseModel):
    project_id: int
    plan_name: str = Field(..., min_length=1, max_length=255)
    date: date
    shift_type: str = Field(..., min_length=1, max_length=50) # Day, Night
    requirements_description: Optional[str] = None

class ShiftPlanCreate(ShiftPlanBase):
    pass

class ShiftPlanResponse(ShiftPlanBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# AI Shift Planner Agent Request/Response
class ShiftPlannerRequest(BaseModel):
    project_id: int
    start_date: date
    end_date: date

class ShiftPlannerResponse(BaseModel):
    project_id: int
    plans: List[ShiftPlanResponse]
    shortage_warnings: List[str]
    optimization_summary: str
