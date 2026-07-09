from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal

from app.models.budget import Budget, BudgetItem, EquipmentCost, LaborCost
from app.models.project import Project
from app.schemas.budget import BudgetEstimateRequest, BudgetUpdateRequest
from app.agents.cost_agent import cost_estimation_agent

class CostService:
    @staticmethod
    def calculate_and_save_budget(db: Session, req: BudgetEstimateRequest) -> Budget:
        """
        Triggers the LangGraph workflow, validates calculations, and persists the budget,
        line items, labor breakdown, and machinery costs to the database.
        """
        # Ensure project exists
        project = db.query(Project).filter(Project.id == req.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found."
            )

        # Convert Pydantic request to LangGraph State Dict
        initial_state = {
            "project_id": req.project_id,
            "area_sqft": float(req.area_sqft),
            "currency": req.currency,
            "materials_input": [{"material": m.material, "quantity": float(m.quantity), "unit_price": float(m.unit_price)} for m in req.materials],
            "labor_input": [{"worker_type": l.worker_type, "worker_count": l.worker_count, "daily_rate": float(l.daily_rate), "days": l.days} for l in req.labor],
            "equipment_input": [{"equipment_name": e.equipment_name, "daily_rate": float(e.daily_rate), "days_used": e.days_used} for e in req.equipment],
            "errors": [],
            "budget_items": []
        }

        # Run State Machine Workflow
        result_state = cost_estimation_agent.invoke(initial_state)

        # Catch workflow validation errors
        if result_state.get("errors"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation errors: {', '.join(result_state['errors'])}"
            )

        # 1. Create Budget summary record
        budget = Budget(
            project_id=req.project_id,
            estimated_cost=Decimal(result_state["estimated_cost"]),
            optimized_cost=Decimal(result_state["optimized_cost"]),
            currency=req.currency,
            ai_summary=result_state.get("ai_summary", ""),
            ai_recommendations=result_state.get("ai_recommendations", "")
        )
        db.add(budget)
        db.commit()
        db.refresh(budget)

        # 2. Add itemized BudgetItems
        for item in result_state.get("budget_items", []):
            db_item = BudgetItem(
                budget_id=budget.id,
                category=item["category"],
                description=item["description"],
                quantity=Decimal(item["quantity"]),
                unit_price=Decimal(item["unit_price"]),
                total_price=Decimal(item["total_price"])
            )
            db.add(db_item)

        # 3. Add LaborCosts logs
        # First clean up old labor/equipment entries for this project to maintain standard active counts
        db.query(LaborCost).filter(LaborCost.project_id == req.project_id).delete()
        for l in req.labor:
            db_labor = LaborCost(
                project_id=req.project_id,
                worker_type=l.worker_type,
                worker_count=l.worker_count,
                daily_rate=l.daily_rate,
                days=l.days,
                total_cost=Decimal(float(l.worker_count) * float(l.daily_rate) * float(l.days))
            )
            db.add(db_labor)

        # 4. Add EquipmentCosts logs
        db.query(EquipmentCost).filter(EquipmentCost.project_id == req.project_id).delete()
        for e in req.equipment:
            db_eq = EquipmentCost(
                project_id=req.project_id,
                equipment_name=e.equipment_name,
                days_used=e.days_used,
                daily_rate=e.daily_rate,
                total_cost=Decimal(float(e.daily_rate) * float(e.days_used))
            )
            db.add(db_eq)

        db.commit()
        db.refresh(budget)
        return budget

    @staticmethod
    def get_budget_by_project(db: Session, project_id: int) -> Optional[Budget]:
        """Gets latest committed budget for a project."""
        return db.query(Budget).filter(Budget.project_id == project_id).order_by(Budget.created_at.desc()).first()

    @staticmethod
    def get_budget_detail(db: Session, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Gets latest budget summary and loads itemized labor and machinery costs.
        """
        budget = CostService.get_budget_by_project(db, project_id)
        if not budget:
            return None
            
        labor_costs = db.query(LaborCost).filter(LaborCost.project_id == project_id).all()
        equipment_costs = db.query(EquipmentCost).filter(EquipmentCost.project_id == project_id).all()
        return {
            "budget": budget,
            "labor_costs": labor_costs,
            "equipment_costs": equipment_costs
        }

    @staticmethod
    def get_budget_history(db: Session, project_id: int, page: int = 1, size: int = 10) -> Tuple[int, List[Budget]]:
        """Returns paginated budget estimates history."""
        query = db.query(Budget).filter(Budget.project_id == project_id)
        total = query.count()
        offset = (page - 1) * size
        items = query.order_by(Budget.created_at.desc()).offset(offset).limit(size).all()
        return total, items

    @staticmethod
    def get_budget(db: Session, budget_id: int) -> Optional[Budget]:
        """Gets budget by primary key ID."""
        return db.query(Budget).filter(Budget.id == budget_id).first()

    @staticmethod
    def update_budget(db: Session, budget_id: int, req: BudgetUpdateRequest) -> Optional[Budget]:
        """
        Updates budget values.
        If items list is passed, truncates old items and writes the new items.
        """
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            return None

        update_data = req.model_dump(exclude_unset=True)
        
        # Update main fields
        if "estimated_cost" in update_data:
            budget.estimated_cost = req.estimated_cost
        if "optimized_cost" in update_data:
            budget.optimized_cost = req.optimized_cost
        if "currency" in update_data:
            budget.currency = req.currency

        # Update item listings if provided
        if "items" in update_data and req.items is not None:
            # Delete old items
            db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).delete()
            # Insert new ones
            for item in req.items:
                db_item = BudgetItem(
                    budget_id=budget.id,
                    category=item.category,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=Decimal(float(item.quantity) * float(item.unit_price))
                )
                db.add(db_item)

        db.commit()
        db.refresh(budget)
        return budget

    @staticmethod
    def delete_budget(db: Session, budget: Budget):
        """Deletes a budget and cascades child tables."""
        db.delete(budget)
        db.commit()
