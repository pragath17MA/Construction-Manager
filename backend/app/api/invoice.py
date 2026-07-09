import os
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, BackgroundTasks, Query, Response
from sqlalchemy.orm import Session
from typing import List

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access, get_project_and_verify_write_access
from app.models.user import User, UserRole
from app.services.ocr_service import InvoiceService
from app.services.report_generator import ReportGenerator
from app.core.files import validate_and_save_file

router = APIRouter(tags=["invoices"])

@router.post("/invoice/upload", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    background_tasks: BackgroundTasks,
    project_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Uploads invoice PDF/Image and triggers background OCR parsing (Admin/PM)."""
    project = get_project_and_verify_write_access(project_id, db, current_user)
    
    # Dynamically determine file category based on extension
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    category = "image" if ext in [".png", ".jpg", ".jpeg", ".webp"] else "document"
    
    saved_path = await validate_and_save_file(file, category)
    
    # Save record
    invoice = InvoiceService.create_invoice(
        db=db,
        project_id=project_id,
        image_path=saved_path
    )
    
    # Process OCR in background
    background_tasks.add_task(InvoiceService.process_ocr, db, invoice.id)
    
    return invoice

@router.get("/invoice/{id}", response_model=schemas.InvoiceResponse)
def get_invoice_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Retrieves metadata, items, and comparisons for an invoice (All roles)."""
    invoice = InvoiceService.get_invoice(db, id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    _ = get_project_and_verify_view_access(invoice.project_id, db, current_user)
    return invoice

@router.post("/invoice/analyze", response_model=schemas.InvoiceAnalysisResponse)
def analyze_invoice_reconciliation(
    req: schemas.InvoiceAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Triggers invoice audit checks (duplicate check, budget overruns, and AI fraud checks) (Admin/PM)."""
    invoice = InvoiceService.get_invoice(db, req.invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    _ = get_project_and_verify_write_access(invoice.project_id, db, current_user)
    return InvoiceService.analyze_invoice(db, req.invoice_id)

@router.get("/invoice/project/{project_id}", response_model=List[schemas.InvoiceResponse])
def get_project_invoices_list(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Lists invoices associated with a project (All roles)."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    return InvoiceService.list_project_invoices(db, project_id)

@router.get("/invoice/report/{id}")
def download_invoice_analysis_report(
    id: int,
    format: str = Query("pdf", pattern="^(pdf|excel)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Generates and returns invoice audit reports in PDF or CSV format (All roles)."""
    invoice = InvoiceService.get_invoice(db, id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    project = get_project_and_verify_view_access(invoice.project_id, db, current_user)
    
    # Run analysis dynamically to ensure comparisons exist
    analysis_data = InvoiceService.analyze_invoice(db, id)

    if format == "excel":
        csv_content = ReportGenerator.generate_invoice_excel_csv(invoice, invoice.comparisons)
        filename = f"invoice_report_{id}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        pdf_buffer = ReportGenerator.generate_invoice_report_pdf(
            project.project_name, invoice, analysis_data
        )
        from fastapi.responses import StreamingResponse
        filename = f"invoice_report_{id}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
