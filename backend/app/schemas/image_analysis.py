from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator
import json

class SiteImageAnalysisCreate(BaseModel):
    project_id: int
    site_image_id: int

class SiteImageAnalysisResponse(BaseModel):
    id: int
    project_id: int
    site_image_id: int
    progress_percentage: Decimal
    construction_stage: str
    safety_issues: List[str] = []
    recommendations: Optional[str] = None
    annotated_image_path: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('safety_issues', mode='before')
    @classmethod
    def parse_safety_issues(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [v] if v else []
        elif isinstance(v, list):
            return v
        return []
