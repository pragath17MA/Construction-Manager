import pytest
from decimal import Decimal
from app.models.user import UserRole

def get_auth_headers(client, email, password, role="Site Engineer", name="Test User"):
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": name,
            "role": role
        }
    )
    # Login
    resp = client.post(
        "/api/auth/login",
        data={"username": email, "password": password}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_budget_estimation_workflow(client):
    # Setup users
    admin_headers = get_auth_headers(client, "b_admin@example.com", "adminpass", "Admin", "Admin User")
    pm_headers = get_auth_headers(client, "b_pm@example.com", "pmpass", "Project Manager", "PM User")
    eng_headers = get_auth_headers(client, "b_eng@example.com", "engpass", "Site Engineer", "Engineer User")

    # 1. Create a project
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Flyover Construction Zone B",
            "client_name": "Delhi Metro Corp",
            "location": "New Delhi",
            "start_date": "2026-09-01",
            "expected_end_date": "2027-09-01",
            "budget": 50000000.00
        },
        headers=admin_headers
    )
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    # Add PM and Site Engineer as members of the project so they have visibility/edit rights
    pm_user_id = client.get("/api/auth/me", headers=pm_headers).json()["id"]
    eng_user_id = client.get("/api/auth/me", headers=eng_headers).json()["id"]

    client.post(f"/api/projects/{proj_id}/members", json={"user_id": pm_user_id, "role": "Project Manager"}, headers=admin_headers)
    client.post(f"/api/projects/{proj_id}/members", json={"user_id": eng_user_id, "role": "Site Engineer"}, headers=admin_headers)

    # 2. Test input validation (Reject area <= 0)
    invalid_resp = client.post(
        "/api/budget/estimate",
        json={
            "project_id": proj_id,
            "area_sqft": 0, # invalid
            "materials": [{"material": "Cement Bags", "quantity": 100, "unit_price": 400}],
            "labor": [],
            "equipment": []
        },
        headers=pm_headers
    )
    assert invalid_resp.status_code == 422

    # 3. Perform a valid estimation
    # Formulas check:
    # Materials = 1000 bags * 400 = 400,000; 10 Tons steel * 60,000 = 600,000. Total Materials = 1,000,000
    # Labor = 10 workers * 800/day * 20 days = 160,000
    # Equipment = 1 machine * 5000/day * 5 days = 25,000
    # Subtotal (Material + Labor + Equipment) = 1,000,000 + 160,000 + 25,000 = 1,185,000
    # Indirect = 10% of subtotal = 118,500
    # Contingency = 5% of (subtotal + indirect) = 5% of 1,303,500 = 65,175
    # Total Estimated = 1,303,500 + 65,175 = 1,368,675.00
    estimate_payload = {
        "project_id": proj_id,
        "area_sqft": 4500.0,
        "currency": "INR",
        "materials": [
            {"material": "Cement Bags", "quantity": 1000.0, "unit_price": 400.0},
            {"material": "Structural Steel", "quantity": 10.0, "unit_price": 60000.0}
        ],
        "labor": [
            {"worker_type": "Masons", "worker_count": 10, "daily_rate": 800.0, "days": 20}
        ],
        "equipment": [
            {"equipment_name": "Excavator Loader", "daily_rate": 5000.0, "days_used": 5}
        ]
    }

    estimate_resp = client.post("/api/budget/estimate", json=estimate_payload, headers=pm_headers)
    assert estimate_resp.status_code == 201
    est_data = estimate_resp.json()
    budget_id = est_data["id"]

    assert float(est_data["estimated_cost"]) == 1368675.0
    assert float(est_data["optimized_cost"]) <= 1368675.0
    assert est_data["currency"] == "INR"

    # 4. Get active project budget (Engineer view only access)
    get_resp = client.get(f"/api/budget/{proj_id}", headers=eng_headers)
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert float(detail["budget"]["estimated_cost"]) == 1368675.0
    assert len(detail["labor_costs"]) == 1
    assert float(detail["labor_costs"][0]["total_cost"]) == 160000.0

    # 5. Site Engineer triggers new estimate -> FORBIDDEN (restricted to Admin/PM)
    forbidden_resp = client.post("/api/budget/estimate", json=estimate_payload, headers=eng_headers)
    assert forbidden_resp.status_code == 403

    # 6. Update budget (Admin/PM)
    update_payload = {
        "estimated_cost": 960000.00,
        "optimized_cost": 910000.00,
        "items": [
            {"category": "Material", "description": "Bulk Cement", "quantity": 1.0, "unit_price": 400000.0},
            {"category": "Labor", "description": "Contract labor", "quantity": 1.0, "unit_price": 300000.0}
        ]
    }
    update_resp = client.put(f"/api/budget/update/{budget_id}", json=update_payload, headers=pm_headers)
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert float(updated_data["estimated_cost"]) == 960000.0
    assert float(updated_data["optimized_cost"]) == 910000.0
    assert len(updated_data["items"]) == 2

    # 7. Download PDF report (Streams successfully)
    report_resp = client.get(f"/api/budget/report/{budget_id}", headers=eng_headers)
    assert report_resp.status_code == 200
    assert report_resp.headers["content-type"] == "application/pdf"
    assert len(report_resp.content) > 0

    # 8. Delete budget (PM)
    del_resp = client.delete(f"/api/budget/{budget_id}", headers=pm_headers)
    assert del_resp.status_code == 204

    # Verify deleted
    get_deleted = client.get(f"/api/budget/{proj_id}", headers=pm_headers)
    assert get_deleted.status_code == 404
