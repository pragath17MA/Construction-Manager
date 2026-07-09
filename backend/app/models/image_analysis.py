from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class SiteImageAnalysis(Base):
    __tablename__ = "site_image_analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    site_image_id = Column(Integer, ForeignKey("site_images.id", ondelete="CASCADE"), nullable=False, index=True)
    progress_percentage = Column(Numeric(5, 2), nullable=False, default=0.0)
    construction_stage = Column(String(100), nullable=False)
    safety_issues = Column(Text, nullable=True)  # JSON serialized list of detected safety issues
    recommendations = Column(Text, nullable=True)
    annotated_image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project")
    site_image = relationship("SiteImage")
