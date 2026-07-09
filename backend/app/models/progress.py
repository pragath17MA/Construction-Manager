from sqlalchemy import Column, Integer, String, Text, Date, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProgressReport(Base):
    __tablename__ = "progress_reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(50), nullable=False) # "Daily", "Weekly", "Monthly"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    overall_completion_percentage = Column(Numeric(5, 2), nullable=False, default=0.0)
    milestones_completed_count = Column(Integer, nullable=False, default=0)
    budget_spent_so_far = Column(Numeric(15, 2), nullable=False, default=0.0)
    resource_utilization_rate = Column(Numeric(5, 2), nullable=False, default=0.0) # percentage
    variance_status = Column(String(50), nullable=False, default="On-Track") # "On-Track", "Minor Variance", "Critical Delay"
    ai_summary = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project")
    creator = relationship("User")

class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    milestone_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    planned_end_date = Column(Date, nullable=False)
    actual_end_date = Column(Date, nullable=True)
    completion_percentage = Column(Numeric(5, 2), nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="Planning") # "Planning", "On-Time", "At-Risk", "Delayed", "Completed"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project")

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    log_date = Column(Date, nullable=False)
    update_text = Column(Text, nullable=False)
    image_path = Column(String(500), nullable=True)
    submitted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project")
    submitter = relationship("User")
