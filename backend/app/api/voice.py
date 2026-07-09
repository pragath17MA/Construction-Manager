import os
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access
from app.models.user import User
from app.services.voice_service import VoiceService
from app.models.voice import VoiceCommandLog

router = APIRouter(tags=["voice"])

@router.post("/voice/command", response_model=schemas.VoiceCommandResponse)
async def process_voice_control_command(
    project_id: Optional[int] = Form(None),
    command_text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Processes a voice command.
    Accepts text input, or an audio file upload (which will be transcribed).
    Queries corresponding metrics and returns response narrative + synthesized audio response.
    """
    if project_id:
        _ = get_project_and_verify_view_access(project_id, db, current_user)

    temp_audio_path = None
    try:
        # 1. If audio file is uploaded, save it temporarily to disk
        if audio:
            upload_dir = os.path.join("uploads", "voice", "incoming")
            os.makedirs(upload_dir, exist_ok=True)
            
            # Use timestamp to avoid collisions
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            ext = os.path.splitext(audio.filename)[1] or ".wav"
            temp_audio_path = os.path.join(upload_dir, f"cmd_{timestamp}{ext}")
            
            with open(temp_audio_path, "wb") as buffer:
                shutil.copyfileobj(audio.file, buffer)
        
        # 2. Process command using voice service
        log_entry = VoiceService.process_voice_command(
            db=db,
            user_id=current_user.id,
            project_id=project_id,
            audio_path=temp_audio_path,
            command_text=command_text
        )
        
        # 3. Formulate response model
        audio_url = None
        if log_entry.audio_path:
            audio_url = f"/api/voice/audio/{os.path.basename(log_entry.audio_path)}"
            
        return schemas.VoiceCommandResponse(
            command_text=log_entry.command_text,
            response_text=log_entry.response_text,
            audio_url=audio_url
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    finally:
        # Clean up incoming temp audio file if needed, but Whisper might still read it,
        # so we can keep it or delete it. Let's delete if successfully transcribed
        pass

@router.get("/voice/history/{project_id}", response_model=List[schemas.VoiceHistoryResponse])
def get_project_voice_logs(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Retrieves all voice command history logs for a project."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    return VoiceService.get_history(db, project_id)

@router.get("/voice/audio/{filename}")
def serve_synthesized_response_audio(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Serves response synthesized audio files securely."""
    # Find log entry matching this filename to verify view access permissions
    filename = os.path.basename(filename)
    audio_path = os.path.join("uploads", "voice", filename)
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found on disk.")
        
    log_entry = db.query(VoiceCommandLog).filter(VoiceCommandLog.audio_path == audio_path).first()
    if log_entry and log_entry.project_id:
        _ = get_project_and_verify_view_access(log_entry.project_id, db, current_user)
        
    return FileResponse(audio_path, media_type="audio/wav")
