import pytest

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

def test_executive_analytics_dashboard(client, db):
    # 1. Access without authentication (should be rejected)
    resp = client.get("/api/projects/executive/analytics")
    assert resp.status_code == 401

    # 2. Register PM and verify access
    headers = get_auth_headers(client, "exec_pm@example.com", "pass123", "Project Manager")
    
    # Create project to have data in DB
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Exec Building",
            "client_name": "Exec Corp",
            "location": "Sector 4",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "budget": 1000000.00
        },
        headers=headers
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 3. Pull analytics
    analytics_resp = client.get("/api/projects/executive/analytics", headers=headers)
    assert analytics_resp.status_code == 200
    
    data = analytics_resp.json()
    assert "widgets" in data
    assert "charts" in data
    assert "recent_recommendations" in data

    # Verify widgets structure
    widgets = data["widgets"]
    assert widgets["total_projects"] >= 1
    assert widgets["total_budget_limit"] >= 1000000.00
    assert widgets["attendance_rate"] >= 0.0

    # Verify charts structure
    charts = data["charts"]
    assert "line_risk_history" in charts
    assert "pie_budget_distribution" in charts
    assert "bar_material_costs" in charts
    assert "heatmap_attendance" in charts
    assert "timeline_milestones" in charts
    assert "forecast_progress" in charts

    # 4. Pull analytics with project filter
    filtered_resp = client.get(
        f"/api/projects/executive/analytics?project_id={project_id}",
        headers=headers
    )
    assert filtered_resp.status_code == 200
    assert filtered_resp.json()["widgets"]["total_projects"] == 1
