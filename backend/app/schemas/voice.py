from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class VoiceCommandRequest(BaseModel):
    project_id: Optional[int] = None
    command_text: Optional[str] = None  # Text input from chat. If audio is uploaded, this might be empty and handled by Form upload.

class VoiceCommandResponse(BaseModel):
    command_text: str
    response_text: str
    audio_url: Optional[str] = None

class VoiceHistoryResponse(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int] = None
    command_text: str
    response_text: str
    audio_path: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
