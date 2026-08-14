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


@pytest.fixture(autouse=True)
def reset_limiter():
    main.limiter.reset()
    yield
    main.limiter.reset()


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


class TestRateLimit:
    def test_health_allows_first_request(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_cheap_get_limit_exceeded_returns_429(self, client):
        ok = 0
        for _ in range(121):
            resp = client.get("/health")
            if resp.status_code == 200:
                ok += 1
                continue
            assert resp.status_code == 429
            assert "Rate limit exceeded" in resp.json()["error"]
            break
        else:
            raise AssertionError("rate limit never triggered for /health")
        assert ok >= 1

    def test_predict_limit_exceeded_returns_429(
        self, client, predict_payload, monkeypatch
    ):
        monkeypatch.setattr(main, "predict", fake_predict)
        ok = 0
        for _ in range(21):
            resp = client.post("/api/predict", json=predict_payload)
            if resp.status_code == 200:
                ok += 1
                continue
            assert resp.status_code == 429
            break
        else:
            raise AssertionError("rate limit never triggered for /api/predict")
        assert ok >= 1

    def test_recommend_limit_exceeded_returns_429(
        self, client, predict_payload, monkeypatch
    ):
        monkeypatch.setattr(main, "recommend", fake_recommend)
        payload = dict(predict_payload, price_min=500_000, price_max=2_000_000, k=5)
        ok = 0
        for _ in range(21):
            resp = client.post("/api/recommend", json=payload)
            if resp.status_code == 200:
                ok += 1
                continue
            assert resp.status_code == 429
            break
        else:
            raise AssertionError("rate limit never triggered for /api/recommend")
        assert ok >= 1
