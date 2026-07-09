import os
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access
from app.models.user import User
from app.services.chat_service import ChatService
from app.services.voice_service import VoiceService

router = APIRouter(tags=["chat"])

@router.post("/chat/sessions", response_model=schemas.ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_new_chat_session(
    req: schemas.ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Creates a new conversational chat session."""
    if req.project_id:
        _ = get_project_and_verify_view_access(req.project_id, db, current_user)
    return ChatService.create_session(db, current_user.id, req.project_id, req.session_name)

@router.get("/chat/sessions", response_model=List[schemas.ChatSessionResponse])
def list_user_chat_sessions(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Lists history conversational sessions for user, optionally filtered by project."""
    if project_id:
        _ = get_project_and_verify_view_access(project_id, db, current_user)
    return ChatService.list_sessions(db, current_user.id, project_id)

@router.get("/chat/sessions/{session_id}", response_model=schemas.ChatSessionDetailResponse)
def get_chat_session_details(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Retrieves full list of message logs for a session."""
    session = ChatService.get_session(db, session_id, current_user.id)
    return session

@router.delete("/chat/sessions/{session_id}", status_code=status.HTTP_200_OK)
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Deletes a chat session permanently."""
    success = ChatService.delete_session(db, session_id, current_user.id)
    return {"message": "Chat session deleted successfully.", "success": success}

@router.post("/chat/sessions/{session_id}/message", response_model=schemas.ChatMessageResponse)
def send_text_chat_query(
    session_id: int,
    req: schemas.ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Submits a text-based conversational inquiry to the AI agent."""
    try:
        reply = ChatService.process_chat_query(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            query_text=req.message_text
        )
        return reply
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat query: {str(e)}")

@router.post("/chat/sessions/{session_id}/audio-message", response_model=schemas.ChatMessageResponse)
def send_voice_chat_query(
    session_id: int,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Transcribes uploaded voice query audio and processes the transcribed query."""
    # Ensure session exists and user has access
    session = ChatService.get_session(db, session_id, current_user.id)
    
    temp_path = None
    try:
        # Save incoming audio file
        upload_dir = os.path.join("uploads", "chat", "voice")
        os.makedirs(upload_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        ext = os.path.splitext(audio.filename)[1] or ".wav"
        temp_path = os.path.join(upload_dir, f"chat_cmd_{timestamp}{ext}")
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
            
        # Transcribe audio using Module 11 speech service
        transcribed_text = VoiceService.transcribe_audio(temp_path)
        
        # Process query
        reply = ChatService.process_chat_query(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            query_text=transcribed_text
        )
        return reply
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice chat query execution failed: {str(e)}")
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

@router.post("/chat/sessions/{session_id}/image-message", response_model=schemas.ChatMessageResponse)
def send_image_chat_query(
    session_id: int,
    query_text: str = Form("Analyze this site image and identify hazards."),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Uploads a site photo for visual threat auditing, then answers the query incorporating analysis findings."""
    session = ChatService.get_session(db, session_id, current_user.id)
    
    temp_path = None
    try:
        # Save incoming image file
        upload_dir = os.path.join("uploads", "chat", "images")
        os.makedirs(upload_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        ext = os.path.splitext(image.filename)[1] or ".jpg"
        temp_path = os.path.join(upload_dir, f"chat_img_{timestamp}{ext}")
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        # Process query with visual attachment
        reply = ChatService.process_chat_query(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            query_text=query_text,
            image_path=temp_path
        )
        return reply
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image visual chat query execution failed: {str(e)}")
