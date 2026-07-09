from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class VoiceCommandLog(Base):
    __tablename__ = "voice_command_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    command_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    audio_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User")
    project = relationship("Project")
