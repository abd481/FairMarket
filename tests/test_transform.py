import pytest

from data.processing.transform import safe_beds, safe_int


class TestSafeInt:
    @pytest.mark.parametrize(
        "value,expected", [(5, 5), ("7", 7), ("  12  ", 12), (-3, -3)]
    )
    def test_valid_values(self, value, expected):
        assert safe_int(value) == expected

    @pytest.mark.parametrize("value", ["abc", "7.5", "", None, [1, 2], {}])
    def test_invalid_values_return_none(self, value):
        assert safe_int(value) is None


class TestSafeBeds:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (3, "3"),
            ("3", "3"),
            (4.5, "4"),
            (None, None),
            ("Studio", "Studio"),
            ("studio", "Studio"),
            ("  STUDIO  ", "Studio"),
        ],
    )
    def test_valid_values(self, value, expected):
        assert safe_beds(value) == expected

    @pytest.mark.parametrize("value", ["abc", "3.5", "", "hotel"])
    def test_garbage_returns_none(self, value):
        assert safe_beds(value) is None
