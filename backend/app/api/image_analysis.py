import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access, get_project_and_verify_write_access
from app.models.user import User, UserRole
from app.models.image_analysis import SiteImageAnalysis
from app.services.image_analysis_service import ImageAnalysisService

router = APIRouter(tags=["image_analysis"])

@router.post(
    "/image-analysis/analyze",
    response_model=schemas.SiteImageAnalysisResponse,
    status_code=status.HTTP_201_CREATED
)
def trigger_site_image_visual_audit(
    req: schemas.SiteImageAnalysisCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Triggers the visual audit on an uploaded site image."""
    # Ensure view permission on project is valid
    _ = get_project_and_verify_view_access(req.project_id, db, current_user)
    
    try:
        analysis = ImageAnalysisService.analyze_image(
            db=db,
            project_id=req.project_id,
            site_image_id=req.site_image_id
        )
        return analysis
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(re))

@router.get(
    "/image-analysis/project/{project_id}",
    response_model=List[schemas.SiteImageAnalysisResponse]
)
def list_project_visual_audits(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Retrieves all site image visual analyses for a project."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    return ImageAnalysisService.get_project_analyses(db, project_id)

@router.get(
    "/image-analysis/image/{site_image_id}",
    response_model=schemas.SiteImageAnalysisResponse
)
def get_site_image_analysis_record(
    site_image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Retrieves the analysis record for a specific site image."""
    analysis = ImageAnalysisService.get_analysis_by_image_id(db, site_image_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found for this image.")
    
    # Verify permission to view project
    _ = get_project_and_verify_view_access(analysis.project_id, db, current_user)
    return analysis

@router.get("/image-analysis/annotated-image/{analysis_id}")
def serve_annotated_site_image(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Serves the annotated site image file securely."""
    analysis = db.query(SiteImageAnalysis).filter(SiteImageAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis report not found.")
        
    _ = get_project_and_verify_view_access(analysis.project_id, db, current_user)
    
    if not analysis.annotated_image_path or not os.path.exists(analysis.annotated_image_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotated image file not found on disk.")
        
    # Expose the annotated image securely
    return FileResponse(analysis.annotated_image_path)
