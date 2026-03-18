"""Priority 2 — Circuits CRUD: key defensive paths."""
from app.models import Circuit


class TestCreateCircuit:
    def test_create_success(self, client, auth_headers):
        resp = client.post("/api/v1/circuits/", headers=auth_headers, json={
            "circuit_ref": "spa",
            "name": "Spa-Francorchamps",
            "location": "Stavelot",
            "country": "Belgium",
            "lat": 50.4,
            "lng": 5.97,
            "alt": 401,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["circuit_ref"] == "spa"
        assert "circuit_id" in data

    def test_create_duplicate_ref(self, client, auth_headers, seed_data):
        resp = client.post("/api/v1/circuits/", headers=auth_headers, json={
            "circuit_ref": "monza",
            "name": "Autodromo Nazionale Monza",
        })
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    def test_create_without_auth(self, client):
        resp = client.post("/api/v1/circuits/", json={
            "circuit_ref": "new", "name": "New Circuit",
        })
        assert resp.status_code == 401


class TestGetCircuits:
    def test_list(self, client, seed_data):
        resp = client.get("/api/v1/circuits/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert "total_races" in data[0]

    def test_get_single(self, client, seed_data):
        resp = client.get("/api/v1/circuits/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Monza"
        assert "total_races_held" in data
        assert "recent_races" in data

    def test_get_not_found(self, client):
        resp = client.get("/api/v1/circuits/9999")
        assert resp.status_code == 404

    def test_filter_by_country(self, client, seed_data):
        resp = client.get("/api/v1/circuits/?country=Italy")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["country"] == "Italy"


class TestUpdateCircuit:
    def test_update_success(self, client, auth_headers, seed_data):
        resp = client.put("/api/v1/circuits/1", headers=auth_headers, json={
            "name": "Autodromo Nazionale Monza",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Autodromo Nazionale Monza"

    def test_update_empty_body(self, client, auth_headers, seed_data):
        resp = client.put("/api/v1/circuits/1", headers=auth_headers, json={})
        assert resp.status_code == 400

    def test_update_not_found(self, client, auth_headers):
        resp = client.put("/api/v1/circuits/9999", headers=auth_headers, json={
            "name": "Ghost",
        })
        assert resp.status_code == 404


class TestDeleteCircuit:
    def test_delete_success(self, client, admin_headers, db_session):
        circuit = Circuit(
            circuit_id=100, circuit_ref="temp", name="Temp Circuit",
            country="Nowhere",
        )
        db_session.add(circuit)
        db_session.commit()

        resp = client.delete("/api/v1/circuits/100", headers=admin_headers)
        assert resp.status_code == 204

    def test_delete_with_races(self, client, admin_headers, seed_data):
        resp = client.delete("/api/v1/circuits/1", headers=admin_headers)
        assert resp.status_code == 409
        assert "races are associated" in resp.json()["detail"]

    def test_delete_non_admin(self, client, auth_headers, seed_data):
        resp = client.delete("/api/v1/circuits/1", headers=auth_headers)
        assert resp.status_code == 403
