from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access
from app.models.user import User
from app.models.notification import NotificationLog
from app.schemas.notification import NotificationLogResponse

router = APIRouter(tags=["notifications"])

@router.get("/notifications/history/{project_id}", response_model=List[NotificationLogResponse])
def get_notification_history(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Retrieves chronological history logs of alert notifications dispatched for a project.
    - Requires view access to the project.
    """
    # Verify view permissions
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    
    logs = db.query(NotificationLog).filter(
        NotificationLog.project_id == project_id
    ).order_by(NotificationLog.created_at.desc()).all()
    
    return logs
