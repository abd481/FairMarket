import pytest
import pandas as pd
from fastapi.testclient import TestClient

import api.main as main
from api.schemas import FilterBy, PredictResponse, RecommendResponse
from api.services.location import build_location_cache

KNOWN_LOCATIONS = ["Crescent Walk, 6th Settlement", "Sukoon, New Zayed"]


def build_caches():
    df = pd.DataFrame(
        {
            "location": KNOWN_LOCATIONS,
            "district": ["6th Settlement", "New Zayed"],
            "city": ["New Cairo", "New Zayed"],
            "compound": ["Crescent Walk", "Sukoon"],
            "price_per_sqm": [50000, 60000],
        }
    )
    return build_location_cache(df)


def fake_load_all():
    return {"only_villas": object(), "no_villas": object()}, build_caches()


def fake_predict(body, loc, models):
    return PredictResponse(
        predicted_price=1_000_000,
        price_lower=900_000,
        price_upper=1_100_000,
        resolved_location=loc,
    )


def fake_recommend(body, loc, models):
    return RecommendResponse(
        filtered_by=FilterBy.FEATURES_ONLY,
        recommendations=[],
        predicted_fair_price=1_000_000,
        resolved_location=loc,
    )


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "_load_all", fake_load_all)
    with TestClient(main.app) as c:
        yield c


@pytest.fixture
def predict_payload():
    return {
        "area": 150,
        "beds": 2,
        "baths": 2,
        "location": "Crescent Walk, 6th Settlement",
        "property_type": "Apartment",
        "furnishing": "Unfurnished",
        "amenities": ["Pool", "Security"],
    }


class TestHealth:
    def test_ready(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ready"
        assert set(body["models_loaded"]) == {"only_villas", "no_villas"}
        assert body["known_locations"] == len(KNOWN_LOCATIONS)


class TestLocations:
    def test_lists_locations(self, client):
        resp = client.get("/api/locations")
        assert resp.status_code == 200
        assert resp.json() == KNOWN_LOCATIONS


class TestPredictEndpoint:
    def test_valid_request(self, client, predict_payload, monkeypatch):
        monkeypatch.setattr(main, "predict", fake_predict)
        resp = client.post("/api/predict", json=predict_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["predicted_price"] == 1_000_000
        assert body["price_lower"] == 900_000
        assert body["price_upper"] == 1_100_000
        assert body["resolved_location"]["matched"] is True

    def test_unknown_location_returns_400(self, client, predict_payload, monkeypatch):
        monkeypatch.setattr(main, "predict", fake_predict)
        payload = dict(predict_payload, location="Nowhere City")
        resp = client.post("/api/predict", json=payload)
        assert resp.status_code == 400
        assert "not found" in resp.json()["detail"]

    def test_validation_error_returns_422(self, client, predict_payload):
        payload = dict(predict_payload, baths=0)
        resp = client.post("/api/predict", json=payload)
        assert resp.status_code == 422

    def test_missing_field_returns_422(self, client, predict_payload):
        payload = dict(predict_payload)
        del payload["property_type"]
        resp = client.post("/api/predict", json=payload)
        assert resp.status_code == 422

    def test_invalid_enum_returns_422(self, client, predict_payload):
        payload = dict(predict_payload, property_type="Boat")
        resp = client.post("/api/predict", json=payload)
        assert resp.status_code == 422


class TestRecommendEndpoint:
    def test_valid_request(self, client, predict_payload, monkeypatch):
        monkeypatch.setattr(main, "recommend", fake_recommend)
        payload = dict(predict_payload, price_min=500_000, price_max=2_000_000, k=5)
        resp = client.post("/api/recommend", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["filtered_by"] == "features_only"
        assert body["predicted_fair_price"] == 1_000_000
        assert body["recommendations"] == []

    def test_unknown_location_returns_400(self, client, predict_payload, monkeypatch):
        monkeypatch.setattr(main, "recommend", fake_recommend)
        payload = dict(predict_payload, location="Nowhere City")
        resp = client.post("/api/recommend", json=payload)
        assert resp.status_code == 400

    def test_price_and_range_conflict_returns_422(self, client, predict_payload):
        payload = dict(predict_payload, price=1_000_000, price_min=500_000)
        resp = client.post("/api/recommend", json=payload)
        assert resp.status_code == 422
