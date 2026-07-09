from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access, get_project_and_verify_write_access
from app.models.user import User, UserRole
from app.services.cost_service import CostService
from app.services.pdf_generator import generate_budget_pdf_report

router = APIRouter(prefix="/budget", tags=["budget"])

@router.post("/estimate", response_model=schemas.BudgetResponse, status_code=status.HTTP_201_CREATED)
def estimate_project_budget(
    req: schemas.BudgetEstimateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """
    Creates a new budget cost estimate.
    - Restricted to Admins and assigned PMs.
    """
    # Enforce write access for the project
    _ = get_project_and_verify_write_access(req.project_id, db, current_user)
    return CostService.calculate_and_save_budget(db, req)

@router.get("/{project_id}", response_model=schemas.BudgetDetailResponse)
def get_current_budget_detail(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Retrieves the latest budget estimation detail for the project.
    - Requires view access to project.
    """
    # Verify view permissions
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    detail = CostService.get_budget_detail(db, project_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No budget estimate found for this project."
        )
    return detail

@router.get("/history/{project_id}", response_model=schemas.PaginatedBudgets)
def get_project_budget_history(
    project_id: int,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Returns pagination list of historical budget estimates.
    - Requires view access to project.
    """
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    total, items = CostService.get_budget_history(db, project_id, page=page, size=size)
    return {
        "total": total,
        "items": items,
        "page": page,
        "size": size
    }

@router.put("/update/{budget_id}", response_model=schemas.BudgetResponse)
def update_budget(
    budget_id: int,
    req: schemas.BudgetUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """
    Updates budget metadata parameters or budget items list.
    - Restricted to Admins and assigned PMs.
    """
    budget = CostService.get_budget(db, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    # Verify project write privileges
    _ = get_project_and_verify_write_access(budget.project_id, db, current_user)
    
    updated = CostService.update_budget(db, budget_id, req)
    if not updated:
        raise HTTPException(status_code=404, detail="Budget failed to update")
    return updated

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """
    Removes a budget estimate by ID.
    - Restricted to Admins and assigned PMs.
    """
    budget = CostService.get_budget(db, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    # Verify project write privileges
    _ = get_project_and_verify_write_access(budget.project_id, db, current_user)
    
    CostService.delete_budget(db, budget)
    return None

@router.get("/report/{budget_id}")
def download_budget_pdf_report(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Securely streams the compiled budget estimate PDF report.
    - Requires view access to project.
    """
    budget = CostService.get_budget(db, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget estimate not found.")
        
    # Verify view permissions
    project = get_project_and_verify_view_access(budget.project_id, db, current_user)
    
    pdf_buffer = generate_budget_pdf_report(
        budget,
        project_name=project.project_name,
        client_name=project.client_name,
        location=project.location
    )
    
    filename = f"budget_report_{project.project_name.lower().replace(' ', '_')}_{budget.id}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
