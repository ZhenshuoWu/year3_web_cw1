"""Priority 1 — Authentication: register, login, token validation, role checks."""


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert data["role"] == "user"
        assert "id" in data

    def test_register_duplicate_username(self, client, test_user):
        resp = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "other@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 400
        assert "Username already registered" in resp.json()["detail"]

    def test_register_duplicate_email(self, client, test_user):
        resp = client.post("/api/v1/auth/register", json={
            "username": "anotheruser",
            "email": "test@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 400
        assert "Email already registered" in resp.json()["detail"]

    def test_register_short_username(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "username": "ab",
            "email": "x@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 422

    def test_register_short_password(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "username": "validname",
            "email": "x@example.com",
            "password": "12345",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client, test_user):
        resp = client.post("/api/v1/auth/login", data={
            "username": "testuser",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        resp = client.post("/api/v1/auth/login", data={
            "username": "testuser",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        assert "Incorrect username or password" in resp.json()["detail"]

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/v1/auth/login", data={
            "username": "ghost",
            "password": "whatever",
        })
        assert resp.status_code == 401


class TestTokenValidation:
    def test_protected_endpoint_without_token(self, client):
        resp = client.post("/api/v1/drivers/", json={
            "driver_ref": "test", "forename": "A", "surname": "B",
        })
        assert resp.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client):
        resp = client.post(
            "/api/v1/drivers/",
            json={"driver_ref": "test", "forename": "A", "surname": "B"},
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    def test_admin_endpoint_with_user_role(self, client, auth_headers, db_session):
        from app.models import Driver
        driver = Driver(
            driver_id=999, driver_ref="temp", forename="Temp", surname="Driver",
        )
        db_session.add(driver)
        db_session.commit()

        resp = client.delete("/api/v1/drivers/999", headers=auth_headers)
        assert resp.status_code == 403
        assert "Admin privileges required" in resp.json()["detail"]
