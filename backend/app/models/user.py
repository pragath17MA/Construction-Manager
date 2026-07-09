import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, func
from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    PROJECT_MANAGER = "Project Manager"
    SITE_ENGINEER = "Site Engineer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.SITE_ENGINEER)
    is_active = Column(Boolean, default=True, nullable=False)
    password_reset_token = Column(String(255), unique=True, nullable=True, index=True)
    password_reset_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
