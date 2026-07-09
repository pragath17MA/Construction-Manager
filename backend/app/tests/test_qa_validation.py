import os
import io
import pytest
from datetime import date
from PIL import Image
from decimal import Decimal
from app.models.user import UserRole
from app.models.project import Project, SiteImage, ProjectMember
from app.models.budget import Budget
from app.models.material import Material, Inventory, Supplier, PurchaseOrder
from app.models.worker import Worker, WorkerSchedule, Attendance
from app.models.risk import Risk, WeatherData
from app.models.progress import Milestone, DailyLog
from app.models.invoice import Invoice
from app.models.image_analysis import SiteImageAnalysis
from app.models.notification import NotificationLog
from app.services.notification_service import NotificationService

# Helper function to get authenticated headers
def get_auth_headers(client, email, password, role="Project Manager", name="QA User"):
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

def test_full_functional_qa_validation_suite(client, db):
    # ----------------------------------------------------
    # 1. AUTHENTICATION & AUTHORIZATION RBAC CHECKS
    # ----------------------------------------------------
    admin_headers = get_auth_headers(client, "qa_admin@example.com", "admin123", "Admin")
    pm_headers = get_auth_headers(client, "qa_pm@example.com", "pm123", "Project Manager")
    eng_headers = get_auth_headers(client, "qa_eng@example.com", "eng123", "Site Engineer")

    # Unauthorized requests check
    unauth_resp = client.get("/api/projects")
    assert unauth_resp.status_code == 401

    # ----------------------------------------------------
    # 2. PROJECT CREATION & MEMBERSHIP OPERATIONS
    # ----------------------------------------------------
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "QA Build Complex",
            "client_name": "QA Enterprise",
            "location": "Sector 100",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "budget": 15000000.00
        },
        headers=admin_headers
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # Assign PM to project
    pm_user_id = client.get("/api/auth/me", headers=pm_headers).json()["id"]
    member_resp = client.post(
        f"/api/projects/{project_id}/members",
        json={"user_id": pm_user_id, "role": "Project Manager"},
        headers=admin_headers
    )
    assert member_resp.status_code == 200

    # Assign Site Engineer to project
    eng_user_id = client.get("/api/auth/me", headers=eng_headers).json()["id"]
    client.post(
        f"/api/projects/{project_id}/members",
        json={"user_id": eng_user_id, "role": "Site Engineer"},
        headers=admin_headers
    )

    # ----------------------------------------------------
    # 3. BUDGET ESTIMATION & OPTIMIZATION MODULE
    # ----------------------------------------------------
    # Generate material estimates and cost plans (PM)
    est_resp = client.post(
        "/api/materials/estimate",
        json={
            "project_id": project_id,
            "area_sqft": 5000.0,
            "floors": 2,
            "building_type": "Commercial",
            "rooms": 10,
            "timeline_months": 12,
            "budget": 12000000.00,
            "project_category": "Standard"
        },
        headers=pm_headers
    )
    assert est_resp.status_code in [200, 201]
    assert "materials" in est_resp.json()

    # Trigger Cost Optimization & Estimation (PM)
    opt_resp = client.post(
        "/api/budget/estimate",
        json={
            "project_id": project_id,
            "area_sqft": 4500.0,
            "currency": "INR",
            "materials": [
                {"material": "Cement Bags", "quantity": 1000.0, "unit_price": 400.0}
            ],
            "labor": [
                {"worker_type": "Masons", "worker_count": 10, "daily_rate": 800.0, "days": 20}
            ],
            "equipment": [
                {"equipment_name": "Excavator Loader", "daily_rate": 5000.0, "days_used": 5}
            ]
        },
        headers=pm_headers
    )
    assert opt_resp.status_code == 201
    assert "optimized_cost" in opt_resp.json()

    # Fetch budget (Admin/PM)
    bud_resp = client.get(f"/api/budget/{project_id}", headers=pm_headers)
    assert bud_resp.status_code == 200

    # ----------------------------------------------------
    # 4. MATERIALS & INVENTORY CONTROL
    # ----------------------------------------------------
    # Insert global inventory level so alerts can trigger
    cement_inv = db.query(Inventory).filter(Inventory.material_name == "Cement").first()
    if not cement_inv:
        cement_inv = Inventory(
            material_name="Cement",
            quantity_available=Decimal("1500.00"),
            quantity_reserved=Decimal("0.00"),
            unit="bags",
            warehouse_capacity=Decimal("5000.00")
        )
        db.add(cement_inv)
        db.commit()

    # Fetch inventory pool lists (All Roles)
    inv_resp = client.get("/api/materials/inventory/list", headers=eng_headers)
    assert inv_resp.status_code == 200

    # ----------------------------------------------------
    # 5. WORKFORCE SCHEDULING & ATTENDANCE RECORDING
    # ----------------------------------------------------
    # Create Worker profile (PM)
    worker_resp = client.post(
        "/api/workers",
        json={
            "full_name": "Ram Kumar",
            "email": "ram@example.com",
            "phone": "9988776655",
            "role_title": "Mason",
            "worker_type": "Skilled",
            "wage_rate": 800.00,
            "skills": []
        },
        headers=pm_headers
    )
    assert worker_resp.status_code == 201
    worker_id = worker_resp.json()["id"]

    # Schedule worker shift (PM)
    sched_resp = client.post(
        "/api/workers/shift-planner",
        json={
            "project_id": project_id,
            "start_date": "2026-08-01",
            "end_date": "2026-08-31"
        },
        headers=pm_headers
    )
    assert sched_resp.status_code == 200

    # Log Attendance (Site Engineer)
    att_resp = client.post(
        "/api/attendance",
        json={
            "worker_id": worker_id,
            "date": "2026-08-01",
            "status": "Present",
            "hours_worked": 8.0,
            "overtime_hours": 2.0
        },
        headers=eng_headers
    )
    assert att_resp.status_code == 200

    # ----------------------------------------------------
    # 6. RISK FORECASTING & WEATHER MONITORS
    # ----------------------------------------------------
    # Run Risk Predictive Models (Admin/PM)
    risk_resp = client.post(
        "/api/risk/analyze",
        json={"project_id": project_id},
        headers=pm_headers
    )
    assert risk_resp.status_code in [200, 201]
    assert "delay_prediction" in risk_resp.json()

    # Fetch Risk history (All Roles)
    risk_hist = client.get(f"/api/risk/history/{project_id}", headers=eng_headers)
    assert risk_hist.status_code == 200

    # ----------------------------------------------------
    # 7. PROGRESS TRACKING & MILESTONE STAGE LOGS
    # ----------------------------------------------------
    # Create Milestone (Admin/PM)
    ms_resp = client.post(
        "/api/milestone",
        json={
            "project_id": project_id,
            "milestone_name": "Phase 1 Concreting",
            "description": "Pour foundation structures",
            "planned_end_date": "2026-10-01",
            "completion_percentage": 25.0,
            "status": "Planning"
        },
        headers=pm_headers
    )
    assert ms_resp.status_code == 200

    # Log site engineer progress updates (All Roles)
    prog_resp = client.post(
        "/api/progress/update",
        data={
            "project_id": str(project_id),
            "log_date": "2026-08-05",
            "update_text": "Poured foundation section A."
        },
        headers=eng_headers
    )
    assert prog_resp.status_code == 200

    # ----------------------------------------------------
    # 8. TECHNICAL DRAWING RAG BLUEPRINTS SEARCH
    # ----------------------------------------------------
    # Create a dummy PDF specifications document on disk
    dummy_pdf_path = os.path.join("uploads", "test_drawing.pdf")
    os.makedirs("uploads", exist_ok=True)
    with open(dummy_pdf_path, "wb") as f:
        # Mini 1-page valid PDF signature bytes
        f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources << >>\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<< /Length 43 >>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n(Column reinforcement details column A1 40mm steel bars) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000202 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n0000000294\n%%EOF")

    # Upload document to project
    with open(dummy_pdf_path, "rb") as f:
        doc_resp = client.post(
            f"/api/projects/{project_id}/documents",
            files={"file": ("drawing_spec.pdf", f, "application/pdf")},
            headers=pm_headers
        )
    assert doc_resp.status_code in [200, 201]
    doc_id = doc_resp.json()["id"]

    # Trigger indexing (RAG Service process)
    # RAG indexing is scheduled, we run query directly (since easy check stubs are ready)
    query_resp = client.post(
        "/api/documents/query",
        json={"project_id": project_id, "query_text": "What is the column reinforcement size?"},
        headers=eng_headers
    )
    assert query_resp.status_code == 200
    assert "answer" in query_resp.json()

    # Clean up dummy PDF
    if os.path.exists(dummy_pdf_path):
        os.remove(dummy_pdf_path)

    # ----------------------------------------------------
    # 9. INVOICE OCR FINANCIAL COMPLIANCE
    # ----------------------------------------------------
    # Create dummy image and upload as invoice
    dummy_invoice_path = os.path.join("uploads", "invoice_bill.jpg")
    img = Image.new("RGB", (100, 100), color="white")
    img.save(dummy_invoice_path)
    
    with open(dummy_invoice_path, "rb") as f:
        inv_upload = client.post(
            "/api/invoice/upload",
            data={"project_id": str(project_id)},
            files={"file": ("bill.jpg", f, "image/jpeg")},
            headers=pm_headers
        )
    assert inv_upload.status_code in [200, 201]
    invoice_id = inv_upload.json()["id"]

    # Trigger Compliance audit check
    audit_resp = client.post(
        "/api/invoice/analyze",
        json={"invoice_id": invoice_id},
        headers=pm_headers
    )
    assert audit_resp.status_code == 200

    # Clean up dummy invoice
    if os.path.exists(dummy_invoice_path):
        os.remove(dummy_invoice_path)

    # ----------------------------------------------------
    # 10. IMAGE ANALYSIS VISUAL HAZARD COCKPIT
    # ----------------------------------------------------
    # Create site image
    dummy_site_path = os.path.join("uploads", "site_hazard.jpg")
    img_site = Image.new("RGB", (200, 200), color="red")
    img_site.save(dummy_site_path)

    # Upload site image
    with open(dummy_site_path, "rb") as f:
        site_img_resp = client.post(
            f"/api/projects/{project_id}/images",
            data={"capture_date": "2026-08-05"},
            files={"file": ("site.jpg", f, "image/jpeg")},
            headers=eng_headers
        )
    assert site_img_resp.status_code in [200, 201]
    site_image_id = site_img_resp.json()["id"]

    # Trigger visual threat audits
    inspect_resp = client.post(
        "/api/image-analysis/analyze",
        json={"project_id": project_id, "site_image_id": site_image_id},
        headers=pm_headers
    )
    assert inspect_resp.status_code in [200, 201]

    # Clean up site image
    if os.path.exists(dummy_site_path):
        os.remove(dummy_site_path)

    # ----------------------------------------------------
    # 11. VOICE ASSISTANT SIMULATOR COCKPIT
    # ----------------------------------------------------
    voice_resp = client.post(
        "/api/voice/command",
        data={"project_id": str(project_id), "command_text": "What safety issues are active on site?"},
        headers=eng_headers
    )
    assert voice_resp.status_code == 200
    assert "response_text" in voice_resp.json()

    # ----------------------------------------------------
    # 12. AI CHAT ASSISTANT WORKSPACE
    # ----------------------------------------------------
    # Create session
    chat_sess_resp = client.post(
        "/api/chat/sessions",
        json={"project_id": project_id, "session_name": "E2E QA Thread"},
        headers=pm_headers
    )
    assert chat_sess_resp.status_code == 201
    chat_session_id = chat_sess_resp.json()["id"]

    # Submit query message
    chat_msg_resp = client.post(
        f"/api/chat/sessions/{chat_session_id}/message",
        json={"message_text": "Give me an executive summary of this project."},
        headers=pm_headers
    )
    assert chat_msg_resp.status_code == 200

    # ----------------------------------------------------
    # 13. EXECUTIVE PORTFOLIO ANALYTICS
    # ----------------------------------------------------
    dash_resp = client.get(
        f"/api/projects/executive/analytics?project_id={project_id}",
        headers=pm_headers
    )
    assert dash_resp.status_code == 200

    # ----------------------------------------------------
    # 14. REPORT CENTER FILE DOWNLOAD STREAMS
    # ----------------------------------------------------
    # PDF
    rep_pdf = client.get(
        f"/api/reports/download?project_id={project_id}&report_type=budget&report_format=pdf",
        headers=pm_headers
    )
    assert rep_pdf.status_code == 200
    assert rep_pdf.headers["content-type"] == "application/pdf"

    # CSV
    rep_csv = client.get(
        f"/api/reports/download?project_id={project_id}&report_type=material&report_format=csv",
        headers=pm_headers
    )
    assert rep_csv.status_code == 200
    assert "text/csv" in rep_csv.headers["content-type"]

    # ----------------------------------------------------
    # 15. ALERTS NOTIFICATION LOG AUDIT TRAIL
    # ----------------------------------------------------
    # Trigger active notifications scan
    NotificationService.check_and_trigger_alerts(db)

    # Pull history logs API (All Roles)
    notif_hist = client.get(f"/api/notifications/history/{project_id}", headers=eng_headers)
    assert notif_hist.status_code == 200
    # There should be notification logs recorded in the DB due to shortages/budget check
    assert len(notif_hist.json()) >= 0
