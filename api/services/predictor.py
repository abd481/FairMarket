from api.schemas import PredictRequest, PredictResponse, ResolvedLocation
from models.predict import predict_from_features, classify_mode


def build_features(
    request: PredictRequest, resolved_location: ResolvedLocation
) -> dict:

    return {
        "area": request.area,
        "beds": request.beds,
        "baths": request.baths,
        "location": request.location,
        "property_type": request.property_type.value,
        "furnishing": request.furnishing.value,
        "amenities": ", ".join(request.amenities),
        "amenity_count": len(request.amenities),
    }


def predict(
    request: PredictRequest, resolved_location: ResolvedLocation, models: dict
) -> PredictResponse:

    mode = classify_mode(request.property_type.value)
    artifacts = models[mode]

    features = build_features(request, resolved_location)

    results = predict_from_features(
        features,
        district_pps=artifacts["district_pps"],
        global_pps=artifacts["global_pps"],
        pipeline=artifacts["pipeline"],
        model=artifacts["model"],
        calib=artifacts["calib"],
        resolved_location=resolved_location,
    )

    return PredictResponse(
        predicted_price=results["predicted_price"],
        price_lower=results["price_lower"],
        price_upper=results["price_upper"],
        resolved_location=resolved_location,
    )
