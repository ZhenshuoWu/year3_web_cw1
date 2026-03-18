"""Priority 1 — Drivers CRUD: full lifecycle, filters, permissions, error paths."""
from app.models import Driver, Result, Status, Season, Circuit, Race


class TestGetDrivers:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/drivers/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_drivers(self, client, seed_data):
        resp = client.get("/api/v1/drivers/")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_pagination(self, client, seed_data):
        resp = client.get("/api/v1/drivers/?per_page=1&page=1")
        assert len(resp.json()) == 1

    def test_filter_by_nationality(self, client, seed_data):
        resp = client.get("/api/v1/drivers/?nationality=British")
        data = resp.json()
        assert all(d["nationality"] == "British" for d in data)
        assert len(data) == 2  # Hamilton + Norris

    def test_search_by_surname(self, client, seed_data):
        resp = client.get("/api/v1/drivers/?search=Hamilton")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["surname"] == "Hamilton"

    def test_sort_newest(self, client, seed_data):
        resp = client.get("/api/v1/drivers/?sort_by=newest")
        ids = [d["driver_id"] for d in resp.json()]
        assert ids == sorted(ids, reverse=True)

    def test_sort_oldest(self, client, seed_data):
        resp = client.get("/api/v1/drivers/?sort_by=oldest")
        ids = [d["driver_id"] for d in resp.json()]
        assert ids == sorted(ids)


class TestGetSingleDriver:
    def test_found(self, client, seed_data):
        resp = client.get("/api/v1/drivers/1")
        assert resp.status_code == 200
        assert resp.json()["surname"] == "Hamilton"

    def test_not_found(self, client):
        resp = client.get("/api/v1/drivers/9999")
        assert resp.status_code == 404


class TestCreateDriver:
    def test_create_success(self, client, auth_headers):
        resp = client.post("/api/v1/drivers/", headers=auth_headers, json={
            "driver_ref": "leclerc",
            "forename": "Charles",
            "surname": "Leclerc",
            "number": 16,
            "code": "LEC",
            "nationality": "Monegasque",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["driver_ref"] == "leclerc"
        assert data["forename"] == "Charles"
        assert "driver_id" in data

    def test_create_duplicate_ref(self, client, auth_headers, seed_data):
        resp = client.post("/api/v1/drivers/", headers=auth_headers, json={
            "driver_ref": "hamilton",
            "forename": "Lewis",
            "surname": "Hamilton",
        })
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    def test_create_without_auth(self, client):
        resp = client.post("/api/v1/drivers/", json={
            "driver_ref": "new", "forename": "A", "surname": "B",
        })
        assert resp.status_code == 401


class TestUpdateDriver:
    def test_update_success(self, client, auth_headers, seed_data):
        resp = client.put("/api/v1/drivers/1", headers=auth_headers, json={
            "nationality": "English",
        })
        assert resp.status_code == 200
        assert resp.json()["nationality"] == "English"

    def test_update_not_found(self, client, auth_headers):
        resp = client.put("/api/v1/drivers/9999", headers=auth_headers, json={
            "nationality": "Martian",
        })
        assert resp.status_code == 404

    def test_update_empty_body(self, client, auth_headers, seed_data):
        resp = client.put("/api/v1/drivers/1", headers=auth_headers, json={})
        assert resp.status_code == 400
        assert "No fields to update" in resp.json()["detail"]

    def test_update_without_auth(self, client, seed_data):
        resp = client.put("/api/v1/drivers/1", json={"nationality": "X"})
        assert resp.status_code == 401


class TestDeleteDriver:
    def test_delete_success(self, client, admin_headers, db_session):
        # Driver with no results
        driver = Driver(driver_id=100, driver_ref="lonely", forename="Solo", surname="Driver")
        db_session.add(driver)
        db_session.commit()

        resp = client.delete("/api/v1/drivers/100", headers=admin_headers)
        assert resp.status_code == 204

    def test_delete_not_found(self, client, admin_headers):
        resp = client.delete("/api/v1/drivers/9999", headers=admin_headers)
        assert resp.status_code == 404

    def test_delete_with_associated_results(self, client, admin_headers, seed_data):
        resp = client.delete("/api/v1/drivers/1", headers=admin_headers)
        assert resp.status_code == 409
        assert "race results are associated" in resp.json()["detail"]

    def test_delete_non_admin(self, client, auth_headers, seed_data):
        resp = client.delete("/api/v1/drivers/1", headers=auth_headers)
        assert resp.status_code == 403
