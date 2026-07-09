from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date, datetime
from decimal import Decimal

from app.models.worker import Worker, WorkerSkill, WorkerSchedule, Attendance, LeaveRequest, ShiftPlan
from app.models.project import Project
from app.schemas.worker import WorkerCreate, AttendanceCreate, LeaveRequestCreate, ShiftPlannerRequest
from app.agents.worker_agent import worker_scheduler_agent

class WorkerService:
    @staticmethod
    def create_worker(db: Session, req: WorkerCreate) -> Worker:
        """Creates a worker profile and registers their skills list."""
        existing = db.query(Worker).filter(Worker.email == req.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Worker email is already registered."
            )

        worker = Worker(
            full_name=req.full_name,
            email=req.email,
            phone=req.phone,
            role_title=req.role_title,
            worker_type=req.worker_type,
            wage_rate=req.wage_rate,
            active=True
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        # Write skills
        for skill in req.skills:
            db_skill = WorkerSkill(
                worker_id=worker.id,
                skill_name=skill.skill_name,
                proficiency_level=skill.proficiency_level
            )
            db.add(db_skill)
        db.commit()
        db.refresh(worker)
        return worker

    @staticmethod
    def get_workers(db: Session) -> List[Worker]:
        """Lists all registered workers."""
        return db.query(Worker).all()

    @staticmethod
    def get_worker(db: Session, worker_id: int) -> Optional[Worker]:
        """Gets worker by primary key ID."""
        return db.query(Worker).filter(Worker.id == worker_id).first()

    @staticmethod
    def update_worker(db: Session, worker_id: int, req: WorkerCreate) -> Optional[Worker]:
        """Modifies worker details and overrides skill maps."""
        worker = db.query(Worker).filter(Worker.id == worker_id).first()
        if not worker:
            return None

        # Email check if changing email
        if worker.email != req.email:
            existing = db.query(Worker).filter(Worker.email == req.email).first()
            if existing:
                raise HTTPException(status_code=400, detail="Worker email already registered.")

        worker.full_name = req.full_name;
        worker.email = req.email;
        worker.phone = req.phone;
        worker.role_title = req.role_title;
        worker.worker_type = req.worker_type;
        worker.wage_rate = req.wage_rate;

        # Clear old skills and insert new ones
        db.query(WorkerSkill).filter(WorkerSkill.worker_id == worker.id).delete()
        for skill in req.skills:
            db_skill = WorkerSkill(
                worker_id=worker.id,
                skill_name=skill.skill_name,
                proficiency_level=skill.proficiency_level
            )
            db.add(db_skill)

        db.commit()
        db.refresh(worker)
        return worker

    @staticmethod
    def delete_worker(db: Session, worker_id: int) -> bool:
        """Deletes a worker permanently."""
        worker = db.query(Worker).filter(Worker.id == worker_id).first()
        if not worker:
            return False
        db.delete(worker)
        db.commit()
        return True

    @staticmethod
    def log_attendance(db: Session, req: AttendanceCreate) -> Attendance:
        """Logs daily attendance for a worker."""
        # Ensure worker exists
        worker = db.query(Worker).filter(Worker.id == req.worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found.")

        # Check duplicate date logs for same worker
        existing = db.query(Attendance).filter(
            Attendance.worker_id == req.worker_id,
            Attendance.date == req.date
        ).first()
        
        if existing:
            # Update existing
            existing.status = req.status
            existing.hours_worked = req.hours_worked
            existing.overtime_hours = req.overtime_hours
            db.commit()
            db.refresh(existing)
            return existing

        db_att = Attendance(
            worker_id=req.worker_id,
            date=req.date,
            status=req.status,
            hours_worked=req.hours_worked,
            overtime_hours=req.overtime_hours
        )
        db.add(db_att)
        db.commit()
        db.refresh(db_att)
        return db_att

    @staticmethod
    def get_attendance(db: Session, project_id: Optional[int] = None) -> List[Attendance]:
        """Lists attendance records."""
        # Query all
        return db.query(Attendance).order_by(Attendance.date.desc()).all()

    @staticmethod
    def create_leave_request(db: Session, req: LeaveRequestCreate) -> LeaveRequest:
        """Submits a leave request for approval."""
        # Ensure worker exists
        worker = db.query(Worker).filter(Worker.id == req.worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found.")

        req_db = LeaveRequest(
            worker_id=req.worker_id,
            start_date=req.start_date,
            end_date=req.end_date,
            leave_type=req.leave_type,
            status="Pending",
            reason=req.reason
        )
        db.add(req_db)
        db.commit()
        db.refresh(req_db)
        return req_db

    @staticmethod
    def get_leave_requests(db: Session) -> List[LeaveRequest]:
        """Lists leave requests."""
        return db.query(LeaveRequest).order_by(LeaveRequest.start_date.desc()).all()

    @staticmethod
    def update_leave_status(db: Session, leave_id: int, status_str: str) -> Optional[LeaveRequest]:
        """Approves or Rejects a pending leave request."""
        req = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
        if not req:
            return None
        req.status = status_str
        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def optimize_and_save_shift_plan(db: Session, req: ShiftPlannerRequest) -> Dict[str, Any]:
        """
        Triggers the worker agent state machine, predicts shortages,
        rotates shifts, and saves plans & schedules.
        """
        # Ensure project exists
        project = db.query(Project).filter(Project.id == req.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        # Fetch active workers pool
        worker_rows = db.query(Worker).filter(Worker.active == True).all()
        workers_pool = [{
            "worker_id": w.id,
            "full_name": w.full_name,
            "role_title": w.role_title,
            "worker_type": w.worker_type,
            "wage_rate": float(w.wage_rate)
        } for w in worker_rows]

        # Fetch leave requests pool
        leave_rows = db.query(LeaveRequest).all()
        leaves_pool = [{
            "worker_id": l.worker_id,
            "start_date": l.start_date.strftime("%Y-%m-%d") if isinstance(l.start_date, (date, datetime)) else l.start_date,
            "end_date": l.end_date.strftime("%Y-%m-%d") if isinstance(l.end_date, (date, datetime)) else l.end_date,
            "status": l.status
        } for l in leave_rows]

        # Run State Machine Workflow
        initial_state = {
            "project_id": req.project_id,
            "start_date": req.start_date.strftime("%Y-%m-%d"),
            "end_date": req.end_date.strftime("%Y-%m-%d"),
            "required_roles": [],
            "workers_pool": workers_pool,
            "leaves_pool": leaves_pool,
            "available_workers": [],
            "assigned_schedules": [],
            "shortage_warnings": [],
            "optimization_summary": "",
            "errors": []
        }

        result_state = worker_scheduler_agent.invoke(initial_state)

        if result_state.get("errors"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation errors: {', '.join(result_state['errors'])}"
            )

        # Truncate old ShiftPlans and schedules for this project on these dates to prevent duplicates
        db.query(ShiftPlan).filter(
            ShiftPlan.project_id == req.project_id,
            ShiftPlan.date >= req.start_date,
            ShiftPlan.date <= req.end_date
        ).delete()
        
        db.query(WorkerSchedule).filter(
            WorkerSchedule.project_id == req.project_id,
            WorkerSchedule.start_date >= req.start_date,
            WorkerSchedule.end_date <= req.end_date
        ).delete()

        # Save Day & Night Shift Plans
        plans_saved = []
        for shift in ["Day", "Night"]:
            plan = ShiftPlan(
                project_id=req.project_id,
                plan_name=f"{project.project_name} - {shift} Shift Optimization",
                date=req.start_date,
                shift_type=shift,
                requirements_description=result_state.get("optimization_summary", "")
            )
            db.add(plan)
            plans_saved.append(plan)

        # Write WorkerSchedule logs for allocated workers
        schedules_saved = []
        for sched in result_state.get("assigned_schedules", []):
            db_sched = WorkerSchedule(
                worker_id=sched["worker_id"],
                project_id=req.project_id,
                start_date=req.start_date,
                end_date=req.end_date,
                shift_type=sched["shift_type"]
            )
            db.add(db_sched)
            schedules_saved.append(db_sched)

        db.commit()

        # Refresh
        for p in plans_saved:
            db.refresh(p)
        for s in schedules_saved:
            db.refresh(s)

        return {
            "project_id": req.project_id,
            "plans": plans_saved,
            "shortage_warnings": result_state.get("shortage_warnings", []),
            "optimization_summary": result_state.get("optimization_summary", "")
        }

    @staticmethod
    def get_project_schedules(db: Session, project_id: int) -> List[WorkerSchedule]:
        """Gets worker schedules mapped to a project."""
        return db.query(WorkerSchedule).filter(WorkerSchedule.project_id == project_id).all()
