import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import joblib
from sklearn.neighbors import NearestNeighbors

from utils.db import get_pg_engine
from models.predict import classify_mode, VILLA_TYPES
from models.predict import prepare_row

# --- Global config / shared resources ---------------------------------
REC_DIR = PROJECT_ROOT / "artifacts" / "recommendations"

# Per-mode filter definitions: which property types belong to each index,
# and whether "other" means "exclude" villa types (i.e. everything else).
MODEL_PARAMS = {
    "only_villas": {"property_types": VILLA_TYPES, "other": False},
    "no_villas": {"property_types": VILLA_TYPES, "other": True},
}


def build_index(mode):
    """Build and persist a KNN index (+ supporting artifacts) for a given mode.

    Loads clean_properties from Postgres, applies the same filters/feature
    engineering used at training time, transforms features through the
    saved pipeline for `mode`, fits a NearestNeighbors index on the result,
    and dumps the index plus its feature matrix / ids / metadata to disk.
    """
    REC_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_sql("SELECT * FROM clean_properties", get_pg_engine())

    # Filter by mode (villa vs. non-villa properties)
    if MODEL_PARAMS[mode]["other"]:
        df = df[~df["property_type"].isin(VILLA_TYPES)]
    else:
        df = df[df["property_type"].isin(VILLA_TYPES)]

    # Apply same filters as training (filter_data in preprocessing.py)
    cond = (df["area"] >= 50) & (df["price"] >= 1_000_000) & (df["price"] <= 23_000_000)
    df = df[cond].copy()

    print(f"{mode}: {len(df)} properties for index")

    # Feature engineering (same as preprocess() and prepare_row())
    df["compound"] = df["location"].apply(
        lambda x: (
            x.split(",")[0].strip()
            if pd.notna(x) and "," in x
            else (x.strip() if pd.notna(x) else "Unknown")
        )
    )
    df["location_proptype"] = (
        df["location"].fillna("Unknown") + ", " + df["property_type"]
    )
    df["beds_baths"] = df["beds"] * df["baths"]

    # Load pipeline and compute district_avg_pps
    pipeline = joblib.load(
        PROJECT_ROOT / "artifacts" / "pipelines" / f"{mode}_pipeline.joblib"
    )
    district_pps = df.groupby("district")["price_per_sqm"].mean()
    global_pps = df["price_per_sqm"].mean()
    df["district_avg_pps"] = df["district"].map(district_pps).fillna(global_pps)

    # Prepare X
    X = df.drop(columns=["price", "scraped_at", "id"], errors="ignore")
    if "title" not in X.columns:
        X["title"] = ""

    property_ids = df["id"].values
    metadata_cols = [
        "id",
        "price",
        "area",
        "beds",
        "baths",
        "property_type",
        "furnishing",
        "amenities",
        "location",
        "city",
        "district",
        "compound",
    ]

    X_tr = pipeline.transform(X)
    print(f"Feature matrix: {X_tr.shape}")

    knn = NearestNeighbors(n_neighbors=min(50, len(X_tr)), metric="euclidean")
    knn.fit(X_tr)

    joblib.dump(knn, REC_DIR / f"{mode}_knn.joblib")
    joblib.dump(X_tr, REC_DIR / f"{mode}_feature_matrix.joblib")
    joblib.dump(property_ids, REC_DIR / f"{mode}_property_ids.joblib")
    joblib.dump(df[metadata_cols], REC_DIR / f"{mode}_metadata.joblib")
    print(f"Saved artifacts to {REC_DIR}")


