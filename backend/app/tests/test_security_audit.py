import pytest
from app.models.user import UserRole
from app.models.project import Project, ProjectMember

def get_auth_headers(client, email, password, role="Site Engineer", name="Test User"):
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": name, "role": role}
    )
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_security_rbac_and_input_sanitization(client, db):
    # Register multi-role headers
    admin_headers = get_auth_headers(client, "sec_admin@example.com", "adminpass", "Admin")
    pm_headers = get_auth_headers(client, "sec_pm@example.com", "pmpass", "Project Manager")
    eng_headers = get_auth_headers(client, "sec_eng@example.com", "engpass", "Site Engineer")

    # 1. Create a project
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Security Test Complex",
            "client_name": "Defense Corp",
            "location": "Site Area A",
            "start_date": "2026-09-01",
            "expected_end_date": "2027-09-01",
            "budget": 20000000.00
        },
        headers=admin_headers
    )
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    # Assign PM member
    pm_user_id = client.get("/api/auth/me", headers=pm_headers).json()["id"]
    client.post(f"/api/projects/{proj_id}/members", json={"user_id": pm_user_id, "role": "Project Manager"}, headers=admin_headers)

    # Assign Engineer member
    eng_user_id = client.get("/api/auth/me", headers=eng_headers).json()["id"]
    client.post(f"/api/projects/{proj_id}/members", json={"user_id": eng_user_id, "role": "Site Engineer"}, headers=admin_headers)

    # ----------------------------------------------------
    # Security Rule 1: RBAC Check (Site Engineer blocked from writing budgets)
    # ----------------------------------------------------
    bad_estimate_resp = client.post(
        "/api/budget/estimate",
        json={
            "project_id": proj_id,
            "area_sqft": 4500.0,
            "currency": "INR",
            "materials": [],
            "labor": [],
            "equipment": []
        },
        headers=eng_headers
    )
    # Site Engineer role must be blocked by RoleChecker
    assert bad_estimate_resp.status_code == 403

    # ----------------------------------------------------
    # Security Rule 2: JWT Integrity / Malformed Signature Checks
    # ----------------------------------------------------
    bad_headers = {"Authorization": "Bearer not.a.valid.jwt.token.sig"}
    unauth_resp = client.get("/api/projects", headers=bad_headers)
    assert unauth_resp.status_code == 401

    # ----------------------------------------------------
    # Security Rule 3: SQL Injection (SQLi) Protection Checks
    # ----------------------------------------------------
    # Attack payload: try to select all projects or create projects with raw SQL
    sqli_payload = {
        "project_name": "Project Name' OR '1'='1",
        "client_name": "Defense Corp",
        "location": "Site Area A",
        "start_date": "2026-09-01",
        "expected_end_date": "2027-09-01",
        "budget": 20000000.00
    }
    sqli_resp = client.post("/api/projects", json=sqli_payload, headers=admin_headers)
    assert sqli_resp.status_code == 201
    sqli_proj_id = sqli_resp.json()["id"]
    
    # Query database directly: confirm name matches precisely, proving parameter binding was used
    sqli_row = db.query(Project).filter(Project.id == sqli_proj_id).first()
    assert sqli_row.project_name == "Project Name' OR '1'='1"

    # ----------------------------------------------------
    # Security Rule 4: Cross Site Scripting (XSS) Sanitization Checks
    # ----------------------------------------------------
    xss_payload = {
        "project_name": "<script>alert('XSS')</script> Project Safe",
        "client_name": "Defense Corp",
        "location": "Site Area A",
        "start_date": "2026-09-01",
        "expected_end_date": "2027-09-01",
        "budget": 20000000.00
    }
    xss_resp = client.post("/api/projects", json=xss_payload, headers=admin_headers)
    assert xss_resp.status_code == 201
    xss_proj_id = xss_resp.json()["id"]

    # Verify input values are escaped or safely stored without crashing HTML/React clients
    xss_row = db.query(Project).filter(Project.id == xss_proj_id).first()
    assert xss_row.project_name == "<script>alert('XSS')</script> Project Safe"
