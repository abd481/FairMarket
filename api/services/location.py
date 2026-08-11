from api.schemas import ResolvedLocation
import difflib

FUZZY_CUTOFF_SINGLE = 0.75


def fuzzy_match(value, vocabulary, cutoff):

    if value in vocabulary:
        return value
    matches = difflib.get_close_matches(value, list(vocabulary), n=1, cutoff=cutoff)
    if matches:
        return matches[0]
    else:
        return None


def build_location_cache(df):

    locations = sorted(df["location"].dropna().unique().tolist())
    district_to_city = (
        df.groupby("district")["city"]
        .agg(lambda s: s.value_counts().idxmax())
        .to_dict()
    )
    known_districts = set(district_to_city.keys())
    known_cities = set(district_to_city.values())
    district_pps = df.groupby("district")["price_per_sqm"].mean().to_dict()
    global_pps = float(df["price_per_sqm"].mean())
    lookup = {loc.lower(): loc for loc in locations}
    parts = df.groupby("location")[["compound", "district", "city"]].first()
    location_parts = {
        loc: {"compound": r.compound, "district": r.district, "city": r.city}
        for loc, r in parts.iterrows()
    }

    return {
        "locations": locations,
        "lookup": lookup,
        "district_to_city": district_to_city,
        "known_districts": known_districts,
        "known_cities": known_cities,
        "district_pps": district_pps,
        "global_pps": global_pps,
        "location_parts": location_parts,
    }


def resolve_location(location_str: str, caches: dict) -> ResolvedLocation:

    # Guard empty
    if not location_str or not location_str.strip():
        return ResolvedLocation(
            original="",
            compound="Unknown",
            city="Unknown",
            district="Unknown",
            matched=False,
        )

    normalized = location_str.strip().lower()

    # exact match against prebuilt case-insensitive lookup
    if normalized in caches["lookup"]:
        parts = caches["location_parts"][caches["lookup"][normalized]]
        return ResolvedLocation(
            original=location_str,
            compound=parts["compound"],
            district=parts["district"],
            city=parts["city"],
            matched=True,
        )

    # fuzzy fallback
    match = fuzzy_match(
        normalized, list(caches["lookup"].keys()), cutoff=FUZZY_CUTOFF_SINGLE
    )
    if match:
        parts = caches["location_parts"][caches["lookup"][match]]

        return ResolvedLocation(
            original=location_str,
            compound=parts["compound"],
            district=parts["district"],
            city=parts["city"],
            matched=True,
        )

    return ResolvedLocation(
        original=location_str,
        compound="Unknown",
        district="Unknown",
        city="Unknown",
        matched=False,
    )
