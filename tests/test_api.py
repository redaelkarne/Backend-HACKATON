"""
Integration tests for the Michelin Riding API.
Make sure the server is running before executing: docker compose up
Then run: pytest tests/ -v
"""

import httpx
import pytest

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "pytest_rider@michelin-test.com"
TEST_PASSWORD = "TestPass123!"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TestAuth:
    def test_register_conflict(self, client, h):
        """Registering with an existing email returns 409."""
        r = client.post("/auth/register", json={
            "first_name": "Dup",
            "last_name": "User",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        })
        assert r.status_code == 409

    def test_register_weak_password(self, client):
        """Password shorter than 8 chars is rejected."""
        r = client.post("/auth/register", json={
            "first_name": "A",
            "last_name": "B",
            "email": "weak@test.com",
            "password": "abc",
        })
        assert r.status_code == 422

    def test_login_success(self, client):
        r = client.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body["data"]
        assert body["data"]["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        r = client.post("/auth/login", json={"email": TEST_EMAIL, "password": "wrongpass"})
        assert r.status_code == 401

    def test_login_unknown_email(self, client):
        r = client.post("/auth/login", json={"email": "nobody@test.com", "password": "anything"})
        assert r.status_code == 401

    def test_me_authenticated(self, client, h, user_id):
        r = client.get("/auth/me", headers=h)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["id"] == user_id
        assert data["email"] == TEST_EMAIL

    def test_me_unauthenticated(self, client):
        r = client.get("/auth/me")
        assert r.status_code in (401, 403)

    def test_me_invalid_token(self, client):
        r = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class TestProfile:
    def test_get_profile(self, client, h, user_id):
        r = client.get(f"/profiles/{user_id}", headers=h)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["user_id"] == user_id
        assert "stats" in data

    def test_get_profile_not_found(self, client, h):
        r = client.get("/profiles/usr_nonexistent", headers=h)
        assert r.status_code == 404

    def test_update_profile(self, client, h, user_id):
        r = client.patch(f"/profiles/{user_id}", headers=h, json={
            "bio": "Passionné de longues sorties route.",
            "rider_type": "route",
            "preferences": {
                "terrains": ["route"],
                "priorities": ["performance"],
                "weather_preferences": ["dry"],
            },
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["bio"] == "Passionné de longues sorties route."
        assert data["rider_type"] == "route"

    def test_add_bike(self, client, h, user_id, bike_id):
        """bike_id fixture already added a bike; verify it has the right shape."""
        r = client.get(f"/profiles/{user_id}", headers=h)
        assert r.status_code == 200
        # bike was created by fixture — just confirm profile is healthy
        assert r.json()["data"]["user_id"] == user_id

    def test_add_mounted_tyre(self, client, h, user_id, mounted_tyre_id):
        """mounted_tyre_id fixture created the tyre; check the ID format."""
        assert mounted_tyre_id.startswith("mty_")


# ---------------------------------------------------------------------------
# Activities
# ---------------------------------------------------------------------------

class TestActivities:
    def test_create_activity(self, client, h, activity_id):
        assert activity_id.startswith("act_")

    def test_list_activities(self, client, h, user_id):
        r = client.get("/activities", headers=h, params={"user_id": user_id})
        assert r.status_code == 200
        body = r.json()
        assert "items" in body["data"]
        assert body["meta"]["total"] >= 1

    def test_list_activities_with_limit(self, client, h):
        r = client.get("/activities", headers=h, params={"limit": 1})
        assert r.status_code == 200
        assert len(r.json()["data"]["items"]) <= 1

    def test_get_activity(self, client, h, activity_id):
        r = client.get(f"/activities/{activity_id}", headers=h)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["id"] == activity_id

    def test_get_activity_not_found(self, client, h):
        r = client.get("/activities/act_notexist", headers=h)
        assert r.status_code == 404

    def test_update_activity(self, client, h, activity_id):
        r = client.patch(f"/activities/{activity_id}", headers=h, json={
            "notes": "Updated notes after the ride.",
            "weather": "wet",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["notes"] == "Updated notes after the ride."
        assert data["weather"] == "wet"

    def test_complete_activity(self, client, h, completed_activity_id):
        r = client.get(f"/activities/{completed_activity_id}", headers=h)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["status"] == "completed"
        assert data["distance_km"] == 42.3
        assert data["duration_seconds"] == 5640
        assert data["elevation_m"] == 312
        assert data["average_speed_kmh"] == 26.8
        assert data["completed_at"] is not None


# ---------------------------------------------------------------------------
# Community
# ---------------------------------------------------------------------------

class TestCommunity:
    def test_get_feed(self, client, h, completed_activity_id):
        r = client.get("/feed", headers=h)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body["data"]
        ids = [item["activity_id"] for item in body["data"]["items"]]
        assert completed_activity_id in ids

    def test_feed_item_shape(self, client, h, completed_activity_id):
        r = client.get("/feed", headers=h)
        items = r.json()["data"]["items"]
        item = next(i for i in items if i["activity_id"] == completed_activity_id)
        assert "user" in item
        assert "summary" in item
        assert "likes_count" in item
        assert "comments_count" in item
        assert "verified_michelin_review" in item

    def test_like_activity(self, client, h, completed_activity_id):
        r = client.post(f"/activities/{completed_activity_id}/like", headers=h)
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["activity_id"] == completed_activity_id
        assert data["liked"] is True
        assert data["likes_count"] >= 1

    def test_unlike_activity(self, client, h, completed_activity_id):
        """Second like on same activity should toggle off."""
        r = client.post(f"/activities/{completed_activity_id}/like", headers=h)
        assert r.status_code == 201
        assert r.json()["data"]["liked"] is False

    def test_like_not_found(self, client, h):
        r = client.post("/activities/act_notexist/like", headers=h)
        assert r.status_code == 404

    def test_add_comment(self, client, h, completed_activity_id):
        r = client.post(f"/activities/{completed_activity_id}/comments", headers=h, json={
            "content": "Super sortie, joli rythme !",
        })
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["content"] == "Super sortie, joli rythme !"
        assert data["activity_id"] == completed_activity_id

    def test_comment_not_found(self, client, h):
        r = client.post("/activities/act_notexist/comments", headers=h, json={"content": "hi"})
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

class TestProgress:
    def test_progress_summary(self, client, h, completed_activity_id):
        r = client.get("/progress/summary", headers=h)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["total_km"] >= 42.3
        assert data["total_rides"] >= 1
        assert "weekly_km" in data
        assert "monthly_km" in data
        assert "badges_count" in data

    def test_weekly_progress(self, client, h):
        r = client.get("/progress/weekly", headers=h)
        assert r.status_code == 200
        days = r.json()["data"]["days"]
        assert len(days) == 7
        day_names = {d["day"] for d in days}
        assert day_names == {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}

    def test_tyre_wear(self, client, h, mounted_tyre_id, completed_activity_id):
        r = client.get("/progress/tyre-wear", headers=h)
        assert r.status_code == 200
        items = r.json()["data"]["items"]
        assert len(items) >= 1
        item = items[0]
        assert "wear_percent" in item
        assert item["replacement_status"] in ("ok", "monitor", "replace_soon")


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

class TestRecommendations:
    def test_create_recommendation(self, client, h, recommendation_id):
        assert recommendation_id.startswith("rec_")

    def test_recommendation_shape(self, client, h, recommendation_id):
        r = client.get(f"/recommendations/tyres/{recommendation_id}", headers=h)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["recommendation_id"] == recommendation_id
        assert "primary_tyre" in data
        assert data["primary_tyre"]["brand"] == "Michelin"
        assert isinstance(data["alternatives"], list)

    def test_recommendation_not_found(self, client, h):
        r = client.get("/recommendations/tyres/rec_notexist", headers=h)
        assert r.status_code == 404

    @pytest.mark.parametrize("rider_type,terrain,weather,priority", [
        ("route", "road", "dry", "performance"),
        ("route", "road", "wet", "grip"),
        ("gravel", "mixed", "dry", "performance"),
        ("mtb", "trail", "wet", "grip"),
        ("urban", "city", "dry", "durability"),
    ])
    def test_recommendation_variants(self, client, h, rider_type, terrain, weather, priority):
        r = client.post("/recommendations/tyres", headers=h, json={
            "rider_type": rider_type,
            "terrain": terrain,
            "weather": weather,
            "priority": priority,
            "ride_frequency": "regular",
        })
        assert r.status_code == 201
        assert r.json()["data"]["primary_tyre"]["brand"] == "Michelin"


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------

class TestChallenges:
    def test_list_challenges(self, client, h):
        r = client.get("/challenges", headers=h)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body["data"]
        assert isinstance(body["data"]["items"], list)

    def test_join_nonexistent_challenge(self, client, h):
        r = client.post("/challenges/chl_notexist/join", headers=h)
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"
        assert r.json()["database"] == "connected"
