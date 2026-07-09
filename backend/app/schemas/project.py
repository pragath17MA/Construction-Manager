from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator, ConfigDict
from app.models.project import ProjectStatus
from app.models.user import UserRole
from app.schemas.user import UserResponse

class ProjectBase(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    client_name: str = Field(..., min_length=1, max_length=255)
    location: str = Field(..., min_length=1, max_length=255)
    start_date: date
    expected_end_date: date
    status: ProjectStatus = ProjectStatus.PLANNING
    budget: Decimal = Field(..., gt=0)

class ProjectCreate(ProjectBase):
    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectCreate":
        if self.expected_end_date <= self.start_date:
            raise ValueError("expected_end_date must be after start_date")
        return self

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    client_name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    expected_end_date: Optional[date] = None
    status: Optional[ProjectStatus] = None
    budget: Optional[Decimal] = Field(None, gt=0)

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectUpdate":
        s_date = self.start_date
        e_date = self.expected_end_date
        if s_date is not None and e_date is not None:
            if e_date <= s_date:
                raise ValueError("expected_end_date must be after start_date")
        return self

class ProjectMemberBase(BaseModel):
    user_id: int
    role: UserRole

class ProjectMemberCreate(ProjectMemberBase):
    pass

class ProjectMemberResponse(ProjectMemberBase):
    id: int
    project_id: int
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(BaseModel):
    id: int
    project_id: int
    file_name: str
    file_type: str
    file_path: str
    uploaded_by: Optional[int]
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DrawingResponse(BaseModel):
    id: int
    project_id: int
    drawing_name: str
    drawing_path: str
    uploaded_by: Optional[int]
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SiteImageResponse(BaseModel):
    id: int
    project_id: int
    image_path: str
    capture_date: date
    uploaded_by: Optional[int]
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectResponse(ProjectBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectDetailResponse(ProjectResponse):
    members: List[ProjectMemberResponse] = []
    documents: List[DocumentResponse] = []
    drawings: List[DrawingResponse] = []
    images: List[SiteImageResponse] = []

    model_config = ConfigDict(from_attributes=True)

class PaginatedProjects(BaseModel):
    total: int
    items: List[ProjectResponse]
    page: int
    size: int
