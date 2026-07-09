from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    material_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # Cement, Steel, Bricks, etc.
    quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(50), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_cost = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    material_name = Column(String(255), unique=True, index=True, nullable=False)
    quantity_available = Column(Numeric(12, 2), default=0.0, nullable=False)
    quantity_reserved = Column(Numeric(12, 2), default=0.0, nullable=False)
    unit = Column(String(50), nullable=False)
    warehouse_capacity = Column(Numeric(12, 2), nullable=False)


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(255), index=True, nullable=False)
    rating = Column(Numeric(3, 2), default=5.0, nullable=False)
    contact_info = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    active = Column(Boolean, default=True, nullable=False)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    material_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_cost = Column(Numeric(15, 2), nullable=False)
    status = Column(String(50), default="Pending", nullable=False)  # Pending, Approved, Shipped, Delivered
    ordered_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project")
    supplier = relationship("Supplier")
