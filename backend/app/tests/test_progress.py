import pytest
from datetime import date
from decimal import Decimal
from app.models.user import UserRole
from app.models.progress import Milestone, DailyLog, ProgressReport

def get_auth_headers(client, email, password, role="Site Engineer", name="Test User"):
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": name, "role": role}
    )
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_progress_monitoring_workflow(client, db):
    admin_headers = get_auth_headers(client, "prog_admin@example.com", "adminpass", "Admin")
    pm_headers = get_auth_headers(client, "prog_pm@example.com", "pmpass", "Project Manager")
    eng_headers = get_auth_headers(client, "prog_eng@example.com", "engpass", "Site Engineer")

    # 1. Create a project
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Metro Extension Phase 7",
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

    # 2. Create Milestones (Admin/PM)
    ms_resp = client.post(
        "/api/milestone",
        json={
            "project_id": proj_id,
            "milestone_name": "Phase 1 Concreting",
            "description": "Foundation pour",
            "planned_end_date": "2026-12-01",
            "completion_percentage": 50.0,
            "status": "Planning"
        },
        headers=pm_headers
    )
    assert ms_resp.status_code == 200
    assert ms_resp.json()["status"] == "On-Time"

    # Create Completed milestone
    ms_comp = client.post(
        "/api/milestone",
        json={
            "project_id": proj_id,
            "milestone_name": "Excavation",
            "description": "Soil prep",
            "planned_end_date": "2026-10-15",
            "completion_percentage": 100.0,
            "status": "Planning"
        },
        headers=pm_headers
    )
    assert ms_comp.status_code == 200
    assert ms_comp.json()["status"] == "Completed"

    # 3. Post Daily update log with image upload mock (Site Engineer)
    import io
    file_payload = {"file": ("progress.jpg", io.BytesIO(b"dummy image data"), "image/jpeg")}
    form_payload = {
        "project_id": str(proj_id),
        "log_date": "2026-10-05",
        "update_text": "Completed concrete column pouring for section A."
    }

    log_resp = client.post(
        "/api/progress/update",
        data=form_payload,
        files=file_payload,
        headers=eng_headers
    )
    assert log_resp.status_code == 200
    assert log_resp.json()["image_path"] is not None

    # 4. Fetch Progress cockpit summary (All roles)
    sum_resp = client.get(f"/api/progress/project/{proj_id}", headers=eng_headers)
    assert sum_resp.status_code == 200
    sum_data = sum_resp.json()
    # Overall completion: (50 + 100) / 2 = 75%
    assert float(sum_data["overall_completion"]) == 75.0
    assert len(sum_data["milestones"]) == 2
    assert len(sum_data["latest_logs"]) == 1

    # 5. Download Progress Report PDF
    pdf_resp = client.get(f"/api/reports/progress/{proj_id}?format=pdf", headers=eng_headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 0

    # Download Progress Report CSV Excel
    csv_resp = client.get(f"/api/reports/progress/{proj_id}?format=excel", headers=eng_headers)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert len(csv_resp.content) > 0
