import os
import json
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.project import SiteImage
from app.models.image_analysis import SiteImageAnalysis
from app.agents.image_analysis_agent import site_image_analysis_agent

logger = logging.getLogger(__name__)

class ImageAnalysisService:
    @staticmethod
    def analyze_image(db: Session, project_id: int, site_image_id: int) -> SiteImageAnalysis:
        """
        Loads the site image, invokes the visual agent workflow (YOLOv8 + OpenCV),
        updates/inserts the SiteImageAnalysis database record, and returns it.
        """
        # 1. Fetch site image record
        site_image = db.query(SiteImage).filter(SiteImage.id == site_image_id).first()
        if not site_image:
            raise ValueError(f"Site image not found for ID: {site_image_id}")
            
        if site_image.project_id != project_id:
            raise ValueError(f"Site image {site_image_id} does not belong to Project {project_id}")

        # 2. Invoke visual agent workflow
        inputs = {
            "project_id": project_id,
            "site_image_id": site_image_id,
            "image_path": site_image.image_path,
            "progress_percentage": 0.0,
            "construction_stage": "",
            "safety_issues": [],
            "annotated_image_path": None,
            "recommendations": "",
            "errors": []
        }
        
        try:
            result = site_image_analysis_agent.invoke(inputs)
        except Exception as e:
            logger.error(f"Failed to invoke image analysis agent: {e}")
            raise RuntimeError(f"Visual audit agent workflow failed: {str(e)}")

        # 3. Check for existing analysis record
        analysis = db.query(SiteImageAnalysis).filter(
            SiteImageAnalysis.site_image_id == site_image_id
        ).first()
        
        if not analysis:
            analysis = SiteImageAnalysis(
                project_id=project_id,
                site_image_id=site_image_id
            )
            db.add(analysis)

        # 4. Save results to db
        analysis.progress_percentage = result.get("progress_percentage", 0.0)
        analysis.construction_stage = result.get("construction_stage", "Unknown")
        analysis.safety_issues = json.dumps(result.get("safety_issues", []))
        analysis.recommendations = result.get("recommendations", "")
        analysis.annotated_image_path = result.get("annotated_image_path")
        
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def get_analysis_by_image_id(db: Session, site_image_id: int) -> Optional[SiteImageAnalysis]:
        """Fetches the analysis report for a specific site image."""
        return db.query(SiteImageAnalysis).filter(SiteImageAnalysis.site_image_id == site_image_id).first()

    @staticmethod
    def get_project_analyses(db: Session, project_id: int) -> List[SiteImageAnalysis]:
        """Lists all site visual analysis reports for a specific project."""
        return db.query(SiteImageAnalysis).filter(SiteImageAnalysis.project_id == project_id).all()
