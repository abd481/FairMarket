from datetime import datetime, timedelta
import pytest
from data.validation.rules import PropertyRules
from data.validation.schema import Property


def make_property(**overrides):
    defaults = dict(
        price=1000000,
        location="Cairo",
        title="Nice Apartment",
        beds=3,
        baths=2,
        area=150.0,
        property_type="Apartment",
        amenities=["pool"],
        link="https://www.bayut.com/property/1",
        furnishing="Furnished",
        source="bayut",
        scraped_at=datetime.now(),
    )
    defaults.update(overrides)
    return Property(**defaults)


class TestRulesPrice:
    def test_price_greater_than_zero(self):
        prop = make_property(price=0)
        valid, errors = PropertyRules.validate(prop)
        assert not valid
        assert "Price must be greater than 0" in errors

    def test_price_negative(self):
        prop = make_property(price=-100)
        valid, _ = PropertyRules.validate(prop)
        assert not valid

    def test_price_positive_passes(self):
        prop = make_property(price=500000)
        valid, _ = PropertyRules.validate(prop)
        assert valid


class TestRulesArea:
    def test_area_must_be_positive(self):
        prop = make_property(area=0)
        valid, errors = PropertyRules.validate(prop)
        assert not valid
        assert "Area must be greater than 0" in errors


class TestRulesBeds:
    def test_beds_less_than_zero(self):
        prop = make_property(beds=-1)
        valid, errors = PropertyRules.validate(prop)
        assert not valid
        assert "Beds must be greater than 0" in errors

    def test_beds_zero(self):
        prop = make_property(beds=0)
        valid, _ = PropertyRules.validate(prop)
        assert not valid

    def test_beds_too_many(self):
        prop = make_property(beds=21)
        valid, errors = PropertyRules.validate(prop)
        assert not valid
        assert "Unrealistic number of beds" in errors

    def test_beds_valid(self):
        prop = make_property(beds=3)
        valid, _ = PropertyRules.validate(prop)
        assert valid


class TestRulesBaths:
    def test_baths_negative(self):
        prop = make_property(baths=-1)
        valid, errors = PropertyRules.validate(prop)
        assert not valid
        assert "Baths must be greater than 0" in errors

    def test_baths_valid(self):
        prop = make_property(baths=2)
        valid, _ = PropertyRules.validate(prop)
        assert valid


class TestRulesFurnishing:
    def test_invalid_furnishing(self):
        prop = make_property(furnishing="InvalidValue")
        valid, errors = PropertyRules.validate(prop)
        assert not valid
        assert "Invalid furnishing" in errors[0]

    def test_valid_furnishing(self):
        prop = make_property(furnishing="Unfurnished")
        valid, _ = PropertyRules.validate(prop)
        assert valid


class TestRulesSource:
    def test_invalid_source(self):
        prop = make_property(source="invalid_source", link="https://example.com/property/1")
        valid, errors = PropertyRules.validate(prop)
        assert not valid
        assert "Invalid source" in errors[0]

    def test_valid_source(self):
        prop = make_property(source="olx")
        valid, _ = PropertyRules.validate(prop)
        assert valid


class TestRulesLink:
    def test_invalid_link(self):
        prop = make_property(link="not-a-url")
        valid, errors = PropertyRules.validate(prop)
        assert not valid
        assert "Invalid link" in errors

    def test_valid_link(self):
        prop = make_property(link="https://www.bayut.com/property/1")
        valid, _ = PropertyRules.validate(prop)
        assert valid


class TestRulesDate:
    def test_future_date_fails(self):
        prop = make_property(reactivated_date=datetime.now() + timedelta(days=1))
        valid, errors = PropertyRules.validate(prop)
        assert not valid
        assert "Reactivated date cannot be in the future" in errors

    def test_past_date_passes(self):
        prop = make_property(reactivated_date=datetime.now() - timedelta(days=1))
        valid, _ = PropertyRules.validate(prop)
        assert valid


class TestRulesValidProperty:
    def test_all_valid_passes(self):
        prop = make_property()
        valid, errors = PropertyRules.validate(prop)
        assert valid, f"Expected valid, got errors: {errors}"
