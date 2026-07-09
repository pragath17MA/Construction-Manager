import pytest
from datetime import date
from decimal import Decimal
from app.models.user import UserRole
from app.models.worker import Worker

def get_auth_headers(client, email, password, role="Site Engineer", name="Test User"):
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": name, "role": role}
    )
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_workers_and_scheduling_workflow(client):
    admin_headers = get_auth_headers(client, "work_admin@example.com", "adminpass", "Admin")
    pm_headers = get_auth_headers(client, "work_pm@example.com", "pmpass", "Project Manager")
    eng_headers = get_auth_headers(client, "work_eng@example.com", "engpass", "Site Engineer")

    # 1. Create a project
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Metro Extension Phase 5",
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

    # 2. Add active system workers (Admin)
    w1_resp = client.post(
        "/api/workers",
        json={
            "full_name": "Ramesh Kumar",
            "email": "ramesh@example.com",
            "phone": "9876543210",
            "role_title": "Mason",
            "worker_type": "Skilled",
            "wage_rate": 800.00,
            "skills": [{"skill_name": "Brickwork", "proficiency_level": "Expert"}]
        },
        headers=admin_headers
    )
    assert w1_resp.status_code == 201
    w1_id = w1_resp.json()["id"]

    w2_resp = client.post(
        "/api/workers",
        json={
            "full_name": "Suresh Singh",
            "email": "suresh@example.com",
            "phone": "9876543211",
            "role_title": "Supervisor",
            "worker_type": "Skilled",
            "wage_rate": 1200.00,
            "skills": [{"skill_name": "Management", "proficiency_level": "Expert"}]
        },
        headers=admin_headers
    )
    assert w2_resp.status_code == 201
    w2_id = w2_resp.json()["id"]

    # 3. Log attendance (Site Engineer)
    att_resp = client.post(
        "/api/attendance",
        json={
            "worker_id": w1_id,
            "date": "2026-10-05",
            "status": "Present",
            "hours_worked": 8.0,
            "overtime_hours": 2.0
        },
        headers=eng_headers
    )
    assert att_resp.status_code == 200

    # 4. Submit leave request (Site Engineer)
    leave_resp = client.post(
        "/api/attendance/leave",
        json={
            "worker_id": w2_id,
            "start_date": "2026-10-10",
            "end_date": "2026-10-12",
            "leave_type": "Sick",
            "reason": "Fever recovery"
        },
        headers=eng_headers
    )
    assert leave_resp.status_code == 200
    leave_id = leave_resp.json()["id"]

    # Approve leave request (PM)
    app_resp = client.put(
        f"/api/attendance/leave/{leave_id}/approve",
        json={"status": "Approved"},
        headers=pm_headers
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "Approved"

    # 5. Trigger AI Shift Optimizer (PM)
    shift_resp = client.post(
        "/api/workers/shift-planner",
        json={
            "project_id": proj_id,
            "start_date": "2026-10-05",
            "end_date": "2026-10-12"
        },
        headers=pm_headers
    )
    assert shift_resp.status_code == 200
    shift_data = shift_resp.json()
    assert len(shift_data["plans"]) == 2
    # Ramesh should be scheduled, Suresh is on leave from 10-12, but this shift is from 10-05 to 10-12.
    # Shortage warnings should pop up since we have very few workers in total
    assert len(shift_data["shortage_warnings"]) > 0

    # 6. Stream shift report PDF (All)
    report_resp = client.get(
        f"/api/workers/worker-report/{proj_id}?start_date=2026-10-05&end_date=2026-10-12",
        headers=eng_headers
    )
    assert report_resp.status_code == 200
    assert report_resp.headers["content-type"] == "application/pdf"
    assert len(report_resp.content) > 0

    # 7. Stream attendance CSV
    csv_resp = client.get("/api/attendance/csv", headers=eng_headers)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert len(csv_resp.content) > 0
