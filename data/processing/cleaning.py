# In the name of Allah, The Most Gracious, The Most Merciful

import os
import sys
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from utils.db import get_pg_engine

load_dotenv()

KNOWN_CITIES = ["Cairo", "Giza", "Alexandria", "New Cairo", "New Capital City"]
GOVERNORATES = {"Cairo", "Giza", "New Cairo", "Alexandria"}


def canonicalize_location(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def strip_governorate(loc):
        if pd.isna(loc):
            return loc
        parts = [p.strip() for p in loc.split(",")]
        if len(parts) > 2 and parts[-1] in GOVERNORATES:
            parts = parts[:-1]
        return ", ".join(parts)

    def prefix_key(loc):
        if pd.isna(loc):
            return loc
        parts = [p.strip() for p in loc.split(",")]
        return ", ".join(parts[:2])

    df["location_canonical"] = df["location"].apply(strip_governorate)
    df["location_prefix"] = df["location_canonical"].apply(prefix_key)

    # most-frequent-wins: pick the fullest common canonical form per prefix
    freq_table = (
        df.groupby(["location_prefix", "location_canonical"])
        .size()
        .reset_index(name="cnt")
        .sort_values("cnt", ascending=False)
        .drop_duplicates("location_prefix")
        .set_index("location_prefix")["location_canonical"]
        .to_dict()
    )

    df["location"] = (
        df["location_prefix"].map(freq_table).fillna(df["location_canonical"])
    )
    df = df.drop(columns=["location_canonical", "location_prefix"])

    return df


def load_data() -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM properties", get_pg_engine())
    print(f"✅ Loaded {len(df)} rows")
    return df


def clean_price_per_sqm(df: pd.DataFrame) -> pd.DataFrame:
    df["price_per_sqm"] = df["price"] / df["area"].replace(0, pd.NA)
    return df


def clean_baths(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["baths"] = pd.to_numeric(df["baths"], errors="coerce")

    df["baths"] = df.groupby(["property_type"])["baths"].transform(
        lambda x: x.fillna(x.median())
    )

    df = df.dropna(subset=["baths"])
    df["baths"] = df["baths"].astype(int)

    return df


def clean_studio(df: pd.DataFrame) -> pd.DataFrame:
    df["is_studio"] = (
        df["beds"].astype(str).str.contains("Studio", case=False, na=False)
    )
    df["beds"] = df["beds"].replace("Studio", 0)
    return df


def clean_beds(df: pd.DataFrame) -> pd.DataFrame:
    df["beds"] = pd.to_numeric(df["beds"], errors="coerce")
    df["beds"] = df.groupby("property_type")["beds"].transform(
        lambda x: x.fillna(x.median())
    )
    df["beds"] = df["beds"].astype(int)
    return df


def clean_amenities(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["amenities"] = df["amenities"].replace("", pd.NA)
    df["amenities"] = df["amenities"].fillna("Not Mentioned")

    def parse_amenities(text):
        if pd.isna(text) or text == "Not Mentioned":
            return 0
        return len([item.strip() for item in str(text).split(",") if item.strip()])

    df["amenity_count"] = df["amenities"].apply(parse_amenities)

    return df


def clean_furnishing(df: pd.DataFrame) -> pd.DataFrame:
    df["furnishing"] = df["furnishing"].fillna("Not Specified")
    return df


def clean_property_type(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "Town House": "Townhouse",
        "Standalone Villa": "Stand Alone Villa",
        "Ivilla": "Stand Alone Villa",
        "Roof": "Other",
        "Other Residential": "Other",
        "Room": "Other",
    }
    df["property_type"] = df["property_type"].str.strip().str.title().replace(mapping)
    return df


def clean_transaction_type(df: pd.DataFrame) -> pd.DataFrame:
    df["transaction_type"] = (
        df["link"]
        .str.contains("for-rent", case=False, na=False)
        .map({True: "rent", False: "sale"})
    )
    df = df[df["transaction_type"] == "sale"]
    return df


def split_location(location):
    """Deterministically split a location string into compound, district, city.

    Rules (no curated lookup lists):
    - 3 parts:  compound = part[0], district = part[1], city = part[-1]
                e.g. "Cairova, 6th Settlement, New Cairo"
        -> compound=Cairova, district=6th Settlement, city=New Cairo
    - 2 parts:  compound = district = part[0], city = part[1]
                e.g. "Hyde Park New Cairo Compound, 5th Settlement"
        -> compound=Hyde Park New Cairo Compound, district=Hyde Park New Cairo Compound,
           city=5th Settlement
    """
    if pd.isna(location):
        return pd.NA, pd.NA, pd.NA
    parts = [p.strip() for p in location.split(",") if p.strip()]
    if not parts:
        return pd.NA, pd.NA, pd.NA
    if len(parts) >= 3:
        compound, district = parts[0], parts[1]
    else:
        compound, district = parts[0], parts[0]
    city = parts[-1]
    return compound, district, city


def clean_location(df: pd.DataFrame, use_known_cities: bool = True) -> pd.DataFrame:
    df[["compound", "district", "city"]] = (
        df["location"].apply(split_location).apply(pd.Series)
    )
    return df


def drop_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=["checksum", "reactivated_date", "transformed_at"])
    return df


def save_data(df: pd.DataFrame) -> None:
    df.to_sql(
        name="clean_properties", con=get_pg_engine(), if_exists="replace", index=False
    )
    # print(f"✅ Saved {len(df)} rows to clean_properties")


def filter_price_anomalies(
    df: pd.DataFrame, pps_threshold: float = 0.30, min_district_size: int = 3
) -> pd.DataFrame:
    """
    Drop properties whose price_per_sqm is suspiciously low for their district.
    These are usually installment/down-payment prices mis-scraped as full prices.

    For each district with >= min_district_size properties, compute the median PPS.
    If a property's PPS < pps_threshold * district_median_PPS, it's flagged as an anomaly.

    Args:
        df: DataFrame with 'district' and 'price_per_sqm' columns
        pps_threshold: Fraction of district median PPS below which a listing is anomalous
        min_district_size: Minimum number of properties in a district to compute a reliable median
    """
    initial = len(df)

    district_pps_median = df.groupby("district")["price_per_sqm"].transform("median")
    district_count = df.groupby("district")["price_per_sqm"].transform("count")

    is_anomaly = (district_count >= min_district_size) & (
        df["price_per_sqm"] < pps_threshold * district_pps_median
    )

    dropped = is_anomaly.sum()
    if dropped > 0:
        print(
            f"⚠️ Price anomaly filter dropped {dropped} suspicious listings "
            f"(PPS < {pps_threshold:.0%} of district median) — {len(df) - dropped} rows remaining"
        )
        for _, row in df[is_anomaly].iterrows():
            print(
                f"     {row['district']:<25} actual={row['price']:>8,.0f}  area={row['area']:>4.0f}  "
                f"PPS={row['price_per_sqm']:>7,.0f}  district_median_PPS={district_pps_median.loc[row.name]:>7,.0f}"
            )

    return df[~is_anomaly]


def validate(df: pd.DataFrame) -> pd.DataFrame:
    initial_count = len(df)

    # 1. drop nulls in critical columns
    critical_columns = ["price", "area", "beds", "baths", "property_type", "city"]
    df = df.dropna(subset=critical_columns)

    # 2. drop invalid price and area
    df = df[df["price"].between(1_000_000, 150_000_000)]
    df = df[df["area"] > 0]

    # 3. drop negative beds and baths
    df = df[df["beds"] >= 0]
    df = df[df["baths"] >= 0]

    # 4. drop unexpected transaction types
    df = df[df["transaction_type"] == "sale"]

    # 5. drop negative amenity_count
    df = df[df["amenity_count"] >= 0]

    # 6. drop duplicates
    df = df.drop_duplicates()

    dropped = initial_count - len(df)
    if dropped > 0:
        print(f"⚠️ Validation dropped {dropped} bad rows — {len(df)} rows remaining")
    else:
        print(f"✅ All {len(df)} rows passed validation")

    return df


def clean():
    df = load_data()
    df = clean_price_per_sqm(df)
    df = clean_baths(df)
    df = clean_studio(df)
    df = clean_beds(df)
    df = clean_amenities(df)
    df = clean_furnishing(df)
    df = clean_property_type(df)
    df = clean_transaction_type(df)
    df = canonicalize_location(df)
    df = clean_location(df, use_known_cities=False)
    df = drop_columns(df)
    df = filter_price_anomalies(df)
    df = validate(df)
    save_data(df)


if __name__ == "__main__":
    clean()
