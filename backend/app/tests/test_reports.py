import pytest
from app.models.budget import Budget
from app.models.project import Project

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

def test_report_center_endpoints(client, db):
    headers = get_auth_headers(client, "reports_pm@example.com", "pass123", "Project Manager")
    
    # 1. Setup Project & Budget
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Ledger Site",
            "client_name": "Ledger Corp",
            "location": "Sector 9",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "budget": 2000000.00
        },
        headers=headers
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # Insert budget so budget PDF report generation works
    budget = Budget(
        project_id=project_id,
        total_estimated_cost=1800000.00,
        total_optimized_cost=1700000.00,
        currency="INR"
    )
    db.add(budget)
    db.commit()

    # 2. Test PDF Budget Report
    pdf_resp = client.get(
        f"/api/reports/download?project_id={project_id}&report_type=budget&report_format=pdf",
        headers=headers
    )
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 0

    # 3. Test CSV Budget Report
    csv_resp = client.get(
        f"/api/reports/download?project_id={project_id}&report_type=budget&report_format=csv",
        headers=headers
    )
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert b"PROJECT BUDGET ESTIMATION LEDGER" in csv_resp.content

    # 4. Test Excel Budget Report (CSV table layout streamed)
    xls_resp = client.get(
        f"/api/reports/download?project_id={project_id}&report_type=budget&report_format=excel",
        headers=headers
    )
    assert xls_resp.status_code == 200
    assert "application/vnd.ms-excel" in xls_resp.headers["content-type"]

    # 5. Test Project Summary PDF Report
    summary_resp = client.get(
        f"/api/reports/download?project_id={project_id}&report_type=project_summary&report_format=pdf",
        headers=headers
    )
    assert summary_resp.status_code == 200
    assert summary_resp.headers["content-type"] == "application/pdf"
