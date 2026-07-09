import io
import pytest
from app.models.user import UserRole
from app.models.project import ProjectStatus
from app.core import security

# Helper function to get authenticated headers
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

def test_create_project(client):
    admin_headers = get_auth_headers(client, "admin@example.com", "adminpass", "Admin", "Admin User")
    
    # 1. Successful project creation
    response = client.post(
        "/api/projects",
        json={
            "project_name": "Terminal Building Construction",
            "description": "Constructing main terminal building",
            "client_name": "Aviation Board",
            "location": "New Delhi",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "status": "Planning",
            "budget": 250000000.00
        },
        headers=admin_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["project_name"] == "Terminal Building Construction"
    assert float(data["budget"]) == 250000000.00
    
    # 2. Date constraint check (expected_end_date <= start_date)
    response_date_error = client.post(
        "/api/projects",
        json={
            "project_name": "Terminal Building Construction 2",
            "description": "Constructing main terminal building",
            "client_name": "Aviation Board",
            "location": "New Delhi",
            "start_date": "2026-08-01",
            "expected_end_date": "2026-07-01",
            "status": "Planning",
            "budget": 250000000.00
        },
        headers=admin_headers
    )
    assert response_date_error.status_code == 422 # Pydantic model validation failure
    
    # 3. Budget constraint check (budget <= 0)
    response_budget_error = client.post(
        "/api/projects",
        json={
            "project_name": "Terminal Building Construction 3",
            "description": "Constructing main terminal building",
            "client_name": "Aviation Board",
            "location": "New Delhi",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "status": "Planning",
            "budget": 0
        },
        headers=admin_headers
    )
    assert response_budget_error.status_code == 422

def test_project_uniqueness(client):
    admin_headers = get_auth_headers(client, "admin2@example.com", "adminpass", "Admin")
    
    # Register first project
    client.post(
        "/api/projects",
        json={
            "project_name": "Bridge Phase 1",
            "client_name": "PWD Delhi",
            "location": "Delhi",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "budget": 10000000.00
        },
        headers=admin_headers
    )
    
    # Re-register same project name for same client -> 400 Bad Request
    resp = client.post(
        "/api/projects",
        json={
            "project_name": "Bridge Phase 1",
            "client_name": "PWD Delhi",
            "location": "Noida",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "budget": 20000000.00
        },
        headers=admin_headers
    )
    assert resp.status_code == 400
    assert "already exists for the specified client" in resp.json()["detail"]

def test_site_engineer_update_restrictions(client):
    admin_headers = get_auth_headers(client, "admin3@example.com", "adminpass", "Admin")
    eng_headers = get_auth_headers(client, "engineer@example.com", "engpass", "Site Engineer", "Engineer User")
    
    # Create project
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Smart Highway",
            "client_name": "NHAI",
            "location": "UP",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "budget": 12000000.00
        },
        headers=admin_headers
    )
    proj_id = proj_resp.json()["id"]
    
    # Site Engineer can't write because they are not a member of the project yet
    resp = client.patch(
        f"/api/projects/{proj_id}",
        json={"status": "In Progress"},
        headers=eng_headers
    )
    assert resp.status_code == 403
    
    # Add Site Engineer to Project Members
    me_resp = client.get("/api/auth/me", headers=eng_headers)
    eng_user_id = me_resp.json()["id"]
    
    client.post(
        f"/api/projects/{proj_id}/members",
        json={"user_id": eng_user_id, "role": "Site Engineer"},
        headers=admin_headers
    )
    
    # Engineer updates project status -> SUCCESS
    resp_success = client.patch(
        f"/api/projects/{proj_id}",
        json={"status": "In Progress"},
        headers=eng_headers
    )
    assert resp_success.status_code == 200
    assert resp_success.json()["status"] == "In Progress"
    
    # Engineer attempts to edit project budget -> FORBIDDEN
    resp_forbidden = client.patch(
        f"/api/projects/{proj_id}",
        json={"budget": 99999.00},
        headers=eng_headers
    )
    assert resp_forbidden.status_code == 403
    assert "only permitted to update the project status" in resp_forbidden.json()["detail"]

def test_file_upload_validation(client):
    admin_headers = get_auth_headers(client, "admin4@example.com", "adminpass", "Admin")
    
    # Create project
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Commercial Complex",
            "client_name": "DLF",
            "location": "Gurugram",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "budget": 350000000.00
        },
        headers=admin_headers
    )
    proj_id = proj_resp.json()["id"]
    
    # 1. Upload valid drawing PDF -> SUCCESS
    pdf_content = b"%PDF-1.4 mock content"
    resp_pdf = client.post(
        f"/api/projects/{proj_id}/drawings",
        data={"drawing_name": "Architectural Elevation Plan"},
        files={"file": ("elevation.pdf", pdf_content, "application/pdf")},
        headers=admin_headers
    )
    assert resp_pdf.status_code == 200
    assert resp_pdf.json()["drawing_name"] == "Architectural Elevation Plan"
    
    # 2. Upload invalid drawing extension/MIME -> FAILURE
    resp_bad = client.post(
        f"/api/projects/{proj_id}/drawings",
        data={"drawing_name": "Bad Drawing"},
        files={"file": ("elevation.png", b"image bytes", "image/png")},
        headers=admin_headers
    )
    assert resp_bad.status_code == 400
    assert "not allowed" in resp_bad.json()["detail"]

    # 3. Upload oversized drawing (> 10MB) -> FAILURE
    large_pdf_content = b"%PDF-1.4 " + b"x" * (11 * 1024 * 1024)
    resp_oversized = client.post(
        f"/api/projects/{proj_id}/drawings",
        data={"drawing_name": "Huge Blueprint"},
        files={"file": ("huge.pdf", large_pdf_content, "application/pdf")},
        headers=admin_headers
    )
    assert resp_oversized.status_code == 400
    assert "exceeds the limit" in resp_oversized.json()["detail"]
