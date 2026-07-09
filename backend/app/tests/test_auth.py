def test_register_user(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "role": "Site Engineer"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "Site Engineer"
    assert "id" in data

def test_register_user_duplicate(client):
    # First registration
    client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "Duplicate User",
            "role": "Site Engineer"
        }
    )
    # Second registration with same email
    response = client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "anotherpassword",
            "full_name": "Another Name",
            "role": "Project Manager"
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_user(client):
    # Register
    client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "loginpassword",
            "full_name": "Login User",
            "role": "Admin"
        }
    )
    # Login via OAuth2 Form data
    response = client.post(
        "/api/auth/login",
        data={
            "username": "login@example.com",
            "password": "loginpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "Admin"
    assert data["user_name"] == "Login User"

def test_login_user_incorrect_credentials(client):
    response = client.post(
        "/api/auth/login",
        data={
            "username": "wrong@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]

def test_forgot_and_reset_password(client):
    # Register
    client.post(
        "/api/auth/register",
        json={
            "email": "reset@example.com",
            "password": "oldpassword",
            "full_name": "Reset User",
            "role": "Project Manager"
        }
    )
    # Forgot password
    forgot_resp = client.post(
        "/api/auth/forgot-password",
        json={"email": "reset@example.com"}
    )
    assert forgot_resp.status_code == 200
    forgot_data = forgot_resp.json()
    assert "dev_token" in forgot_data
    token = forgot_data["dev_token"]
    
    # Reset password
    reset_resp = client.post(
        "/api/auth/reset-password",
        json={
            "token": token,
            "new_password": "newpassword123"
        }
    )
    assert reset_resp.status_code == 200
    assert "reset successfully" in reset_resp.json()["message"]
    
    # Verify login works with new password
    login_resp = client.post(
        "/api/auth/login",
        data={
            "username": "reset@example.com",
            "password": "newpassword123"
        }
    )
    assert login_resp.status_code == 200

def test_read_user_me(client):
    # Register
    client.post(
        "/api/auth/register",
        json={
            "email": "me@example.com",
            "password": "mypassword",
            "full_name": "Me User",
            "role": "Site Engineer"
        }
    )
    # Login
    login_resp = client.post(
        "/api/auth/login",
        data={
            "username": "me@example.com",
            "password": "mypassword"
        }
    )
    token = login_resp.json()["access_token"]
    
    # Get current user details
    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "me@example.com"
    assert me_data["full_name"] == "Me User"
    assert me_data["role"] == "Site Engineer"
