// TypeScript types mirroring the FastAPI backend contract in `api/schemas.py`.
// Keep these in sync with the Python schema — do not invent fields.

export const PROPERTY_TYPES = [
  "Apartment",
  "Other",
  "Duplex",
  "Penthouse",
  "Hotel Apartment",
  "Townhouse",
  "Studio",
  "Villa",
  "Twin House",
  "Stand Alone Villa",
  "Chalet",
] as const;

export type PropertyType = (typeof PROPERTY_TYPES)[number];

export const FURNISHING_OPTIONS = ["Furnished", "Unfurnished"] as const;
export type Furnishing = (typeof FURNISHING_OPTIONS)[number];

export const AMENITIES = [
  "pool",
  "gym",
  "balcony",
  "elevator",
  "security",
  "covered parking",
  "private garden",
  "maids room",
  "sea view",
  "smart home",
] as const;
export type Amenity = (typeof AMENITIES)[number];

export interface PredictRequest {
  area: number;
  beds: number;
  baths: number;
  location: string;
  property_type: PropertyType;
  furnishing: Furnishing;
  amenities: string[];
}

export interface ResolvedLocation {
  original: string;
  city?: string | null;
  district?: string | null;
  compound?: string | null;
  matched: boolean;
}

export interface PredictResponse {
  predicted_price: number;
  price_upper: number;
  price_lower: number;
  resolved_location: ResolvedLocation;
}

export type FilterBy = "features_only" | "price" | "price_range";

export interface Recommendation {
  price: number;
  beds: number;
  baths: number;
  area: number;
  location: string;
  property_type: PropertyType;
  furnishing: Furnishing | null;
  amenities: string[];
  property_id: number;
  similarity: number;
}

export interface RecommendRequest extends PredictRequest {
  price?: number | null;
  price_min?: number | null;
  price_max?: number | null;
  k?: number;
  price_tolerance?: number;
}

export interface RecommendResponse {
  filtered_by: FilterBy;
  recommendations: Recommendation[];
  predicted_fair_price: number | null;
  resolved_location: ResolvedLocation;
}

export interface PropertyDetail {
  id: number;
  title?: string | null;
  price: number;
  area: number;
  beds: number;
  baths: number;
  location: string;
  district?: string | null;
  city?: string | null;
  compound?: string | null;
  property_type: string;
  furnishing?: string | null;
  amenities: string[];
  price_per_sqm?: number | null;
  source?: string | null;
  link?: string | null;
}

export type HealthStatus = "ready" | "starting" | "error";

export interface HealthResponse {
  status: HealthStatus;
  models_loaded: string[];
  recommend_loaded: string[];
  uptime_seconds: number;
  started_at: string;
  known_locations: number;
}

export interface ApiErrorBody {
  error: string;
  detail: string;
}