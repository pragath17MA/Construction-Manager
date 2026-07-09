from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class ChatMessageCreate(BaseModel):
    message_text: str

class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    sender: str
    message_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatSessionCreate(BaseModel):
    project_id: Optional[int] = None
    session_name: Optional[str] = "New Conversation"

class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int] = None
    session_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatSessionDetailResponse(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int] = None
    session_name: str
    created_at: datetime
    messages: List[ChatMessageResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ChatQueryRequest(BaseModel):
    project_id: Optional[int] = None
    query: str
    # If audio is uploaded, voice commands handle transcription first, then call chat.
    # We can also accept optional voice audio or image trigger params.
