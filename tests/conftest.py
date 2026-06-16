import pytest
import httpx

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "pytest_rider@michelin-test.com"
TEST_PASSWORD = "TestPass123!"


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=10) as c:
        yield c


@pytest.fixture(scope="session")
def auth(client):
    r = client.post("/auth/register", json={
        "first_name": "Test",
        "last_name": "Rider",
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    if r.status_code == 409:
        r = client.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert r.status_code in (200, 201), f"Auth setup failed: {r.text}"
    data = r.json()["data"]
    return {"token": data["access_token"], "user_id": data["user"]["id"]}


@pytest.fixture(scope="session")
def h(auth):
    return {"Authorization": f"Bearer {auth['token']}"}


@pytest.fixture(scope="session")
def user_id(auth):
    return auth["user_id"]


@pytest.fixture(scope="session")
def bike_id(client, h, user_id):
    r = client.post(f"/profiles/{user_id}/bike", headers=h, json={
        "brand": "Trek",
        "model": "Emonda SL",
        "category": "route",
        "wheel_size": "700c",
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


@pytest.fixture(scope="session")
def mounted_tyre_id(client, h, user_id, bike_id):
    r = client.post(f"/profiles/{user_id}/mounted-tyres", headers=h, json={
        "bike_id": bike_id,
        "brand": "Michelin",
        "model": "Power Cup 2",
        "size": "700x28",
        "mounted_at": "2026-01-01",
        "estimated_lifespan_km": 4000,
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


@pytest.fixture(scope="session")
def activity_id(client, h, user_id, bike_id):
    r = client.post("/activities", headers=h, json={
        "user_id": user_id,
        "bike_id": bike_id,
        "type": "route",
        "started_at": "2026-06-16T07:00:00Z",
        "weather": "dry",
        "notes": "Test ride",
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


@pytest.fixture(scope="session")
def completed_activity_id(client, h, activity_id):
    r = client.post(f"/activities/{activity_id}/complete", headers=h, json={
        "distance_km": 42.3,
        "duration_seconds": 5640,
        "elevation_m": 312,
        "average_speed_kmh": 26.8,
        "route_polyline": "abc123",
    })
    assert r.status_code == 200, r.text
    return activity_id


@pytest.fixture(scope="session")
def recommendation_id(client, h):
    r = client.post("/recommendations/tyres", headers=h, json={
        "rider_type": "route",
        "terrain": "road",
        "weather": "dry",
        "priority": "performance",
        "ride_frequency": "frequent",
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]["recommendation_id"]
