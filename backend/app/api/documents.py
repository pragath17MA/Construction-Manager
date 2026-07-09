from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access, get_project_and_verify_write_access
from app.models.user import User, UserRole
from app.services.rag_service import RAGService
from app.core.files import validate_and_save_file

router = APIRouter(tags=["documents"])

@router.post("/documents/upload", response_model=schemas.ConstructionDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_construction_drawing(
    background_tasks: BackgroundTasks,
    project_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Uploads construction drawing specification PDF and triggers background indexing (Admin/PM)."""
    _ = get_project_and_verify_write_access(project_id, db, current_user)
    
    # Save physical PDF
    saved_path = await validate_and_save_file(file, "document")
    
    # Record database entry
    doc = RAGService.create_document(
        db=db,
        project_id=project_id,
        file_name=file.filename,
        file_type=file.content_type or "application/pdf",
        file_path=saved_path
    )
    
    # Queue background parsing
    background_tasks.add_task(RAGService.process_document, db, doc.id)
    
    return doc

@router.post("/documents/query", response_model=schemas.DocumentQueryResponse)
def query_drawing_specifications(
    req: schemas.DocumentQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Performs semantic vector search across drawings and answers construction queries (All roles)."""
    _ = get_project_and_verify_view_access(req.project_id, db, current_user)
    return RAGService.query_documents(db, req.project_id, req.query_text, req.limit)

@router.get("/documents/{id}", response_model=schemas.ConstructionDocumentDetailResponse)
def get_document_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Retrieves metadata and page text segments for a specific document (All roles)."""
    doc = RAGService.get_document_details(db, id)
    if not doc:
        raise HTTPException(status_code=404, detail="Construction document not found.")
    _ = get_project_and_verify_view_access(doc.project_id, db, current_user)
    return doc

@router.get("/documents/project/{project_id}", response_model=List[schemas.ConstructionDocumentResponse])
def get_project_documents_list(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Lists drawings registered to a project (All roles)."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    return RAGService.list_project_documents(db, project_id)
