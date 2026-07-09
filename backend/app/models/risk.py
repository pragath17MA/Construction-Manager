from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Risk(Base):
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False, default=0)
    delay_probability = Column(Numeric(5, 2), nullable=False, default=0.0) # 0.00 to 100.00
    executive_summary = Column(Text, nullable=True)
    
    # 8 Risk Categories severities: Low, Medium, High, Critical
    weather_risk_severity = Column(String(50), nullable=False, default="Low")
    material_risk_severity = Column(String(50), nullable=False, default="Low")
    budget_risk_severity = Column(String(50), nullable=False, default="Low")
    worker_risk_severity = Column(String(50), nullable=False, default="Low")
    equipment_risk_severity = Column(String(50), nullable=False, default="Low")
    supplier_risk_severity = Column(String(50), nullable=False, default="Low")
    safety_risk_severity = Column(String(50), nullable=False, default="Low")
    timeline_risk_severity = Column(String(50), nullable=False, default="Low")
    
    ai_mitigation_suggestions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project")

class RiskHistory(Base):
    __tablename__ = "risk_histories"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False)
    delay_probability = Column(Numeric(5, 2), nullable=False)
    executive_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    # Relationships
    project = relationship("Project")

class WeatherData(Base):
    __tablename__ = "weather_datas"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    location = Column(String(255), nullable=False)
    temperature = Column(Numeric(5, 2), nullable=True)
    wind_speed = Column(Numeric(5, 2), nullable=True)
    precipitation = Column(Numeric(5, 2), nullable=True)
    humidity = Column(Numeric(5, 2), nullable=True)
    weather_description = Column(String(255), nullable=True)
    alerts = Column(Text, nullable=True) # JSON or Comma-separated alerts
    cached_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project")

class DelayPrediction(Base):
    __tablename__ = "delay_predictions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    probability = Column(Numeric(5, 2), nullable=False, default=0.0) # 0.00 to 100.00
    predicted_delay_days = Column(Integer, nullable=False, default=0)
    variance_days = Column(Integer, nullable=False, default=0)
    root_causes = Column(Text, nullable=True)
    recovery_recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project")
