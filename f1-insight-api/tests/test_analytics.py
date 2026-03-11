"""Priority 3 — Analytics integration tests: career-stats, leaderboard, pit-stop analysis."""


class TestCareerStats:
    def test_career_stats_success(self, client, seed_data):
        resp = client.get("/api/v1/analytics/drivers/1/career-stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["driver"]["name"] == "Lewis Hamilton"
        career = data["career"]
        assert career["total_races"] == 3
        assert career["wins"] == 1
        assert career["podiums"] == 3
        assert career["total_points"] == 58.0  # 25 + 18 + 15
        assert career["win_rate"] > 0
        assert "teams" in data
        assert "seasons" in data

    def test_career_stats_driver_not_found(self, client):
        resp = client.get("/api/v1/analytics/drivers/9999/career-stats")
        assert resp.status_code == 404

    def test_career_stats_no_results(self, client, db_session):
        from app.models import Driver
        driver = Driver(driver_id=50, driver_ref="nodata", forename="No", surname="Data")
        db_session.add(driver)
        db_session.commit()
        resp = client.get("/api/v1/analytics/drivers/50/career-stats")
        assert resp.status_code == 404
        assert "No race data" in resp.json()["detail"]


class TestLeaderboard:
    def test_leaderboard_by_points(self, client, seed_data):
        resp = client.get("/api/v1/analytics/leaderboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["metric"] == "points"
        lb = data["leaderboard"]
        assert len(lb) >= 2
        # Verstappen has most points (18+25+25=68), Hamilton (25+18+15=58)
        assert lb[0]["driver"] == "Max Verstappen"
        assert lb[0]["total_points"] == 68.0
        assert lb[1]["driver"] == "Lewis Hamilton"

    def test_leaderboard_by_wins(self, client, seed_data):
        resp = client.get("/api/v1/analytics/leaderboard?metric=wins")
        assert resp.status_code == 200
        lb = resp.json()["leaderboard"]
        assert lb[0]["wins"] >= lb[1]["wins"]

    def test_leaderboard_with_season_filter(self, client, seed_data):
        resp = client.get("/api/v1/analytics/leaderboard?season=2023")
        assert resp.status_code == 200
        data = resp.json()
        assert data["season"] == 2023


class TestPitStopAnalysis:
    def test_pit_stop_analysis_success(self, client, seed_data):
        resp = client.get("/api/v1/analytics/races/1/pit-stop-analysis")
        assert resp.status_code == 200
        data = resp.json()
        assert data["race"] == "Italian Grand Prix"
        assert "strategy_summary" in data
        assert "driver_details" in data
        assert len(data["driver_details"]) >= 2

    def test_pit_stop_analysis_race_not_found(self, client):
        resp = client.get("/api/v1/analytics/races/9999/pit-stop-analysis")
        assert resp.status_code == 404


class TestCircuitHistory:
    def test_circuit_history_success(self, client, seed_data):
        resp = client.get("/api/v1/analytics/circuits/1/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["circuit"]["name"] == "Monza"
        assert data["statistics"]["total_races"] >= 2
        assert len(data["most_successful_drivers"]) >= 1

    def test_circuit_history_not_found(self, client):
        resp = client.get("/api/v1/analytics/circuits/9999/history")
        assert resp.status_code == 404
