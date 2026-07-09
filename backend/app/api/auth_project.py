from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User, UserRole
from app.models.project import Project, ProjectMember
from app.services.project import ProjectService

def get_project_and_verify_view_access(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Project:
    """
    Dependency to verify if the current user can view a project.
    - Admin can view all projects.
    - Assigned Project Members (PMs, Engineers) can view their project.
    """
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    if current_user.role == UserRole.ADMIN:
        return project

    # Check project membership
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You are not a member of this project."
        )

    return project

def get_project_and_verify_write_access(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Project:
    """
    Dependency to verify write permission.
    - Admin can edit any project.
    - Project Manager members can edit metadata.
    - Site Engineers are rejected here (they are handled in the status update path).
    """
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    if current_user.role == UserRole.ADMIN:
        return project

    # Check project membership
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()

    # Site Engineers cannot write metadata
    if not member or member.role == UserRole.SITE_ENGINEER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. Only Project Managers or Admins can modify project metadata."
        )

    return project
