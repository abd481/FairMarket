import pytest

from data.validation.checksum import (
    ListingStatus,
    check_and_handle,
    generate_checksum,
)


class TestGenerateChecksum:
    def _row(self, **overrides):
        row = {
            "link": "https://example.com/1",
            "price": 1500000,
            "area": 150,
        }
        row.update(overrides)
        return row

    def test_deterministic(self):
        checksum_a = generate_checksum(self._row())
        checksum_b = generate_checksum(self._row())
        assert checksum_a == checksum_b

    def test_changes_with_link(self):
        checksum_a = generate_checksum(self._row())
        checksum_b = generate_checksum(self._row(link="https://example.com/2"))
        assert checksum_a != checksum_b

    def test_changes_with_price(self):
        checksum_a = generate_checksum(self._row())
        checksum_b = generate_checksum(self._row(price=2000000))
        assert checksum_a != checksum_b

    def test_changes_with_area(self):
        checksum_a = generate_checksum(self._row())
        checksum_b = generate_checksum(self._row(area=200))
        assert checksum_a != checksum_b

    def test_ignores_unrelated_fields(self):
        checksum_a = generate_checksum(self._row())
        checksum_b = generate_checksum(self._row(beds=5, baths=3, title="Ignored"))
        assert checksum_a == checksum_b

    def test_is_hex_md5(self):
        checksum = generate_checksum(self._row())
        assert len(checksum) == 32
        int(checksum, 16)


class FakeCollection:
    def __init__(self, existing):
        self._existing = existing

    def find_one(self, query):
        return self._existing


class TestCheckAndHandle:
    def _row(self, **overrides):
        row = {
            "link": "https://example.com/1",
            "price": 1500000,
            "area": 150,
        }
        row.update(overrides)
        return row

    def test_new_listing(self, monkeypatch):
        monkeypatch.setattr(
            "data.validation.checksum.get_raw_collection",
            lambda: FakeCollection(None),
        )
        row = self._row()
        status = check_and_handle(row, generate_checksum(row))
        assert status == ListingStatus.NEW

    def test_duplicate_listing(self, monkeypatch):
        row = self._row()
        existing = {
            "link": row["link"],
            "checksum": generate_checksum(row),
        }
        monkeypatch.setattr(
            "data.validation.checksum.get_raw_collection",
            lambda: FakeCollection(existing),
        )
        status = check_and_handle(row, generate_checksum(row))
        assert status == ListingStatus.DUPLICATE

    def test_updated_listing(self, monkeypatch):
        row = self._row(price=2000000)
        existing = {
            "link": row["link"],
            "checksum": "some-old-checksum",
        }
        monkeypatch.setattr(
            "data.validation.checksum.get_raw_collection",
            lambda: FakeCollection(existing),
        )
        status = check_and_handle(row, generate_checksum(row))
        assert status == ListingStatus.UPDATED

    def test_old_document_without_checksum_is_updated(self, monkeypatch):
        row = self._row()
        existing = {"link": row["link"]}
        monkeypatch.setattr(
            "data.validation.checksum.get_raw_collection",
            lambda: FakeCollection(existing),
        )
        status = check_and_handle(row, generate_checksum(row))
        assert status == ListingStatus.UPDATED
