from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import date, datetime

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access, get_project_and_verify_write_access
from app.models.user import User, UserRole
from app.services.worker_service import WorkerService
from app.services.report_exporter import ReportExporter

router = APIRouter(prefix="/workers", tags=["workers"])

@router.post("", response_model=schemas.WorkerResponse, status_code=status.HTTP_201_CREATED)
def create_worker(
    req: schemas.WorkerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Creates a worker profile and registers their skills (Admin/PM)."""
    return WorkerService.create_worker(db, req)

@router.get("", response_model=List[schemas.WorkerResponse])
def get_workers(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Lists all registered workers (All roles)."""
    return WorkerService.get_workers(db)

@router.put("/{id}", response_model=schemas.WorkerResponse)
def update_worker(
    id: int,
    req: schemas.WorkerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Updates worker details (Admin/PM)."""
    updated = WorkerService.update_worker(db, id, req)
    if not updated:
        raise HTTPException(status_code=404, detail="Worker profile not found.")
    return updated

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worker(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Deletes a worker permanently (Admin/PM)."""
    success = WorkerService.delete_worker(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Worker profile not found.")
    return None

@router.post("/shift-planner", response_model=schemas.ShiftPlannerResponse)
def run_shift_planner(
    req: schemas.ShiftPlannerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Triggers the worker agent shift planners (Admin/PM)."""
    _ = get_project_and_verify_write_access(req.project_id, db, current_user)
    return WorkerService.optimize_and_save_shift_plan(db, req)

@router.get("/schedules/{project_id}", response_model=List[schemas.WorkerScheduleResponse])
def get_project_schedules(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Fetches active shifts allocated to a project (All roles)."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    return WorkerService.get_project_schedules(db, project_id)

@router.get("/worker-report/{project_id}")
def download_worker_schedule_report_pdf(
    project_id: int,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Streams a compiled worker shift schedule PDF report (All roles)."""
    project = get_project_and_verify_view_access(project_id, db, current_user)
    
    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be YYYY-MM-DD format.")

    # Generate schedules list using optimized service parameters
    # Run optimizer node silently to generate recommendations text
    plan_data = WorkerService.optimize_and_save_shift_plan(db, schemas.ShiftPlannerRequest(
        project_id=project_id,
        start_date=s_date,
        end_date=e_date
    ))
    
    schedules = WorkerService.get_project_schedules(db, project_id)
    
    pdf_buffer = ReportExporter.generate_worker_report_pdf(
        project_name=project.project_name,
        schedules=schedules,
        shortages=plan_data.get("shortage_warnings", []),
        summary=plan_data.get("optimization_summary", "")
    )
    
    filename = f"worker_shifts_project_{project_id}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
