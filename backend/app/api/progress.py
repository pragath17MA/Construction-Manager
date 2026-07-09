from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Response, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access, get_project_and_verify_write_access
from app.models.user import User, UserRole
from app.services.progress_service import ProgressService
from app.services.report_generator import ReportGenerator
from app.core.files import validate_and_save_file
from app.models.image_analysis import SiteImageAnalysis
from app.models.voice import VoiceCommandLog

router = APIRouter(tags=["progress"])

@router.post("/progress/update", response_model=schemas.DailyLogResponse)
async def submit_daily_progress_update(
    project_id: int = Form(...),
    log_date: date = Form(...),
    update_text: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Site engineer registers daily updates, optionally uploading site images (All project members)."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    
    saved_path = None
    if file:
        saved_path = await validate_and_save_file(file, "image")
        
    req = schemas.DailyLogCreate(
        project_id=project_id,
        log_date=log_date,
        update_text=update_text,
        image_path=saved_path
    )
    return ProgressService.create_daily_log(db, req, current_user.id)

@router.get("/progress/project/{project_id}", response_model=schemas.ProgressSummaryResponse)
def get_project_progress_cockpit(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Calculates overall milestones progression, variances, and lists logs (All roles)."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    return ProgressService.get_progress_summary(db, project_id)

@router.post("/milestone", response_model=schemas.MilestoneResponse)
def add_or_modify_project_milestone(
    req: schemas.MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Creates or updates milestone deadlines and completion ratios (Admin/PM)."""
    _ = get_project_and_verify_write_access(req.project_id, db, current_user)
    return ProgressService.create_or_update_milestone(db, req)

@router.get("/milestones/{project_id}", response_model=List[schemas.MilestoneResponse])
def get_project_milestones_ledger(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Lists planned project milestones (All roles)."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    return ProgressService.get_milestones(db, project_id)

@router.get("/reports/progress/{project_id}")
def download_project_progress_report(
    project_id: int,
    format: str = Query("pdf", pattern="^(pdf|excel)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Generates and returns Progress monitoring reports in PDF or CSV formats (All roles)."""
    project = get_project_and_verify_view_access(project_id, db, current_user)
    
    progress_data = ProgressService.get_progress_summary(db, project_id)
    
    if format == "excel":
        csv_content = ReportGenerator.generate_progress_excel_csv(
            progress_data["milestones"],
            progress_data["reports"]
        )
        filename = f"progress_report_project_{project_id}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        progress_data["visual_analyses"] = db.query(SiteImageAnalysis).filter(SiteImageAnalysis.project_id == project_id).all()
        progress_data["voice_logs"] = db.query(VoiceCommandLog).filter(VoiceCommandLog.project_id == project_id).order_by(VoiceCommandLog.created_at.desc()).limit(5).all()
        pdf_buffer = ReportGenerator.generate_progress_report_pdf(project.project_name, progress_data)
        from fastapi.responses import StreamingResponse
        filename = f"progress_report_project_{project_id}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
