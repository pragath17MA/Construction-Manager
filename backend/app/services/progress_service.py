from datetime import date, datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.project import Project
from app.models.progress import Milestone, DailyLog, ProgressReport
from app.models.budget import Budget
from app.models.worker import Attendance
from app.schemas.progress import DailyLogCreate, MilestoneCreate
from app.agents.progress_agent import progress_monitoring_agent

class ProgressService:
    @staticmethod
    def create_daily_log(db: Session, req: DailyLogCreate, user_id: int) -> DailyLog:
        """Logs daily site update entries."""
        # Ensure project exists
        project = db.query(Project).filter(Project.id == req.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        log = DailyLog(
            project_id=req.project_id,
            log_date=req.log_date,
            update_text=req.update_text,
            image_path=req.image_path,
            submitted_by=user_id
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def create_or_update_milestone(db: Session, req: MilestoneCreate) -> Milestone:
        """Registers a new milestone or updates progress metrics."""
        # Check if project exists
        project = db.query(Project).filter(Project.id == req.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        # Check existing milestone by name to allow update
        existing = db.query(Milestone).filter(
            Milestone.project_id == req.project_id,
            Milestone.milestone_name == req.milestone_name
        ).first()

        today = date.today()
        status_flag = req.status
        
        # Calculate status automatically based on progress indicators
        if req.completion_percentage >= 100.0:
            status_flag = "Completed"
        elif req.planned_end_date < today and req.completion_percentage < 100.0:
            status_flag = "Delayed"
        elif req.completion_percentage < 50.0 and (req.planned_end_date - today).days < 5:
            status_flag = "At-Risk"
        else:
            status_flag = "On-Time"

        if existing:
            existing.description = req.description
            existing.planned_end_date = req.planned_end_date
            existing.actual_end_date = req.actual_end_date or (today if status_flag == "Completed" else None)
            existing.completion_percentage = req.completion_percentage
            existing.status = status_flag
            db_ms = existing
        else:
            db_ms = Milestone(
                project_id=req.project_id,
                milestone_name=req.milestone_name,
                description=req.description,
                planned_end_date=req.planned_end_date,
                actual_end_date=req.actual_end_date or (today if status_flag == "Completed" else None),
                completion_percentage=req.completion_percentage,
                status=status_flag
            )
            db.add(db_ms)

        db.commit()
        db.refresh(db_ms)
        return db_ms

    @staticmethod
    def get_milestones(db: Session, project_id: int) -> List[Milestone]:
        """Lists milestones."""
        return db.query(Milestone).filter(Milestone.project_id == project_id).order_by(Milestone.planned_end_date.asc()).all()

    @staticmethod
    def get_progress_summary(db: Session, project_id: int) -> Dict[str, Any]:
        """
        Gathers progress variables, triggers agent workflows, and saves progress reports.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        milestones = db.query(Milestone).filter(Milestone.project_id == project_id).all()
        daily_logs = db.query(DailyLog).filter(DailyLog.project_id == project_id).order_by(DailyLog.log_date.desc()).limit(5).all()
        
        # Budget numbers
        budget_limit = float(project.budget)
        budget_row = db.query(Budget).filter(Budget.project_id == project_id).first()
        budget_spent = float(budget_row.total_estimated_cost) if budget_row else 0.0

        # Resource Utilization indicator
        # Calculate workers attendance rate
        total_attendance = db.query(Attendance).all()
        present = sum(1 for a in total_attendance if a.status == "Present")
        utilization = (present / len(total_attendance) * 100.0) if total_attendance else 85.0

        # Compile pools
        milestones_pool = [{
            "milestone_name": m.milestone_name,
            "completion_percentage": float(m.completion_percentage),
            "planned_end_date": m.planned_end_date.strftime("%Y-%m-%d") if isinstance(m.planned_end_date, (date, datetime)) else m.planned_end_date,
            "actual_end_date": m.actual_end_date.strftime("%Y-%m-%d") if isinstance(m.actual_end_date, (date, datetime)) else (m.actual_end_date or "")
        } for m in milestones]

        logs_pool = [{
            "log_date": l.log_date.strftime("%Y-%m-%d"),
            "update_text": l.update_text
        } for l in daily_logs]

        # Trigger LangGraph Agent
        state = {
            "project_id": project_id,
            "milestones": milestones_pool,
            "daily_logs": logs_pool,
            "budget_spent": budget_spent,
            "budget_limit": budget_limit,
            "resource_utilization": float(utilization),
            "overall_completion_percentage": 0.0,
            "variance_days": 0,
            "variance_status": "On-Track",
            "ai_progress_summary": "",
            "errors": []
        }

        result = progress_monitoring_agent.invoke(state)

        # Clear old daily progress reports to cache the latest review
        db.query(ProgressReport).filter(
            ProgressReport.project_id == project_id,
            ProgressReport.report_type == "Daily"
        ).delete()

        completed_count = sum(1 for m in milestones if m.completion_percentage >= 100.0)

        # Save fresh ProgressReport
        report = ProgressReport(
            project_id=project_id,
            report_type="Daily",
            start_date=date.today(),
            end_date=date.today(),
            overall_completion_percentage=Decimal(str(result["overall_completion_percentage"])),
            milestones_completed_count=completed_count,
            budget_spent_so_far=Decimal(str(budget_spent)),
            resource_utilization_rate=Decimal(str(utilization)),
            variance_status=result["variance_status"],
            ai_summary=result["ai_progress_summary"]
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        all_reports = db.query(ProgressReport).filter(ProgressReport.project_id == project_id).order_by(ProgressReport.created_at.desc()).all()

        return {
            "project_id": project_id,
            "overall_completion": Decimal(str(result["overall_completion_percentage"])),
            "planned_vs_actual_variance": result["variance_days"],
            "milestones": milestones,
            "latest_logs": daily_logs,
            "reports": all_reports,
            "budget_spent": Decimal(str(budget_spent)),
            "budget_limit": Decimal(str(budget_limit)),
            "resource_utilization": Decimal(str(utilization))
        }
