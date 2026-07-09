from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, Date, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=False)
    role_title = Column(String(100), nullable=False)  # Mason, Electrician, Plumber, Supervisor, Operator, Carpenter, Painter, Contractor, Engineer
    worker_type = Column(String(100), nullable=False)  # Skilled, Semi-Skilled, Unskilled
    wage_rate = Column(Numeric(15, 2), nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    skills = relationship("WorkerSkill", back_populates="worker", cascade="all, delete-orphan")
    schedules = relationship("WorkerSchedule", back_populates="worker", cascade="all, delete-orphan")
    attendance = relationship("Attendance", back_populates="worker", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="worker", cascade="all, delete-orphan")


class WorkerSkill(Base):
    __tablename__ = "worker_skills"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(255), nullable=False)
    proficiency_level = Column(String(50), default="Intermediate", nullable=False)  # Beginner, Intermediate, Expert

    # Relationships
    worker = relationship("Worker", back_populates="skills")


class WorkerSchedule(Base):
    __tablename__ = "worker_schedules"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    shift_type = Column(String(50), default="Day", nullable=False)  # Day, Night
    assigned_at = Column(DateTime, default=func.now())

    # Relationships
    worker = relationship("Worker", back_populates="schedules")
    project = relationship("Project")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False)  # Present, Absent, Late
    hours_worked = Column(Numeric(4, 2), default=8.0, nullable=False)
    overtime_hours = Column(Numeric(4, 2), default=0.0, nullable=False)

    # Relationships
    worker = relationship("Worker", back_populates="attendance")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    leave_type = Column(String(50), nullable=False)  # Sick, Casual, Earned
    status = Column(String(50), default="Pending", nullable=False)  # Pending, Approved, Rejected
    reason = Column(Text, nullable=True)

    # Relationships
    worker = relationship("Worker", back_populates="leave_requests")


class ShiftPlan(Base):
    __tablename__ = "shift_plans"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    plan_name = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    shift_type = Column(String(50), nullable=False)  # Day, Night
    requirements_description = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project")
