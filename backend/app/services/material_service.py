from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal

from app.models.material import Material, Inventory, Supplier, PurchaseOrder
from app.models.project import Project
from app.schemas.material import MaterialEstimateRequest, PurchaseOrderCreate
from app.agents.material_agent import material_planner_agent

class MaterialService:
    @staticmethod
    def estimate_and_save_materials(db: Session, req: MaterialEstimateRequest) -> Dict[str, Any]:
        """
        Runs the material planning agent, clears older estimates for the project,
        and saves new material estimates.
        """
        # Ensure project exists
        project = db.query(Project).filter(Project.id == req.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        # Fetch current stock pools
        inventory_rows = db.query(Inventory).all()
        inventory_pool = [{
            "material_name": i.material_name,
            "quantity_available": float(i.quantity_available),
            "quantity_reserved": float(i.quantity_reserved),
            "unit": i.unit
        } for i in inventory_rows]

        # Fetch active suppliers pools
        supplier_rows = db.query(Supplier).filter(Supplier.active == True).all()
        suppliers_pool = [{
            "id": s.id,
            "supplier_name": s.supplier_name,
            "rating": float(s.rating),
            "active": s.active
        } for s in supplier_rows]

        # Run State Machine Workflow
        initial_state = {
            "project_id": req.project_id,
            "area_sqft": float(req.area_sqft),
            "floors": req.floors,
            "building_type": req.building_type,
            "rooms": req.rooms,
            "timeline_months": req.timeline_months,
            "budget": float(req.budget),
            "project_category": req.project_category,
            "inventory_pool": inventory_pool,
            "suppliers_pool": suppliers_pool,
            "errors": [],
            "materials_estimated": [],
            "low_stock_warnings": [],
            "supplier_recommendations": []
        }

        result_state = material_planner_agent.invoke(initial_state)

        if result_state.get("errors"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation errors: {', '.join(result_state['errors'])}"
            )

        # Truncate old estimates for this project
        db.query(Material).filter(Material.project_id == req.project_id).delete()

        # Insert new Material logs
        materials_saved = []
        for mat in result_state.get("materials_estimated", []):
            db_mat = Material(
                project_id=req.project_id,
                material_name=mat["material_name"],
                category=mat["category"],
                quantity=Decimal(mat["quantity"]),
                unit=mat["unit"],
                unit_price=Decimal(mat["unit_price"]),
                total_cost=Decimal(mat["total_cost"])
            )
            db.add(db_mat)
            materials_saved.append(db_mat)

        db.commit()

        # Refresh objects to return
        for m in materials_saved:
            db.refresh(m)

        return {
            "project_id": req.project_id,
            "materials": materials_saved,
            "low_stock_warnings": result_state.get("low_stock_warnings", []),
            "supplier_recommendations": result_state.get("supplier_recommendations", []),
            "optimization_summary": result_state.get("optimization_summary", "")
        }

    @staticmethod
    def get_project_materials(db: Session, project_id: int) -> List[Material]:
        """Gets all estimated materials for a project."""
        return db.query(Material).filter(Material.project_id == project_id).all()

    @staticmethod
    def update_material(db: Session, material_id: int, quantity: Decimal, unit_price: Decimal) -> Optional[Material]:
        """Modifies estimated material quantities."""
        mat = db.query(Material).filter(Material.id == material_id).first()
        if not mat:
            return None
        mat.quantity = quantity
        mat.unit_price = unit_price
        mat.total_cost = Decimal(float(quantity) * float(unit_price))
        db.commit()
        db.refresh(mat)
        return mat

    @staticmethod
    def delete_material(db: Session, material_id: int) -> bool:
        """Deletes a material row."""
        mat = db.query(Material).filter(Material.id == material_id).first()
        if not mat:
            return False
        db.delete(mat)
        db.commit()
        return True

    @staticmethod
    def get_inventory(db: Session) -> List[Inventory]:
        """Gets all warehouse inventory rows."""
        return db.query(Inventory).all()

    @staticmethod
    def update_inventory(db: Session, name: str, quantity_change: Decimal) -> Inventory:
        """Modifies inventory available stock quantities."""
        inv = db.query(Inventory).filter(Inventory.material_name == name).first()
        if not inv:
            # Create a default inventory row
            inv = Inventory(
                material_name=name,
                quantity_available=max(Decimal(0.0), quantity_change),
                quantity_reserved=Decimal(0.0),
                unit="Units",
                warehouse_capacity=Decimal(10000.0)
            )
            db.add(inv)
        else:
            inv.quantity_available = max(Decimal(0.0), inv.quantity_available + quantity_change)
        db.commit()
        db.refresh(inv)
        return inv

    @staticmethod
    def get_suppliers(db: Session) -> List[Supplier]:
        """Gets list of all suppliers."""
        return db.query(Supplier).all()

    @staticmethod
    def create_purchase_order(db: Session, req: PurchaseOrderCreate) -> PurchaseOrder:
        """
        Creates a purchase order and updates inventory reserved stock.
        """
        # Save PO
        po = PurchaseOrder(
            project_id=req.project_id,
            supplier_id=req.supplier_id,
            material_name=req.material_name,
            quantity=req.quantity,
            unit_price=req.unit_price,
            total_cost=Decimal(float(req.quantity) * float(req.unit_price)),
            status="Pending"
        )
        db.add(po)
        
        # Reserved stock in Inventory
        inv = db.query(Inventory).filter(Inventory.material_name == req.material_name).first()
        if inv:
            inv.quantity_reserved += req.quantity
        else:
            # Add a stock mapping holding reservations
            inv = Inventory(
                material_name=req.material_name,
                quantity_available=Decimal(0.0),
                quantity_reserved=req.quantity,
                unit="Units",
                warehouse_capacity=Decimal(10000.0)
            )
            db.add(inv)
            
        db.commit()
        db.refresh(po)
        return po

    @staticmethod
    def get_purchase_orders(db: Session, project_id: Optional[int] = None) -> List[PurchaseOrder]:
        """Returns purchase orders, optionally filtered by project."""
        query = db.query(PurchaseOrder)
        if project_id is not None:
            query = query.filter(PurchaseOrder.project_id == project_id)
        return query.order_by(PurchaseOrder.ordered_at.desc()).all()
