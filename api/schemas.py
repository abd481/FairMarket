from pydantic import BaseModel, Field, model_validator
from enum import Enum
from typing import Optional, List, Self


class PropertyType(str, Enum):
    APARTMENT = "Apartment"
    OTHER = "Other"
    DUPLEX = "Duplex"
    PENTHOUSE = "Penthouse"
    HOTEL_APARTMENT = "Hotel Apartment"
    TOWNHOUSE = "Townhouse"
    STUDIO = "Studio"
    VILLA = "Villa"
    TWIN_HOUSE = "Twin House"
    STAND_ALONE_VILLA = "Stand Alone Villa"
    CHALET = "Chalet"


class Furnishing(str, Enum):
    FURNISHED = "Furnished"
    UNFURNISHED = "Unfurnished"


class PredictRequest(BaseModel):
    area: float = Field(gt=0)
    beds: int = Field(ge=0)
    baths: int = Field(gt=0)
    location: str = Field(min_length=1)
    property_type: PropertyType
    furnishing: Furnishing
    amenities: list[str] = []


class ResolvedLocation(BaseModel):
    original: str
    city: Optional[str] = None
    district: Optional[str] = None
    compound: Optional[str] = None
    matched: bool


class PredictResponse(BaseModel):
    predicted_price: float
    price_upper: float
    price_lower: float
    resolved_location: ResolvedLocation


class Recommendation(BaseModel):
    price: float
    beds: int
    baths: int
    area: float
    location: str
    property_type: PropertyType
    furnishing: Optional[Furnishing] = None
    amenities: list[str] = []
    property_id: int
    similarity: float


class RecommendRequest(PredictRequest):
    price: Optional[float] = Field(default=None, gt=0)
    price_min: Optional[float] = Field(default=None, ge=0)
    price_max: Optional[float] = Field(default=None, ge=0)
    k: int = Field(default=10, ge=1)
    price_tolerance: float = Field(default=0.3, ge=0, le=1)

    @model_validator(mode="after")
    def validate(self) -> Self:

        if (
            self.price_min is not None
            and self.price_max is not None
            and self.price_min > self.price_max
        ):
            raise ValueError("Minum price cannot exceed maximum price.")
        if self.price is not None and (
            self.price_min is not None or self.price_max is not None
        ):
            raise ValueError("You cannot provide both price and price range.")

        return self


class FilterBy(str, Enum):
    FEATURES_ONLY = "features_only"
    PRICE = "price"
    PRICE_RANGE = "price_range"


class RecommendResponse(BaseModel):
    filtered_by: FilterBy
    recommendations: list[Recommendation]
    predicted_fair_price: Optional[float] = None
    resolved_location: ResolvedLocation


class Status(str, Enum):
    READY = "ready"
    STARTING = "starting"
    ERROR = "error"


class HealthResponse(BaseModel):
    status: Status
    models_loaded: list[str]
    recommend_loaded: list[str]
    uptime_seconds: float
    started_at: str
    known_locations: int


class ErrorResponse(BaseModel):
    error: str
    detail: str
