from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(100), nullable=False)  # Budget Exceeded, Worker Shortage, etc.
    channel = Column(String(50), nullable=False)     # Email, WhatsApp, Push
    recipient = Column(String(255), nullable=False)   # Email or Phone number
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="Sent")  # Sent, Failed
    created_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project")
    user = relationship("User")
