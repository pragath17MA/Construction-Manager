import os
import io
import pytest
from datetime import date
from PIL import Image
from app.models.project import Project, SiteImage
from app.models.chat import ChatSession, ChatMessage

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

def test_chat_assistant_flow(client, db):
    # 1. Register User and Project
    headers = get_auth_headers(client, "pm_chat@example.com", "pass123", "Project Manager")
    
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Visual Chat Site",
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

    # 2. Create Chat Session
    sess_resp = client.post(
        "/api/chat/sessions",
        json={
            "project_id": project_id,
            "session_name": "Budget Discussion"
        },
        headers=headers
    )
    assert sess_resp.status_code == 201
    session_id = sess_resp.json()["id"]

    # 3. Submit Text Message
    msg_resp = client.post(
        f"/api/chat/sessions/{session_id}/message",
        json={"message_text": "What is the target budget of the project?"},
        headers=headers
    )
    assert msg_resp.status_code == 200
    assert msg_resp.json()["sender"] == "assistant"
    assert "budget" in msg_resp.json()["message_text"].lower() or "cost" in msg_resp.json()["message_text"].lower()

    # 4. List Sessions
    list_resp = client.get("/api/chat/sessions", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) > 0

    # 5. Fetch Session Details
    detail_resp = client.get(f"/api/chat/sessions/{session_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert len(detail_resp.json()["messages"]) >= 2  # user msg + ai response

    # 6. Submit Audio Message (Dummy WAV file)
    dummy_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x40\x1f\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00"
    audio_file = {"audio": ("test.wav", io.BytesIO(dummy_wav), "audio/wav")}
    audio_resp = client.post(
        f"/api/chat/sessions/{session_id}/audio-message",
        files=audio_file,
        headers=headers
    )
    assert audio_resp.status_code == 200
    assert audio_resp.json()["sender"] == "assistant"

    # 7. Submit Image Message (Dummy JPG file)
    img_io = io.BytesIO()
    img = Image.new("RGB", (50, 50), color="blue")
    img.save(img_io, format="JPEG")
    img_io.seek(0)
    image_file = {"image": ("test.jpg", img_io, "image/jpeg")}
    
    img_resp = client.post(
        f"/api/chat/sessions/{session_id}/image-message",
        data={"query_text": "Identify any safety issues"},
        files=image_file,
        headers=headers
    )
    assert img_resp.status_code == 200
    assert img_resp.json()["sender"] == "assistant"

    # 8. Clean up uploaded files if created
    chat_img_dir = os.path.join("uploads", "chat", "images")
    if os.path.exists(chat_img_dir):
        for f in os.listdir(chat_img_dir):
            os.remove(os.path.join(chat_img_dir, f))
