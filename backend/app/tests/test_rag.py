import pytest
import io
from app.models.user import UserRole
from app.models.document import ConstructionDocument, DrawingChunk
from app.services.rag_service import RAGService
from app.services.embedding_service import EmbeddingService

def get_auth_headers(client, email, password, role="Site Engineer", name="Test User"):
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": name, "role": role}
    )
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_drawing_rag_pipeline(client, db):
    admin_headers = get_auth_headers(client, "rag_admin@example.com", "adminpass", "Admin")
    pm_headers = get_auth_headers(client, "rag_pm@example.com", "pmpass", "Project Manager")
    eng_headers = get_auth_headers(client, "rag_eng@example.com", "engpass", "Site Engineer")

    # 1. Create project
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Signature Towers RAG",
            "client_name": "Signature Group",
            "location": "Gurugram",
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

    # 2. Test RAG drawing upload (Admin/PM)
    # Generate dummy PDF structure bytes
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << >> /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 50 >>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n(OPC 53 Grade Concrete spec) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000120 00000 n\n0000000212 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n310\n%%EOF"
    file_payload = {"file": ("drawing_spec.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    form_payload = {"project_id": str(proj_id)}

    # Site Engineer -> 403 Forbidden
    upload_fail = client.post(
        "/api/documents/upload",
        data=form_payload,
        files=file_payload,
        headers=eng_headers
    )
    assert upload_fail.status_code == 403

    # PM -> 201 Created
    file_payload = {"file": ("drawing_spec.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    upload_ok = client.post(
        "/api/documents/upload",
        data=form_payload,
        files=file_payload,
        headers=pm_headers
    )
    assert upload_ok.status_code == 201
    doc_data = upload_ok.json()
    assert doc_data["status"] == "Pending"
    doc_id = doc_data["id"]

    # 3. Synchronously run processing to bypass background thread for testing
    processed_doc = RAGService.process_document(db, doc_id)
    assert processed_doc.status == "Completed"
    assert processed_doc.total_chunks > 0

    # 4. Fetch details
    detail_resp = client.get(f"/api/documents/{doc_id}", headers=eng_headers)
    assert detail_resp.status_code == 200
    assert len(detail_resp.json()["chunks"]) > 0

    # 5. Semantic Search Q&A
    query_resp = client.post(
        "/api/documents/query",
        json={
            "project_id": proj_id,
            "query_text": "Is concrete specified?",
            "limit": 3
        },
        headers=eng_headers
    )
    assert query_resp.status_code == 200
    data = query_resp.json()
    assert "answer" in data
    assert len(data["sources"]) > 0
    assert "concrete" in data["answer"].lower()
