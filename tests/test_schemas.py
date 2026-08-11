import pytest
from pydantic import ValidationError

from api.schemas import PredictRequest, RecommendRequest


def valid_predict(**overrides):
    payload = {
        "area": 150,
        "beds": 2,
        "baths": 2,
        "location": "Crescent Walk, 6th Settlement",
        "property_type": "Apartment",
        "furnishing": "Unfurnished",
        "amenities": ["Pool", "Security"],
    }
    payload.update(overrides)
    return payload


class TestPredictRequest:
    def test_valid_payload(self):
        req = PredictRequest(**valid_predict())
        assert req.area == 150
        assert req.amenities == ["Pool", "Security"]

    def test_amenities_default_to_empty(self):
        payload = valid_predict()
        del payload["amenities"]
        req = PredictRequest(**payload)
        assert req.amenities == []

    def test_area_must_be_positive(self):
        with pytest.raises(ValidationError):
            PredictRequest(**valid_predict(area=0))
        with pytest.raises(ValidationError):
            PredictRequest(**valid_predict(area=-10))

    def test_baths_must_be_positive(self):
        with pytest.raises(ValidationError):
            PredictRequest(**valid_predict(baths=0))

    def test_beds_may_be_zero(self):
        req = PredictRequest(**valid_predict(beds=0))
        assert req.beds == 0

    def test_invalid_property_type(self):
        with pytest.raises(ValidationError):
            PredictRequest(**valid_predict(property_type="Boat"))

    def test_invalid_furnishing(self):
        with pytest.raises(ValidationError):
            PredictRequest(**valid_predict(furnishing="Semi-Furnished"))

    def test_missing_required_field(self):
        payload = valid_predict()
        del payload["baths"]
        with pytest.raises(ValidationError):
            PredictRequest(**payload)


class TestRecommendRequest:
    def test_valid_with_price_range(self):
        req = RecommendRequest(
            **valid_predict(price_min=1_000_000, price_max=5_000_000)
        )
        assert req.price_min == 1_000_000
        assert req.price_max == 5_000_000

    def test_valid_with_single_price(self):
        req = RecommendRequest(**valid_predict(price=3_000_000))
        assert req.price == 3_000_000

    def test_valid_without_price_filter(self):
        req = RecommendRequest(**valid_predict())
        assert req.price is None
        assert req.price_min is None

    def test_defaults(self):
        req = RecommendRequest(**valid_predict())
        assert req.k == 10
        assert req.price_tolerance == 0.3

    def test_price_and_range_conflict(self):
        with pytest.raises(ValidationError):
            RecommendRequest(**valid_predict(price=1_000_000, price_min=500_000))

    def test_price_min_gt_max(self):
        with pytest.raises(ValidationError):
            RecommendRequest(**valid_predict(price_min=5_000_000, price_max=1_000_000))

    def test_k_must_be_positive(self):
        with pytest.raises(ValidationError):
            RecommendRequest(**valid_predict(price=1_000_000, k=0))

    def test_price_must_be_positive(self):
        with pytest.raises(ValidationError):
            RecommendRequest(**valid_predict(price=0))

    def test_price_tolerance_bounds(self):
        with pytest.raises(ValidationError):
            RecommendRequest(**valid_predict(price=1_000_000, price_tolerance=1.5))
