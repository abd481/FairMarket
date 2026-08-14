from typing import Optional

from sqlalchemy import text

from api.schemas import PropertyDetail
from utils.db import get_pg_engine

SELECT_PROPERTY = text("""
    SELECT id, title, price, area, beds, baths, location,
           district, city, compound, property_type, furnishing,
           amenities, price_per_sqm, source, link
    FROM clean_properties
    WHERE id = :property_id
    """)


def _parse_amenities(value) -> list[str]:
    if value is None or value == "Not Mentioned":
        return []
    if isinstance(value, list):
        return [str(a).strip() for a in value if str(a).strip()]
    return [a.strip() for a in str(value).split(",") if a.strip()]


def _parse_furnishing(value) -> Optional[str]:
    if value is None or value == "Not Specified":
        return None
    return str(value)


def _optional_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def get_property(property_id: int) -> Optional[PropertyDetail]:
    """Fetch a single property from clean_properties by its integer id.

    Uses a parameterized query — the id is never interpolated into SQL text.
    Returns None when no matching row exists.
    """
    with get_pg_engine().connect() as conn:
        row = (
            conn.execute(SELECT_PROPERTY, {"property_id": property_id})
            .mappings()
            .first()
        )

    if row is None:
        return None

    area = _optional_float(row.get("area")) or 0.0
    price = _optional_float(row.get("price")) or 0.0

    price_per_sqm = _optional_float(row.get("price_per_sqm"))
    if price_per_sqm is None and area > 0:
        price_per_sqm = price / area

    return PropertyDetail(
        id=int(row["id"]),
        title=row.get("title"),
        price=price,
        area=area,
        beds=int(row["beds"]) if row.get("beds") is not None else 0,
        baths=int(row["baths"]) if row.get("baths") is not None else 0,
        location=row["location"],
        district=row.get("district"),
        city=row.get("city"),
        compound=row.get("compound"),
        property_type=row["property_type"],
        furnishing=_parse_furnishing(row.get("furnishing")),
        amenities=_parse_amenities(row.get("amenities")),
        price_per_sqm=price_per_sqm,
        source=row.get("source"),
        link=row.get("link"),
    )
