import os
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access
from app.models.user import User
from app.services.report_center_service import ReportCenterService

router = APIRouter(tags=["reports"])

@router.get("/reports/download")
def download_custom_report(
    project_id: int = Query(...),
    report_type: str = Query(..., pattern="^(budget|material|worker|attendance|risk|invoice|image_analysis|drawing|project_summary|executive|progress)$"),
    report_format: str = Query("pdf", pattern="^(pdf|csv|excel)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Downloads custom generated construction reports.
    Formats supported: PDF, CSV, Excel.
    Report types: budget, material, worker, attendance, risk, invoice, image_analysis, drawing, project_summary, executive, progress.
    """
    # 1. Verify view permission on project
    _ = get_project_and_verify_view_access(project_id, db, current_user)

    filename_base = f"{report_type}_report_project_{project_id}"

    try:
        if report_format == "pdf":
            pdf_buffer = ReportCenterService.generate_pdf_report(db, project_id, report_type)
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename_base}.pdf"}
            )
            
        else:
            # CSV or Excel (CSV structure read natively by Excel)
            csv_content = ReportCenterService.generate_csv_report(db, project_id, report_type)
            mime = "text/csv"
            ext = "csv"
            if report_format == "excel":
                mime = "application/vnd.ms-excel"
                ext = "csv" # Save as CSV since standard tables open in Excel
                
            return Response(
                content=csv_content,
                media_type=mime,
                headers={"Content-Disposition": f"attachment; filename={filename_base}.{ext}"}
            )
            
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate report: {str(e)}")