def recommend(property_id, mode, zone_filter=True, price_tolerance=0.3, k=10):
    """Print the top-k nearest-neighbor recommendations for a stored property_id."""
    # Load artifacts
    knn = joblib.load(REC_DIR / f"{mode}_knn.joblib")
    feature_matrix = joblib.load(REC_DIR / f"{mode}_feature_matrix.joblib")
    stored_ids = joblib.load(REC_DIR / f"{mode}_property_ids.joblib")
    metadata = joblib.load(REC_DIR / f"{mode}_metadata.joblib")

    # Find query property in the matrix
    match_idx = np.where(stored_ids == property_id)[0]
    if len(match_idx) == 0:
        print(f"Property {property_id} not found in index")
        return
    query_vector = feature_matrix[match_idx[0]]

    # Get nearest neighbors
    distances, indices = knn.kneighbors(
        query_vector.reshape(1, -1), n_neighbors=min(k * 3, len(feature_matrix))
    )
    neighbor_ids = stored_ids[indices[0]]
    neighbor_dists = distances[0]

    # Remove self
    mask = neighbor_ids != property_id
    neighbor_ids = neighbor_ids[mask]
    neighbor_dists = neighbor_dists[mask]

    # Look up metadata from cached DataFrame
    id_to_dist = dict(zip(neighbor_ids, neighbor_dists))
    meta = metadata[metadata["id"].isin(neighbor_ids)].copy()
    meta["_dist"] = meta["id"].map(id_to_dist)
    meta = meta.sort_values("_dist")

    # Query property info
    query_row = metadata[metadata["id"] == property_id].iloc[0]
    query_price = query_row["price"]
    query_compound = query_row["compound"]
    query_city = query_row["city"]

    # Apply filters + diversity
    seen_compounds = set()
    results = []

    for _, row in meta.iterrows():
        if zone_filter and row["compound"] in seen_compounds:
            continue
        if price_tolerance is not None:
            lower = query_price * (1 - price_tolerance)
            upper = query_price * (1 + price_tolerance)
            if not (lower <= row["price"] <= upper):
                continue
        if zone_filter:
            seen_compounds.add(row["compound"])
        results.append(row)
        if len(results) >= k:
            break

    print(
        f"\nRecommendation for Property #{property_id} - "
        f"{query_compound} (EGP {query_price:,.0f})"
    )
    print("-" * 110)
    print(
        f"  {'#':<3} {'Price':<12} {'Area':<5} {'Beds':<5} {'Baths':<5} "
        f"{'Type':<16} {'Location':<36} {'Sim':<5}"
    )
    print("-" * 110)

    for i, row in enumerate(results, 1):
        loc = str(row["location"])[:40]
        sim = 1 / (1 + row["_dist"])

    return results


def recommend_from_features(
    features: dict,
    mode: str,
    district_pps: dict,
    global_pps: float,
    pipeline,
    knn,
    stored_ids,
    metadata,
    price=None,
    price_min=None,
    price_max=None,
    k=10,
    price_tolerance=0.3,
) -> dict:
    """Recommend properties from a raw feature dict rather than a stored id.

    Builds the query vector via prepare_row + pipeline, finds nearest
    neighbors, then filters by an exact price (+/- tolerance) or a
    price range, whichever was supplied.
    """
    if price is not None:
        filtered_by = "price"
    elif price_min is not None or price_max is not None:
        filtered_by = "price_range"
    else:
        filtered_by = "features_only"

    prep_feat = prepare_row(features, district_pps, global_pps)
    query_vector = pipeline.transform(pd.DataFrame([prep_feat]))

    distances, indices = knn.kneighbors(query_vector, n_neighbors=k * 3)
    neighbor_ids = stored_ids[indices[0]]
    neighbor_dists = distances[0]

    metadata = metadata[metadata["id"].isin(neighbor_ids)].copy()
    id_to_indices = dict(zip(neighbor_ids, neighbor_dists))
    metadata["_dist"] = metadata["id"].map(id_to_indices)

    if price is not None:
        upper = price + (price * price_tolerance)
        lower = price - (price * price_tolerance)

    results = []
    for _, row in metadata.iterrows():
        # Skip if outside price filter
        if price is not None:
            if not (lower <= row["price"] <= upper):
                continue
        else:
            if price_min is not None and row["price"] < price_min:
                continue
            if price_max is not None and row["price"] > price_max:
                continue

        results.append(row.to_dict())
        if len(results) >= k:
            break

    for r in results:
        r["similarity"] = 1 / (1 + r["_dist"])
        r.pop("_dist")

    return {
        "filtered_by": filtered_by,
        "recommendations": results,
    }


