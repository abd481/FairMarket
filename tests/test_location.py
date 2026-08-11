import pandas as pd
import pytest

from api.services.location import build_location_cache, resolve_location


@pytest.fixture
def caches():
    df = pd.DataFrame(
        {
            "location": [
                "Crescent Walk, 6th Settlement",
                "1st Settlement, New Cairo",
                "Sukoon, New Zayed",
            ],
            "district": ["6th Settlement", "1st Settlement", "New Zayed"],
            "city": ["New Cairo", "New Cairo", "New Zayed"],
            "compound": ["Crescent Walk", "1st Settlement", "Sukoon"],
            "price_per_sqm": [50000, 40000, 60000],
        }
    )
    return build_location_cache(df)


class TestResolveLocation:
    def test_exact_match(self, caches):
        loc = resolve_location("Crescent Walk, 6th Settlement", caches)
        assert loc.matched is True
        assert loc.district == "6th Settlement"
        assert loc.city == "New Cairo"
        assert loc.compound == "Crescent Walk"

    def test_case_insensitive_match(self, caches):
        loc = resolve_location("CRESCENT WALK, 6TH SETTLEMENT", caches)
        assert loc.matched is True
        assert loc.district == "6th Settlement"

    def test_fuzzy_fallback(self, caches):
        loc = resolve_location("Crescent Walk, 6th Settlemen", caches)
        assert loc.matched is True
        assert loc.district == "6th Settlement"

    def test_unknown_location(self, caches):
        loc = resolve_location("Nowhere City", caches)
        assert loc.matched is False
        assert loc.city == "Unknown"
        assert loc.district == "Unknown"

    def test_empty_string(self, caches):
        loc = resolve_location("", caches)
        assert loc.matched is False

    def test_whitespace_only(self, caches):
        loc = resolve_location("   ", caches)
        assert loc.matched is False

    def test_none(self, caches):
        loc = resolve_location(None, caches)
        assert loc.matched is False
