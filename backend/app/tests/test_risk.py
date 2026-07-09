import pytest
from decimal import Decimal
from app.models.user import UserRole
from app.models.risk import Risk, WeatherData, DelayPrediction

def get_auth_headers(client, email, password, role="Site Engineer", name="Test User"):
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": name, "role": role}
    )
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_risk_prediction_workflow(client, db):
    admin_headers = get_auth_headers(client, "risk_admin@example.com", "adminpass", "Admin")
    pm_headers = get_auth_headers(client, "risk_pm@example.com", "pmpass", "Project Manager")
    eng_headers = get_auth_headers(client, "risk_eng@example.com", "engpass", "Site Engineer")

    # 1. Create a project
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Metro Extension Phase 6",
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

    # 2. Trigger risk analysis via PM -> SUCCESS
    analysis_resp = client.post(
        "/api/risk/analyze",
        json={"project_id": proj_id},
        headers=pm_headers
    )
    assert analysis_resp.status_code == 201
    data = analysis_resp.json()
    assert "risk" in data
    assert "delay_prediction" in data
    assert "weather" in data
    
    # Defaults composite index with zero values should be low/moderate (staff shortage triggers ~45 index score)
    assert data["risk"]["risk_score"] < 60
    assert float(data["risk"]["delay_probability"]) < 60.0

    # 3. Trigger risk analysis via Site Engineer -> FORBIDDEN (RBAC)
    forbidden_resp = client.post(
        "/api/risk/analyze",
        json={"project_id": proj_id},
        headers=eng_headers
    )
    assert forbidden_resp.status_code == 403

    # 4. Fetch current risk assessment (All roles)
    get_resp = client.get(f"/api/risk/project/{proj_id}", headers=eng_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["risk"]["project_id"] == proj_id

    # 5. Fetch risk history log
    hist_resp = client.get(f"/api/risk/history/{proj_id}", headers=eng_headers)
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) > 0

    # 6. Download Risk Report PDF
    pdf_resp = client.get(f"/api/reports/risk/{proj_id}?format=pdf", headers=eng_headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 0

    # Download Risk Report CSV Excel
    csv_resp = client.get(f"/api/reports/risk/{proj_id}?format=excel", headers=eng_headers)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert len(csv_resp.content) > 0
