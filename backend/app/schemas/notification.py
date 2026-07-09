from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class NotificationLogResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    user_id: int
    alert_type: str
    channel: str
    recipient: str
    message: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