def explore(
    city=None, district=None, property_type=None, price_min=None, price_max=None, k=20
):
    """Browse recent listings with optional filters, flagging underpriced deals."""
    query = """
        SELECT cp.*, pp.predicted_price
        FROM clean_properties cp
        LEFT JOIN property_predictions pp ON cp.id = pp.property_id
        WHERE 1=1
    """
    params = {}

    if city:
        query += " AND cp.city = :city"
        params["city"] = city
    if district:
        query += " AND cp.district = :district"
        params["district"] = district
    if property_type:
        query += " AND cp.property_type = :property_type"
        params["property_type"] = property_type
    if price_min:
        query += " AND cp.price >= :price_min"
        params["price_min"] = price_min
    if price_max:
        query += " AND cp.price <= :price_max"
        params["price_max"] = price_max

    query += " ORDER BY cp.scraped_at DESC LIMIT :k"
    params["k"] = k

    df = pd.read_sql(query, get_pg_engine(), params=params)

    if df.empty:
        print("No listings match your filters.")
        return

    # Flag properties where the model's predicted price beats the asking price
    if "predicted_price" in df.columns and df["predicted_price"].notna().any():
        df["_value_flag"] = df["predicted_price"] > df["price"]
    else:
        df["_value_flag"] = False

    print(
        f"\nExplore Results{' - ' + city if city else ''}"
        f"{' - ' + district if district else ''}"
        f"{' - ' + property_type if property_type else ''}"
    )
    print("-" * 120)
    print(
        f"  {'#':<3} {'Price':<12} {'Predicted':<12} {'Area':<5} {'Beds':<5} "
        f"{'Baths':<5} {'Type':<16} {'Location':<36} {'PPS':<8} {'Value':<6}"
    )
    print("-" * 120)
    for i, (_, row) in enumerate(df.iterrows(), 1):
        loc = str(row["location"])[:35]
        pps = row["price"] / row["area"] if row["area"] > 0 else 0
        value = "⭐ Deal" if row["_value_flag"] else ""
        pred = (
            f"EGP {row['predicted_price']:,.0f}"
            if pd.notna(row.get("predicted_price"))
            else "N/A"
        )
        print(
            f"  {i:<3} EGP {row['price']:>8,.0f} {pred:<12} {row['area']:<4.0f} "
            f"{row['beds']:<5} {row['baths']:<5} "
            f"{row['property_type']:<16} {loc:<36} {pps:>7,.0f} {value:<6}"
        )

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-index", choices=["only_villas", "no_villas"])
    parser.add_argument("--recommend", type=int, help="Property ID to recommend from")
    parser.add_argument(
        "--mode", choices=["only_villas", "no_villas"], default="no_villas"
    )
    parser.add_argument("--price-tolerance", type=float, default=0.3)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--explore", action="store_true")
    parser.add_argument("--city", type=str)
    parser.add_argument("--district", type=str)
    parser.add_argument("--property-type", type=str)
    parser.add_argument("--price-min", type=float)
    parser.add_argument("--price-max", type=float)

    args = parser.parse_args()

    if args.explore:
        explore(
            city=args.city,
            district=args.district,
            property_type=args.property_type,
            price_min=args.price_min,
            price_max=args.price_max,
            k=args.k,
        )
    if args.build_index:
        build_index(args.build_index)
    elif args.recommend:
        recommend(
            args.recommend, args.mode, price_tolerance=args.price_tolerance, k=args.k
        )
