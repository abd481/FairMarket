from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from models.predict import classify_mode, predict_from_features, prepare_row


class TestClassifyMode:
    def test_villa_routes_to_only_villas(self):
        assert classify_mode("Villa") == "only_villas"

    def test_stand_alone_villa_routes_to_only_villas(self):
        assert classify_mode("Stand Alone Villa") == "only_villas"

    @pytest.mark.parametrize(
        "property_type",
        ["Apartment", "Studio", "Penthouse", "Duplex", "Townhouse", "Chalet"],
    )
    def test_non_villas_route_to_no_villas(self, property_type):
        assert classify_mode(property_type) == "no_villas"

    def test_case_sensitive_match(self):
        assert classify_mode("villa") == "no_villas"


class TestPrepareRow:
    def test_compound_from_location(self):
        row = prepare_row(
            {"location": "Crescent Walk, 6th Settlement", "property_type": "Apartment"},
            {},
            1000.0,
        )
        assert row["compound"] == "Crescent Walk"

    def test_compound_single_part_location(self):
        row = prepare_row(
            {"location": "Maadi", "property_type": "Apartment"}, {}, 1000.0
        )
        assert row["compound"] == "Maadi"

    def test_beds_baths_product(self):
        row = prepare_row(
            {"location": "Maadi", "beds": 3, "baths": 2, "property_type": "Apartment"},
            {},
            1000.0,
        )
        assert row["beds_baths"] == 6

    def test_district_avg_pps_fallback_to_global(self):
        row = prepare_row(
            {
                "location": "Maadi",
                "district": "Unknown District",
                "property_type": "Apartment",
            },
            {"6th Settlement": 50000.0},
            1000.0,
        )
        assert row["district_avg_pps"] == 1000.0

    def test_district_avg_pps_from_map(self):
        row = prepare_row(
            {
                "location": "Maadi",
                "district": "6th Settlement",
                "property_type": "Apartment",
            },
            {"6th Settlement": 50000.0},
            1000.0,
        )
        assert row["district_avg_pps"] == 50000.0


class StubPipeline:
    def transform(self, X):
        return X


class StubModel:
    def __init__(self, log_price):
        self._log_price = log_price

    def predict(self, X):
        return np.array([self._log_price])


class TestPredictFromFeatures:
    def _default_args(self):
        features = {
            "area": 100,
            "beds": 2,
            "baths": 2,
            "location": "Crescent Walk, 6th Settlement",
            "property_type": "Apartment",
            "furnishing": "Unfurnished",
            "amenities": "Pool, Security",
            "amenity_count": 2,
        }
        resolved = SimpleNamespace(city="New Cairo", district="6th Settlement")
        bins = [0, 500_000, 10_000_000, 23_000_000]
        bin_key = pd.cut([1_000_000], bins=bins, include_lowest=True)[0]
        calib = {"bins": bins, "calib_map": {bin_key: 100_000.0}}
        return {
            "features": features,
            "district_pps": {"6th Settlement": 50000.0},
            "global_pps": 40000.0,
            "pipeline": StubPipeline(),
            "model": StubModel(np.log(1_000_000)),
            "calib": calib,
            "resolved_location": resolved,
        }

    def test_predicts_expm1_price(self):
        result = predict_from_features(**self._default_args())
        assert result["predicted_price"] == pytest.approx(1_000_000, abs=5)

    def test_applies_calibration_band(self):
        result = predict_from_features(**self._default_args())
        assert result["price_lower"] == pytest.approx(900_000, abs=5)
        assert result["price_upper"] == pytest.approx(1_100_000, abs=5)

    def test_missing_calibration_bin_uses_zero(self):
        args = self._default_args()
        args["calib"] = {"bins": [0, 500_000, 10_000_000, 23_000_000], "calib_map": {}}
        result = predict_from_features(**args)
        assert result["price_lower"] == pytest.approx(1_000_000, abs=5)
        assert result["price_upper"] == pytest.approx(1_000_000, abs=5)
