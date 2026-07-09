import pytest
from decimal import Decimal
from app.models.user import UserRole
from app.models.material import Inventory, Supplier

def get_auth_headers(client, email, password, role="Site Engineer", name="Test User"):
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": name, "role": role}
    )
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_material_planning_workflow(client, db):
    admin_headers = get_auth_headers(client, "mat_admin@example.com", "adminpass", "Admin")
    pm_headers = get_auth_headers(client, "mat_pm@example.com", "pmpass", "Project Manager")
    eng_headers = get_auth_headers(client, "mat_eng@example.com", "engpass", "Site Engineer")

    # 1. Create a project
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Metro Extension Phase 4",
            "client_name": "DMRC",
            "location": "Noida",
            "start_date": "2026-10-01",
            "expected_end_date": "2028-10-01",
            "budget": 80000000.00
        },
        headers=admin_headers
    )
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    # Assign PM member
    pm_user_id = client.get("/api/auth/me", headers=pm_headers).json()["id"]
    client.post(
        f"/api/projects/{proj_id}/members",
        json={"user_id": pm_user_id, "role": "Project Manager"},
        headers=admin_headers
    )

    # Assign Engineer member
    eng_user_id = client.get("/api/auth/me", headers=eng_headers).json()["id"]
    client.post(
        f"/api/projects/{proj_id}/members",
        json={"user_id": eng_user_id, "role": "Site Engineer"},
        headers=admin_headers
    )

    # 2. Register initial stocks and seed suppliers
    client.post(
        "/api/materials/inventory/update",
        json={"material_name": "Cement", "quantity_change": 100.0},
        headers=admin_headers
    )

    # Seed supplier in database directly using pytest transaction db session
    sup = Supplier(
        supplier_name="Ultratech Cement Ltd",
        rating=Decimal("4.8"),
        contact_info="1800-22-22",
        address="Mumbai",
        active=True
    )
    db.add(sup)
    db.commit()
    db.refresh(sup)
    sup_id = sup.id
    db.close()

    # 3. Trigger materials estimation via PM -> SUCCESS
    est_resp = client.post(
        "/api/materials/estimate",
        json={
            "project_id": proj_id,
            "area_sqft": 5000.0,
            "floors": 2,
            "building_type": "Commercial",
            "rooms": 4,
            "timeline_months": 18,
            "budget": 20000000.0,
            "project_category": "Commercial"
        },
        headers=pm_headers
    )
    assert est_resp.status_code == 201
    est_data = est_resp.json()
    assert len(est_data["materials"]) > 0
    
    # Area (5000) * coefficient (0.4) * floors (2) = 4000 bags
    cement_spec = next(m for m in est_data["materials"] if m["material_name"] == "Cement")
    assert float(cement_spec["quantity"]) == 4000.0

    # 4. Check low stock warnings
    assert len(est_data["low_stock_warnings"]) > 0

    # 5. Site Engineer estimate triggers -> FORBIDDEN
    forbidden_resp = client.post(
        "/api/materials/estimate",
        json={
            "project_id": proj_id,
            "area_sqft": 5000.0,
            "floors": 2,
            "building_type": "Commercial"
        },
        headers=eng_headers
    )
    assert forbidden_resp.status_code == 403

    # 6. PM creates purchase order
    po_resp = client.post(
        "/api/materials/purchase-orders",
        json={
            "project_id": proj_id,
            "supplier_id": sup_id,
            "material_name": "Cement",
            "quantity": 500.0,
            "unit_price": 400.0
        },
        headers=pm_headers
    )
    assert po_resp.status_code == 200
    assert po_resp.json()["status"] == "Pending"

    # 7. Verify inventory reservation updated
    inv_resp = client.get("/api/materials/inventory/list", headers=pm_headers)
    cement_inv = next(i for i in inv_resp.json() if i["material_name"] == "Cement")
    assert float(cement_inv["quantity_reserved"]) == 500.0

    # 8. Check CSV download
    csv_resp = client.get(f"/api/materials/project/{proj_id}/csv", headers=eng_headers)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert len(csv_resp.content) > 0
