from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    estimated_cost = Column(Numeric(15, 2), nullable=False)
    optimized_cost = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    ai_summary = Column(Text, nullable=True)
    ai_recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project")
    items = relationship("BudgetItem", back_populates="budget", cascade="all, delete-orphan")

    @property
    def total_estimated_cost(self):
        return self.estimated_cost

    @total_estimated_cost.setter
    def total_estimated_cost(self, value):
        self.estimated_cost = value

    @property
    def total_optimized_cost(self):
        return self.optimized_cost

    @total_optimized_cost.setter
    def total_optimized_cost(self, value):
        self.optimized_cost = value


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)  # Material, Labor, Equipment, Indirect, Contingency
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)

    # Relationships
    budget = relationship("Budget", back_populates="items")


class EquipmentCost(Base):
    __tablename__ = "equipment_costs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    equipment_name = Column(String(255), nullable=False)
    days_used = Column(Integer, nullable=False)
    daily_rate = Column(Numeric(15, 2), nullable=False)
    total_cost = Column(Numeric(15, 2), nullable=False)

    # Relationships
    project = relationship("Project")


class LaborCost(Base):
    __tablename__ = "labor_costs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    worker_type = Column(String(255), nullable=False)
    worker_count = Column(Integer, nullable=False)
    daily_rate = Column(Numeric(15, 2), nullable=False)
    days = Column(Integer, nullable=False)
    total_cost = Column(Numeric(15, 2), nullable=False)

    # Relationships
    project = relationship("Project")
