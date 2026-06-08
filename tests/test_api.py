import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_counties():
    resp = client.get("/api/v1/counties/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 47
    assert len(data["counties"]) == 47


def test_get_county_valid():
    resp = client.get("/api/v1/counties/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Mombasa"
    assert data["code"] == 1


def test_get_county_invalid():
    resp = client.get("/api/v1/counties/99")
    assert resp.status_code == 404


def test_get_county_nairobi():
    resp = client.get("/api/v1/counties/47")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Nairobi"


@pytest.mark.parametrize("code,name", [
    (1, "Mombasa"), (17, "Makueni"), (22, "Kiambu"),
    (32, "Nakuru"), (42, "Kisumu"), (47, "Nairobi"),
])
def test_multiple_counties(code, name):
    resp = client.get(f"/api/v1/counties/{code}")
    assert resp.status_code == 200
    assert resp.json()["name"] == name


def test_population_forecast():
    resp = client.get("/api/v1/counties/1/population/forecast")
    assert resp.status_code in (200, 404)


def test_clustering():
    resp = client.get("/api/v1/analytics/clustering")
    assert resp.status_code in (200, 404)


def test_health_anomalies():
    resp = client.get("/api/v1/health/anomalies")
    assert resp.status_code in (200, 404)


def test_education():
    resp = client.get("/api/v1/analytics/education")
    assert resp.status_code in (200, 404)


def test_download_csv():
    resp = client.get("/api/v1/data/download/csv")
    assert resp.status_code in (200, 404)


def test_download_json():
    resp = client.get("/api/v1/data/download/json")
    assert resp.status_code in (200, 404)


def test_download_invalid_format():
    resp = client.get("/api/v1/data/download/xml")
    assert resp.status_code == 400
