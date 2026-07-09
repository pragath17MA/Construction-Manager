from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from app import schemas
from app.core.database import get_db
from app.api import deps
from app.api.auth_project import get_project_and_verify_view_access, get_project_and_verify_write_access
from app.models.user import User, UserRole
from app.services.material_service import MaterialService
from app.services.report_exporter import ReportExporter

router = APIRouter(prefix="/materials", tags=["materials"])

@router.post("/estimate", response_model=schemas.MaterialEstimateResponse, status_code=status.HTTP_201_CREATED)
def estimate_materials(
    req: schemas.MaterialEstimateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Triggers AI materials estimations for a project (Admin/PM)."""
    _ = get_project_and_verify_write_access(req.project_id, db, current_user)
    return MaterialService.estimate_and_save_materials(db, req)

@router.get("/project/{project_id}", response_model=List[schemas.MaterialResponse])
def get_project_materials(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Gets all estimated materials for a project (All roles)."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    return MaterialService.get_project_materials(db, project_id)

@router.put("/{id}", response_model=schemas.MaterialResponse)
def update_material_line(
    id: int,
    quantity: Decimal,
    unit_price: Decimal,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Updates estimated material quantities (Admin/PM)."""
    # Fetch material
    from app.models.material import Material as DB_Material
    mat = db.query(DB_Material).filter(DB_Material.id == id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material line not found.")
        
    _ = get_project_and_verify_write_access(mat.project_id, db, current_user)
    updated = MaterialService.update_material(db, id, quantity, unit_price)
    return updated

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material_line(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Removes a material estimation line (Admin/PM)."""
    from app.models.material import Material as DB_Material
    mat = db.query(DB_Material).filter(DB_Material.id == id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material line not found.")
        
    _ = get_project_and_verify_write_access(mat.project_id, db, current_user)
    MaterialService.delete_material(db, id)
    return None

@router.get("/inventory/list", response_model=List[schemas.InventoryResponse])
def get_inventory_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Lists warehouse stock inventory (All roles)."""
    return MaterialService.get_inventory(db)

@router.post("/inventory/update", response_model=schemas.InventoryResponse)
def update_inventory_stock(
    req: schemas.InventoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Modifies warehouse stock levels (Admin/PM)."""
    return MaterialService.update_inventory(db, req.material_name, req.quantity_change)

@router.get("/suppliers/list", response_model=List[schemas.SupplierResponse])
def get_suppliers_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Lists supply vendors (All roles)."""
    return MaterialService.get_suppliers(db)

@router.post("/purchase-orders", response_model=schemas.PurchaseOrderResponse)
def create_purchase_order(
    req: schemas.PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.ADMIN, UserRole.PROJECT_MANAGER]))
):
    """Creates a purchase order and reserves inventory (Admin/PM)."""
    _ = get_project_and_verify_write_access(req.project_id, db, current_user)
    return MaterialService.create_purchase_order(db, req)

@router.get("/purchase-orders/list", response_model=List[schemas.PurchaseOrderResponse])
def get_purchase_orders(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Lists purchase orders (All roles)."""
    if project_id is not None:
        _ = get_project_and_verify_view_access(project_id, db, current_user)
    return MaterialService.get_purchase_orders(db, project_id)

@router.get("/project/{project_id}/csv")
def download_project_materials_csv(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Streams the material planning list as a downloadable CSV."""
    _ = get_project_and_verify_view_access(project_id, db, current_user)
    materials = MaterialService.get_project_materials(db, project_id)
    csv_content = ReportExporter.generate_materials_csv(materials)
    
    filename = f"materials_project_{project_id}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
