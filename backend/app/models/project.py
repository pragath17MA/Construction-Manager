import enum
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, DateTime, ForeignKey, Enum, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import UserRole

class ProjectStatus(str, enum.Enum):
    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    DELAYED = "Delayed"
    CANCELLED = "Cancelled"

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    client_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    expected_end_date = Column(Date, nullable=False)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNING)
    budget = Column(Numeric(15, 2), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    drawings = relationship("Drawing", back_populates="project", cascade="all, delete-orphan")
    images = relationship("SiteImage", back_populates="project", cascade="all, delete-orphan")
    construction_documents = relationship("ConstructionDocument", back_populates="project", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(UserRole), nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_user_member"),
    )

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project", back_populates="documents")
    uploader = relationship("User")


class Drawing(Base):
    __tablename__ = "drawings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    drawing_name = Column(String(255), nullable=False)
    drawing_path = Column(String(500), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project", back_populates="drawings")
    uploader = relationship("User")


class SiteImage(Base):
    __tablename__ = "site_images"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String(500), nullable=False)
    capture_date = Column(Date, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project", back_populates="images")
    uploader = relationship("User")
