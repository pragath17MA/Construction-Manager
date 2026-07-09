import pytest
import io
from app.models.user import UserRole
from app.models.invoice import Invoice, InvoiceItem
from app.services.ocr_service import InvoiceService

def get_auth_headers(client, email, password, role="Site Engineer", name="Test User"):
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": name, "role": role}
    )
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_invoice_audit_reconciliation_pipeline(client, db):
    admin_headers = get_auth_headers(client, "inv_admin@example.com", "adminpass", "Admin")
    pm_headers = get_auth_headers(client, "inv_pm@example.com", "pmpass", "Project Manager")
    eng_headers = get_auth_headers(client, "inv_eng@example.com", "engpass", "Site Engineer")

    # 1. Create project
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Galaxy Arcade Invoices",
            "client_name": "Galaxy Mall Group",
            "location": "Noida",
            "start_date": "2026-11-01",
            "expected_end_date": "2028-11-01",
            "budget": 95000000.00
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

    # Assign Site Engineer member
    eng_user_id = client.get("/api/auth/me", headers=eng_headers).json()["id"]
    client.post(
        f"/api/projects/{proj_id}/members",
        json={"user_id": eng_user_id, "role": "Site Engineer"},
        headers=admin_headers
    )

    # Seed a budget item to test budget comparisons
    # Budgets are mapped based on project ID
    client.post(
        "/api/budget/estimate",
        json={
            "project_id": proj_id,
            "area_sqft": 5000.0,
            "floors": 2,
            "structure_type": "Commercial",
            "materials_grade": "Premium",
            "indirect_factor": 10.0,
            "contingency_factor": 5.0
        },
        headers=pm_headers
    )

    # 2. Test invoice uploads (Admin/PM)
    file_bytes = b"dummy pdf content representing invoice Tata Steel"
    file_payload = {"file": ("invoice_tata.pdf", io.BytesIO(file_bytes), "application/pdf")}
    form_payload = {"project_id": str(proj_id)}

    # Site Engineer -> 403 Forbidden
    upload_fail = client.post(
        "/api/invoice/upload",
        data=form_payload,
        files=file_payload,
        headers=eng_headers
    )
    assert upload_fail.status_code == 403

    # PM -> 201 Created
    file_payload = {"file": ("invoice_tata.pdf", io.BytesIO(file_bytes), "application/pdf")}
    upload_ok = client.post(
        "/api/invoice/upload",
        data=form_payload,
        files=file_payload,
        headers=pm_headers
    )
    assert upload_ok.status_code == 201
    inv_data = upload_ok.json()
    assert inv_data["status"] == "Pending"
    inv_id = inv_data["id"]

    # 3. Synchronously run OCR processing
    processed_inv = InvoiceService.process_ocr(db, inv_id)
    assert processed_inv.status == "Completed"
    assert len(processed_inv.items) > 0

    # 4. Trigger Analysis (Fraud check & Budget comparison)
    analysis_resp = client.post(
        "/api/invoice/analyze",
        json={"invoice_id": inv_id},
        headers=pm_headers
    )
    assert analysis_resp.status_code == 200
    res = analysis_resp.json()
    assert "fraud_risk_score" in res
    assert res["is_duplicate"] is False

    # 5. Upload Duplicate invoice and verify audit detects it
    # Upload same file and same invoice info
    file_payload_dup = {"file": ("invoice_tata_dup.pdf", io.BytesIO(file_bytes), "application/pdf")}
    upload_dup = client.post(
        "/api/invoice/upload",
        data=form_payload,
        files=file_payload_dup,
        headers=pm_headers
    )
    assert upload_dup.status_code == 201
    dup_inv_id = upload_dup.json()["id"]

    # Sync OCR and Sync analyze
    InvoiceService.process_ocr(db, dup_inv_id)
    dup_analysis = client.post(
        "/api/invoice/analyze",
        json={"invoice_id": dup_inv_id},
        headers=pm_headers
    )
    assert dup_analysis.status_code == 200
    dup_res = dup_analysis.json()
    assert dup_res["is_duplicate"] is True
    assert float(dup_res["fraud_risk_score"]) == 100.0 # High fraud alarm due to double billing Conflict

    # 6. Verify detail retrieval
    details = client.get(f"/api/invoice/{inv_id}", headers=eng_headers)
    assert details.status_code == 200
    assert len(details.json()["items"]) > 0

    # 7. Download PDF compliance report
    pdf_resp = client.get(f"/api/invoice/report/{inv_id}?format=pdf", headers=eng_headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 0

    # Download CSV compliance sheet
    csv_resp = client.get(f"/api/invoice/report/{inv_id}?format=excel", headers=eng_headers)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert len(csv_resp.content) > 0
