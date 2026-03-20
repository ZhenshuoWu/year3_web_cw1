"""Priority 2 — Constructors CRUD: key defensive paths."""
from app.models import Constructor


class TestCreateConstructor:
    def test_create_success(self, client, auth_headers):
        resp = client.post("/api/v1/constructors/", headers=auth_headers, json={
            "constructor_ref": "ferrari",
            "name": "Ferrari",
            "nationality": "Italian",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Ferrari"
        assert "constructor_id" in data

    def test_create_duplicate_ref(self, client, auth_headers, seed_data):
        resp = client.post("/api/v1/constructors/", headers=auth_headers, json={
            "constructor_ref": "mercedes",
            "name": "Mercedes AMG",
        })
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    def test_create_without_auth(self, client):
        resp = client.post("/api/v1/constructors/", json={
            "constructor_ref": "new", "name": "New Team",
        })
        assert resp.status_code == 401


class TestGetConstructors:
    def test_list(self, client, seed_data):
        resp = client.get("/api/v1/constructors/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert "total_points" in data[0]
        assert "wins" in data[0]

    def test_get_single_with_career_summary(self, client, seed_data):
        resp = client.get("/api/v1/constructors/2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Red Bull"
        assert "career_summary" in data
        assert data["career_summary"]["wins"] >= 1
        assert "top_drivers" in data

    def test_get_not_found(self, client):
        resp = client.get("/api/v1/constructors/9999")
        assert resp.status_code == 404


class TestUpdateConstructor:
    def test_update_success(self, client, auth_headers, seed_data):
        resp = client.put("/api/v1/constructors/1", headers=auth_headers, json={
            "name": "Mercedes-AMG Petronas",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Mercedes-AMG Petronas"

    def test_update_empty_body(self, client, auth_headers, seed_data):
        resp = client.put("/api/v1/constructors/1", headers=auth_headers, json={})
        assert resp.status_code == 400

    def test_update_not_found(self, client, auth_headers):
        resp = client.put("/api/v1/constructors/9999", headers=auth_headers, json={
            "name": "Ghost",
        })
        assert resp.status_code == 404


class TestDeleteConstructor:
    def test_soft_delete_success(self, client, admin_headers, seed_data):
        """Soft-deleting a constructor with results should succeed."""
        resp = client.delete("/api/v1/constructors/1", headers=admin_headers)
        assert resp.status_code == 204

        # Constructor no longer visible via GET
        resp = client.get("/api/v1/constructors/1")
        assert resp.status_code == 404

        # Constructor no longer visible in list
        resp = client.get("/api/v1/constructors/")
        constructor_ids = [c["constructor_id"] for c in resp.json()]
        assert 1 not in constructor_ids

    def test_delete_already_deleted(self, client, admin_headers, seed_data):
        """Deleting an already soft-deleted constructor returns 404."""
        client.delete("/api/v1/constructors/1", headers=admin_headers)
        resp = client.delete("/api/v1/constructors/1", headers=admin_headers)
        assert resp.status_code == 404

    def test_delete_non_admin(self, client, auth_headers, seed_data):
        resp = client.delete("/api/v1/constructors/1", headers=auth_headers)
        assert resp.status_code == 403
