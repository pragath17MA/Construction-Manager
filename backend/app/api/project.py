from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import os

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.api.deps import get_current_active_user
from app.api.auth_project import get_project_and_verify_view_access, get_project_and_verify_write_access
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.services.project import ProjectService
from app.core.files import validate_and_save_file

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """
    Creates a new project.
    - Restricted to Admins and Project Managers.
    """
    return ProjectService.create_project(db, project_in, creator_id=current_user.id)

@router.get("", response_model=schemas.PaginatedProjects)
def get_projects(
    page: int = 1,
    size: int = 10,
    search: Optional[str] = None,
    status_filter: Optional[ProjectStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Lists projects.
    - Admins see all projects.
    - PMs and Engineers see only projects they are assigned to.
    """
    total, items = ProjectService.get_projects(
        db, current_user, page=page, size=size, search=search, status_filter=status_filter
    )
    return {
        "total": total,
        "items": items,
        "page": page,
        "size": size
    }

@router.get("/{project_id}", response_model=schemas.ProjectDetailResponse)
def get_project(
    project: Project = Depends(get_project_and_verify_view_access)
):
    """
    Gets detailed project specifications by ID.
    - Requires project view access (Admin or assigned member).
    """
    return project

@router.patch("/{project_id}", response_model=schemas.ProjectResponse)
def update_project(
    project_id: int,
    project_in: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Updates project metadata.
    - Admins and assigned PMs can modify all metadata.
    - Site Engineers can ONLY modify the project 'status'.
    """
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Enforce Role-Based updates
    if current_user.role == UserRole.SITE_ENGINEER:
        # Site Engineer must be a project member to see/modify status
        _ = get_project_and_verify_view_access(project_id, db, current_user)
        
        # Enforce that they only modify status
        update_data = project_in.model_dump(exclude_unset=True)
        if any(key != "status" for key in update_data.keys()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Site Engineers are only permitted to update the project status."
            )
    else:
        # Admins or PMs must pass standard project write checks
        _ = get_project_and_verify_write_access(project_id, db, current_user)

    return ProjectService.update_project(db, project, project_in)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN]))
):
    """
    Deletes project.
    - Restricted to Admins.
    """
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ProjectService.delete_project(db, project)
    return None

# Members Management
@router.post("/{project_id}/members", response_model=schemas.ProjectMemberResponse)
def add_project_member(
    project_id: int,
    member_in: schemas.ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Assigns a user member to a project.
    - Restricted to Admins and assigned PMs.
    """
    # Verify write authorization
    _ = get_project_and_verify_write_access(project_id, db, current_user)
    return ProjectService.add_member(db, project_id, member_in.user_id, member_in.role)

@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Removes a member from a project.
    - Restricted to Admins and assigned PMs.
    """
    # Verify write authorization
    _ = get_project_and_verify_write_access(project_id, db, current_user)
    ProjectService.remove_member(db, project_id, user_id)
    return None

# Uploads endpoints
@router.post("/{project_id}/documents", response_model=schemas.DocumentResponse)
async def upload_project_document(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Uploads project documents.
    - Restricted to Admins and assigned PMs.
    """
    _ = get_project_and_verify_write_access(project_id, db, current_user)
    saved_path = await validate_and_save_file(file, "document")
    
    # Save document binding to database
    return ProjectService.add_document(
        db, project_id, file_name=file.filename, file_type=file.content_type, file_path=saved_path, user_id=current_user.id
    )

@router.post("/{project_id}/drawings", response_model=schemas.DrawingResponse)
async def upload_project_drawing(
    project_id: int,
    drawing_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Uploads PDF drawings.
    - Restricted to Admins and assigned PMs.
    """
    _ = get_project_and_verify_write_access(project_id, db, current_user)
    saved_path = await validate_and_save_file(file, "drawing")
    
    # Save drawing binding
    return ProjectService.add_drawing(
        db, project_id, drawing_name=drawing_name, drawing_path=saved_path, user_id=current_user.id
    )

@router.post("/{project_id}/images", response_model=schemas.SiteImageResponse)
async def upload_site_image(
    project_id: int,
    capture_date: date = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Uploads construction site images.
    - Accessible to Admins, assigned PMs, and assigned Site Engineers.
    """
    # Site engineers are allowed view access, meaning they can upload site images
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    saved_path = await validate_and_save_file(file, "image")
    
    return ProjectService.add_site_image(
        db, project_id, image_path=saved_path, capture_date=capture_date, user_id=current_user.id
    )

@router.get("/{project_id}/documents/{document_id}/download")
def download_project_document(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Downloads file documents securely.
    - Requires view access to project.
    """
    # Verify view permissions
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    
    doc = ProjectService.get_document(db, document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found on this project.")
        
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Physical file not found on disk.")
        
    return FileResponse(
        path=doc.file_path,
        media_type=doc.file_type,
        filename=doc.file_name
    )

@router.delete("/{project_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_uploaded_file(
    project_id: int,
    file_id: int,
    category: str, # "document" | "drawing" | "image"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Deletes uploaded physical files and database records.
    - Restricted to Admins and assigned PMs.
    """
    _ = get_project_and_verify_write_access(project_id, db, current_user)
    ProjectService.delete_file_record(db, file_id, category)
    return None
