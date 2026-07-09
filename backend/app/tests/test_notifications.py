import pytest
import time
from app.models.project import Project, ProjectMember
from app.models.notification import NotificationLog
from app.services.notification_service import NotificationService, BackgroundNotificationScheduler

def get_auth_headers(client, email, password, role="Project Manager"):
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User",
            "role": role
        }
    )
    resp = client.post(
        "/api/auth/login",
        data={"username": email, "password": password}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_notification_scheduler_and_dispatch(client, db):
    headers = get_auth_headers(client, "notify_pm@example.com", "pass123", "Project Manager")
    
    # 1. Setup Project & ProjectMember association
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Notify Site",
            "client_name": "Notify Corp",
            "location": "Sector 10",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "budget": 200000.00
        },
        headers=headers
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Add ProjectMember (so checker has a user object to alert)
    pm_user = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).first()
    assert pm_user is not None
    user_id = pm_user.user_id

    # 3. Explicitly trigger manual alert
    logs = NotificationService.trigger_operational_alert(
        db=db,
        project_id=project_id,
        user_id=user_id,
        alert_type="Budget Exceeded",
        message="Manual budget overrun alert triggered.",
        recipient_email="notify_pm@example.com",
        recipient_phone="9999999999"
    )
    assert len(logs) == 3  # Email, WhatsApp, Push
    assert logs[0].channel == "Email"
    assert logs[1].channel == "WhatsApp"
    assert logs[2].channel == "Push"

    # Verify rows in DB
    db_logs = db.query(NotificationLog).filter(NotificationLog.project_id == project_id).all()
    assert len(db_logs) >= 3

    # 4. Start and Stop scheduler daemon to verify thread lifecycle does not crash
    BackgroundNotificationScheduler.start()
    time.sleep(1.0)
    BackgroundNotificationScheduler.stop()

    # 5. Verify API endpoint history retrieval
    api_resp = client.get(f"/api/notifications/history/{project_id}", headers=headers)
    assert api_resp.status_code == 200
    assert len(api_resp.json()) >= 3
    assert api_resp.json()[0]["project_id"] == project_id
    assert "alert_type" in api_resp.json()[0]
