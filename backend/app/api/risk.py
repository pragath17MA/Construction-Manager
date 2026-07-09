from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access, get_project_and_verify_write_access
from app.models.user import User, UserRole
from app.services.risk_service import RiskService
from app.services.report_generator import ReportGenerator

router = APIRouter(tags=["risk"])

@router.post("/risk/analyze", response_model=schemas.RiskAnalysisResponse, status_code=status.HTTP_201_CREATED)
def trigger_risk_prediction(
    req: schemas.RiskAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Triggers composite risk scoring analysis workflow (Admin/PM)."""
    _ = get_project_and_verify_write_access(req.project_id, db, current_user)
    return RiskService.analyze_project_risks(db, req.project_id)

@router.get("/risk/project/{project_id}", response_model=schemas.RiskAnalysisResponse)
def get_project_risk_assessment(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Retrieves current risk parameters (All roles)."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    risk_data = RiskService.get_current_risk(db, project_id)
    if not risk_data:
        # Run analyze implicitly if no record exists
        return RiskService.analyze_project_risks(db, project_id)
    return risk_data

@router.get("/risk/history/{project_id}", response_model=List[schemas.RiskHistoryResponse])
def get_project_risk_history_ledger(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Retrieves pagination list of historical risk audits (All roles)."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    return RiskService.get_risk_history(db, project_id, skip=skip, limit=limit)

@router.get("/reports/risk/{project_id}")
def download_project_risk_report(
    project_id: int,
    format: str = Query("pdf", pattern="^(pdf|excel)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Generates and returns the compiled Risk Report in PDF or CSV format (All roles)."""
    project = get_project_and_verify_view_access(project_id, db, current_user)
    
    risk_data = RiskService.get_current_risk(db, project_id)
    if not risk_data:
        risk_data = RiskService.analyze_project_risks(db, project_id)
        
    if format == "excel":
        history = RiskService.get_risk_history(db, project_id, limit=100)
        csv_content = ReportGenerator.generate_risk_excel_csv(history)
        filename = f"risk_report_project_{project_id}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        pdf_buffer = ReportGenerator.generate_risk_report_pdf(project.project_name, risk_data)
        from fastapi.responses import StreamingResponse
        filename = f"risk_report_project_{project_id}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
