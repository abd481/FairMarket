from datetime import datetime
import pytest
from data.validation.schema import Property


class TestPropertyPrice:
    def test_strips_currency_and_commas(self):
        p = Property(price="1,500,000 EGP")
        assert p.price == 1500000

    def test_strips_whitespace(self):
        p = Property(price=" 750000 ")
        assert p.price == 750000

    def test_returns_none_on_garbage(self):
        p = Property(price="not_a_number")
        assert p.price is None


class TestPropertyBeds:
    def test_extracts_integer(self):
        p = Property(beds="4 Beds")
        assert p.beds == 4

    def test_handles_plus_suffix(self):
        p = Property(beds="10+")
        assert p.beds == 10

    def test_returns_none_after_coerce_fails(self):
        p = Property(beds=None)
        assert p.beds is None

    def test_keeps_non_integer_as_string(self):
        p = Property(beds="Studio")
        assert p.beds == "Studio"


class TestPropertyBaths:
    def test_extracts_integer(self):
        p = Property(baths="3 Baths")
        assert p.baths == 3

    def test_handles_plus_suffix(self):
        p = Property(baths="5+")
        assert p.baths == 5


class TestPropertyArea:
    def test_strips_unit(self):
        p = Property(area="150 sqm")
        assert p.area == 150.0

    def test_strips_commas(self):
        p = Property(area="1,500")
        assert p.area == 1500.0

    def test_returns_none_on_garbage(self):
        p = Property(area=None)
        assert p.area is None


class TestPropertyFurnishing:
    def test_maps_yes_to_furnished(self):
        p = Property(furnishing="Yes")
        assert p.furnishing == "Furnished"

    def test_maps_no_to_unfurnished(self):
        p = Property(furnishing="No")
        assert p.furnishing == "Unfurnished"

    def test_passes_through_valid_values(self):
        p = Property(furnishing="Semi-Furnished")
        assert p.furnishing == "Semi-Furnished"

    def test_returns_none_for_empty(self):
        p = Property(furnishing="")
        assert p.furnishing is None

    def test_returns_none_for_none(self):
        p = Property(furnishing=None)
        assert p.furnishing is None


class TestPropertyParsing:
    def test_parses_amenities_from_string_list(self):
        p = Property(amenities='["pool", "gym"]')
        assert p.amenities == ["pool", "gym"]

    def test_parses_amenities_from_list(self):
        p = Property(amenities=["pool", "gym"])
        assert p.amenities == ["pool", "gym"]

    def test_returns_none_for_empty_amenities(self):
        p = Property(amenities=None)
        assert p.amenities is None

    def test_parses_date(self):
        p = Property(reactivated_date="12 March 2024")
        assert p.reactivated_date == datetime(2024, 3, 12)

    def test_handles_relative_date(self):
        p = Property(reactivated_date="2 hours ago")
        assert p.reactivated_date is not None

    def test_returns_none_for_empty_date(self):
        p = Property(reactivated_date="")
        assert p.reactivated_date is None


class TestPropertySourceDetection:
    def test_detects_bayut(self):
        p = Property(link="https://www.bayut.com/property/1")
        assert p.source == "bayut"

    def test_detects_dubizzle(self):
        p = Property(link="https://www.dubizzle.com/property/1")
        assert p.source == "dubizzle"

    def test_detects_olx(self):
        p = Property(link="https://www.olx.com/property/1")
        assert p.source == "olx"

    def test_detects_aqarmap(self):
        p = Property(link="https://www.aqarmap.com/property/1")
        assert p.source == "aqarmap"

    def test_defaults_to_unknown(self):
        p = Property(link="https://www.example.com/property/1")
        assert p.source == "unknown"
