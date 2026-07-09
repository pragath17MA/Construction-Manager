from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.models.user import User, UserRole
from app.services.worker_service import WorkerService
from app.services.report_exporter import ReportExporter

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("", response_model=schemas.AttendanceResponse)
def log_worker_attendance(
    req: schemas.AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Logs attendance for a worker.
    - Site Engineers, PMs, and Admins can log attendance.
    """
    # Site Engineers can log progress and attendance logs
    return WorkerService.log_attendance(db, req)

@router.get("", response_model=List[schemas.AttendanceResponse])
def get_attendance_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Lists attendance logs (All roles)."""
    return WorkerService.get_attendance(db)

@router.post("/leave", response_model=schemas.LeaveRequestResponse)
def submit_leave_request(
    req: schemas.LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Submits worker leave request (All roles)."""
    return WorkerService.create_leave_request(db, req)

@router.get("/leave", response_model=List[schemas.LeaveRequestResponse])
def get_leave_requests_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Lists worker leave request reviews (All roles)."""
    return WorkerService.get_leave_requests(db)

@router.put("/leave/{id}/approve", response_model=schemas.LeaveRequestResponse)
def approve_leave_request(
    id: int,
    req: schemas.LeaveApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Approves or Rejects a pending leave request (Admin/PM)."""
    updated = WorkerService.update_leave_status(db, id, req.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Leave request not found.")
    return updated

@router.get("/csv")
def download_attendance_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Streams attendance logs as a downloadable CSV."""
    logs = WorkerService.get_attendance(db)
    csv_content = ReportExporter.generate_attendance_csv(logs)
    
    filename = "attendance_logs.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
