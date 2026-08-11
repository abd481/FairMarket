from api.schemas import (
    Recommendation,
    RecommendRequest,
    RecommendResponse,
    ResolvedLocation,
    FilterBy,
    PropertyType,
    Furnishing,
)
from models.recommend import recommend_from_features, classify_mode
from api.services.predictor import build_features, predict


def build_recommend_features(
    request: RecommendRequest, resolved_location: ResolvedLocation
):
    features = build_features(request, resolved_location)
    features["city"] = resolved_location.city
    features["district"] = resolved_location.district
    features["source"] = ""
    features["title"] = ""

    return features


def _parse_amenities(text):
    if not text or text == "Not Mentioned":
        return []
    return [a.strip() for a in str(text).split(",") if a.strip()]


def _to_recommendation(row: dict) -> Recommendation:
    return Recommendation(
        price=float(row["price"]),
        beds=int(row["beds"]),
        baths=int(row["baths"]),
        area=float(row["area"]),
        location=row["location"],
        property_type=PropertyType(row["property_type"]),
        furnishing=(
            Furnishing(row["furnishing"])
            if row["furnishing"] != "Not Specified"
            else None
        ),
        amenities=_parse_amenities(row["amenities"]),
        property_id=int(row["id"]),
        similarity=row["similarity"],
    )


def recommend(request, resolved_location, models) -> RecommendResponse:

    mode = classify_mode(request.property_type.value)
    artifacts = models[mode]

    features = build_recommend_features(request, resolved_location)
    results = recommend_from_features(
        features,
        mode,
        district_pps=artifacts["district_pps"],
        global_pps=artifacts["global_pps"],
        pipeline=artifacts["pipeline"],
        knn=artifacts["knn"],
        stored_ids=artifacts["stored_ids"],
        metadata=artifacts["metadata"],
        price=request.price,
        price_min=request.price_min,
        price_max=request.price_max,
        k=request.k,
        price_tolerance=request.price_tolerance,
    )

    return RecommendResponse(
        filtered_by=FilterBy(results["filtered_by"]),
        recommendations=[_to_recommendation(r) for r in results["recommendations"]],
        predicted_fair_price=predict(
            request, resolved_location, models
        ).predicted_price,
        resolved_location=resolved_location,
    )
