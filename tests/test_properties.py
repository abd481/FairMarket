import pytest
import pandas as pd
from fastapi.testclient import TestClient

import api.main as main
import api.services.properties as properties_service
from api.schemas import PropertyDetail
from api.services.location import build_location_cache

KNOWN_LOCATIONS = ["Crescent Walk, 6th Settlement", "Sukoon, New Zayed"]

ROW = {
    "id": 123,
    "title": "Luxury 3BR in Crescent Walk",
    "price": 5_500_000.0,
    "area": 160.0,
    "beds": 3,
    "baths": 2,
    "location": "Crescent Walk, 6th Settlement",
    "district": "6th Settlement",
    "city": "New Cairo",
    "compound": "Crescent Walk",
    "property_type": "Apartment",
    "furnishing": "Furnished",
    "amenities": "Pool, Security, Balcony",
    "price_per_sqm": 34_375.0,
    "source": "bayut",
    "link": "https://bayut.example.com/listing/123",
}


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


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "_load_all", fake_load_all)
    with TestClient(main.app) as c:
        yield c


class FakeConn:
    def __init__(self, row):
        self.row = row
        self.captured_stmt = None
        self.captured_params = None

    def execute(self, stmt, params=None):
        self.captured_stmt = stmt
        self.captured_params = params
        return self

    def mappings(self):
        return self

    def first(self):
        return dict(self.row) if self.row is not None else None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.fixture
def fake_engine(monkeypatch):
    conn = FakeConn(ROW)
    monkeypatch.setattr(
        properties_service,
        "get_pg_engine",
        lambda: type("Engine", (), {"connect": lambda self: conn})(),
    )
    return conn


class TestGetProperty:
    def test_maps_row_to_safe_response_shape(self, fake_engine):
        prop = properties_service.get_property(123)
        assert isinstance(prop, PropertyDetail)
        assert prop.id == 123
        assert prop.title == "Luxury 3BR in Crescent Walk"
        assert prop.price == 5_500_000.0
        assert prop.area == 160.0
        assert prop.beds == 3
        assert prop.baths == 2
        assert prop.location == "Crescent Walk, 6th Settlement"
        assert prop.district == "6th Settlement"
        assert prop.city == "New Cairo"
        assert prop.compound == "Crescent Walk"
        assert prop.property_type == "Apartment"
        assert prop.furnishing == "Furnished"
        assert prop.amenities == ["Pool", "Security", "Balcony"]
        assert prop.price_per_sqm == pytest.approx(34_375.0)
        assert prop.source == "bayut"
        assert prop.link == "https://bayut.example.com/listing/123"

    def test_query_is_parameterized(self, fake_engine):
        properties_service.get_property(123)
        stmt_text = str(fake_engine.captured_stmt)
        assert ":property_id" in stmt_text
        assert "123" not in stmt_text.replace(":property_id", "")
        assert fake_engine.captured_params == {"property_id": 123}

    def test_missing_row_returns_none(self, monkeypatch):
        conn = FakeConn(None)
        monkeypatch.setattr(
            properties_service,
            "get_pg_engine",
            lambda: type("Engine", (), {"connect": lambda self: conn})(),
        )
        assert properties_service.get_property(999) is None

    def test_computes_price_per_sqm_when_absent(self, monkeypatch):
        row = dict(ROW, price_per_sqm=None)
        conn = FakeConn(row)
        monkeypatch.setattr(
            properties_service,
            "get_pg_engine",
            lambda: type("Engine", (), {"connect": lambda self: conn})(),
        )
        prop = properties_service.get_property(123)
        assert prop.price_per_sqm == pytest.approx(5_500_000.0 / 160.0)

    def test_parses_not_mentioned_amenities_as_empty(self, monkeypatch):
        row = dict(ROW, amenities="Not Mentioned")
        conn = FakeConn(row)
        monkeypatch.setattr(
            properties_service,
            "get_pg_engine",
            lambda: type("Engine", (), {"connect": lambda self: conn})(),
        )
        prop = properties_service.get_property(123)
        assert prop.amenities == []

    def test_parses_not_specified_furnishing_as_none(self, monkeypatch):
        row = dict(ROW, furnishing="Not Specified")
        conn = FakeConn(row)
        monkeypatch.setattr(
            properties_service,
            "get_pg_engine",
            lambda: type("Engine", (), {"connect": lambda self: conn})(),
        )
        prop = properties_service.get_property(123)
        assert prop.furnishing is None


class TestPropertyEndpoint:
    def test_existing_property_returns_safe_shape(self, client, monkeypatch):
        monkeypatch.setattr(
            main,
            "get_property",
            lambda pid: properties_service.get_property(pid) or PropertyDetail(),
        )
        # Avoid DB by pointing the service at a fake engine with ROW.
        fake_engine_row = dict(ROW)
        conn = FakeConn(fake_engine_row)
        monkeypatch.setattr(
            properties_service,
            "get_pg_engine",
            lambda: type("Engine", (), {"connect": lambda self: conn})(),
        )
        resp = client.get("/api/properties/123")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == 123
        assert body["title"] == "Luxury 3BR in Crescent Walk"
        assert body["price"] == 5_500_000.0
        assert body["property_type"] == "Apartment"
        assert body["amenities"] == ["Pool", "Security", "Balcony"]
        # No internal columns leaked.
        for internal in (
            "checksum",
            "scraped_at",
            "transformed_at",
            "reactivated_date",
            "is_studio",
            "amenity_count",
            "transaction_type",
        ):
            assert internal not in body

    def test_missing_property_returns_404(self, client, monkeypatch):
        monkeypatch.setattr(main, "get_property", lambda pid: None)
        resp = client.get("/api/properties/999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    def test_non_positive_id_returns_422(self, client):
        for bad in ("0", "-1"):
            resp = client.get(f"/api/properties/{bad}")
            assert resp.status_code == 422

    def test_non_integer_id_returns_422(self, client):
        resp = client.get("/api/properties/not-a-number")
        assert resp.status_code == 422
