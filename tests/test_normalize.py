import pytest
from data.processing.normalize import normalize_row


class TestNormalizeRow:
    def test_maps_all_keys(self, sample_raw_listing):
        result = normalize_row(sample_raw_listing)
        assert result["price"] == 1500000
        assert result["location"] == "Cairo, New Cairo"
        assert result["title"] == "Nice Apartment"
        assert result["beds"] == 3
        assert result["baths"] == 2
        assert result["area"] == "150 sqm"
        assert result["property_type"] == "Apartment"
        assert result["furnishing"] == "Furnished"
        assert result["amenities"] == '["pool", "gym"]'
        assert result["link"] == "https://example.com/1"

    def test_falls_back_to_lowercase_keys(self):
        row = {
            "price": 500000,
            "location": "Giza",
            "title": "Villa",
            "beds": 4,
            "baths": 3,
            "area": 200,
            "type": "Villa",
            "furnishing": None,
            "amenities": "[]",
            "link": "https://example.com/2",
        }
        result = normalize_row(row)
        assert result["price"] == 500000
        assert result["property_type"] == "Villa"

    def test_missing_furnishing_returns_none(self):
        result = normalize_row({
            "Price": 100000, "Location": "Cairo", "Title": "Test",
            "Beds": 2, "Baths": 1, "Area": 80, "Type": "Apartment",
            "Amenities": "[]", "Link": "url",
        })
        assert result["furnishing"] is None

    def test_missing_reactivated_date_returns_none(self):
        result = normalize_row({
            "Price": 100000, "Location": "Cairo", "Title": "Test",
            "Beds": 2, "Baths": 1, "Area": 80, "Type": "Apartment",
            "Amenities": "[]", "Link": "url",
        })
        assert result["reactivated_date"] is None

    def test_handles_empty_amenities(self):
        result = normalize_row({
            "Price": 100000, "Location": "Cairo", "Title": "Test",
            "Beds": 2, "Baths": 1, "Area": 80, "Type": "Apartment",
            "Furnishing": "No", "Amenities": "", "Link": "url",
        })
        assert result["amenities"] == "[]"

    def test_handles_none_price(self):
        row = {"Price": None, "Location": "Cairo", "Title": "Test",
               "Beds": 2, "Baths": 1, "Area": 80, "Type": "Apartment",
               "Furnishing": None, "Amenities": "[]", "Link": "url"}
        result = normalize_row(row)
        assert result["price"] is None
