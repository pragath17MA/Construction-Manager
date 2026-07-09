import os
import wave
import pytest
from app.models.project import Project
from app.models.voice import VoiceCommandLog

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

def test_voice_assistant_endpoints(client, db):
    # 1. Setup Auth and Project
    headers = get_auth_headers(client, "pm_voice@example.com", "voicepass", "Project Manager")
    
    proj_resp = client.post(
        "/api/projects",
        json={
            "project_name": "Voice Assistant Build Site",
            "client_name": "Development Board",
            "location": "Noida Sector 15",
            "start_date": "2026-08-01",
            "expected_end_date": "2027-08-01",
            "budget": 8000000.00
        },
        headers=headers
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Test Text Command
    text_data = {
        "project_id": str(project_id),
        "command_text": "What is the budget for the project?"
    }
    
    resp = client.post(
        "/api/voice/command",
        data=text_data,
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "budget" in data["command_text"].lower()
    assert data["response_text"] is not None
    assert data["audio_url"] is not None
    
    filename = data["audio_url"].split("/")[-1]
    
    # 3. Test Audio File command upload
    dummy_wav_path = "uploads/voice/incoming/test_cmd_budget.wav"
    os.makedirs(os.path.dirname(dummy_wav_path), exist_ok=True)
    
    # Write a short valid WAV file of silence
    with wave.open(dummy_wav_path, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b'\x00' * 32000) # 1 second of silence
        
    with open(dummy_wav_path, "rb") as f:
        resp_audio = client.post(
            "/api/voice/command",
            data={"project_id": str(project_id)},
            files={"audio": (os.path.basename(dummy_wav_path), f, "audio/wav")},
            headers=headers
        )
    assert resp_audio.status_code == 200
    audio_data = resp_audio.json()
    assert audio_data["command_text"] is not None
    assert audio_data["response_text"] is not None
    assert audio_data["audio_url"] is not None

    # 4. Fetch history ledger
    hist_resp = client.get(
        f"/api/voice/history/{project_id}",
        headers=headers
    )
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) >= 2
    assert history[0]["project_id"] == project_id

    # 5. Playback synthesized WAV audio file
    audio_resp = client.get(
        f"/api/voice/audio/{filename}",
        headers=headers
    )
    assert audio_resp.status_code == 200
    assert len(audio_resp.content) > 0

    # Clean up test files
    if os.path.exists(dummy_wav_path):
        os.remove(dummy_wav_path)
    
    # Remove synthesized audio response files
    resp_audio_path = os.path.join("uploads", "voice", filename)
    if os.path.exists(resp_audio_path):
        os.remove(resp_audio_path)
        
    other_filename = audio_data["audio_url"].split("/")[-1]
    other_audio_path = os.path.join("uploads", "voice", other_filename)
    if os.path.exists(other_audio_path):
        os.remove(other_audio_path)
