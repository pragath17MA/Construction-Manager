import os
import pytest
from datetime import date
from decimal import Decimal
from app.models.project import Project, SiteImage
from app.models.image_analysis import SiteImageAnalysis
from app.models.user import UserRole
from app.core import security
from PIL import Image

# Helper function to get authenticated headers
def get_auth_headers(client, email, password, role="Project Manager", name="PM User"):
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": name,
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

def test_image_analysis_endpoints(client, db):
    # 1. Setup Auth and Project
    headers = get_auth_headers(client, "pm_image@example.com", "pass123", "Project Manager")
    
    # Register project
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Visual Audit Build Site",
            "client_name": "Infrastructure Corp",
            "location": "Sector 62",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "budget": 5000000.00
        },
        headers=headers
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # Create dummy image on disk
    dummy_image_dir = os.path.join("uploads", "test")
    os.makedirs(dummy_image_dir, exist_ok=True)
    dummy_image_path = os.path.join(dummy_image_dir, "test_site.jpg")
    
    # Write a dummy black image using Pillow
    img = Image.new("RGB", (100, 100), color="black")
    img.save(dummy_image_path)

    # 2. Insert SiteImage into db
    site_img = SiteImage(
        project_id=project_id,
        image_path=dummy_image_path,
        capture_date=date.today()
    )
    db.add(site_img)
    db.commit()
    db.refresh(site_img)
    site_image_id = site_img.id

    # 3. Trigger Visual Analysis via endpoint
    req_body = {
        "project_id": project_id,
        "site_image_id": site_image_id
    }
    
    resp = client.post(
        "/api/image-analysis/analyze",
        json=req_body,
        headers=headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["project_id"] == project_id
    assert data["site_image_id"] == site_image_id
    assert "construction_stage" in data
    assert float(data["progress_percentage"]) >= 0.0
    assert len(data["safety_issues"]) > 0
    assert data["recommendations"] is not None
    analysis_id = data["id"]

    # 4. Fetch analysis by project
    get_proj_resp = client.get(
        f"/api/image-analysis/project/{project_id}",
        headers=headers
    )
    assert get_proj_resp.status_code == 200
    proj_analyses = get_proj_resp.json()
    assert len(proj_analyses) > 0
    assert proj_analyses[0]["id"] == analysis_id

    # 5. Fetch analysis by image
    get_img_resp = client.get(
        f"/api/image-analysis/image/{site_image_id}",
        headers=headers
    )
    assert get_img_resp.status_code == 200
    assert get_img_resp.json()["id"] == analysis_id

    # 6. Fetch annotated image file
    get_file_resp = client.get(
        f"/api/image-analysis/annotated-image/{analysis_id}",
        headers=headers
    )
    assert get_file_resp.status_code == 200
    assert len(get_file_resp.content) > 0

    # Clean up dummy images
    if os.path.exists(dummy_image_path):
        os.remove(dummy_image_path)
    if os.path.exists(data["annotated_image_path"]):
        os.remove(data["annotated_image_path"])
