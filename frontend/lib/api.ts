import type {
  HealthResponse,
  PredictRequest,
  PredictResponse,
  PropertyDetail,
  RecommendRequest,
  RecommendResponse,
  ApiErrorBody,
} from "@/types/api";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;
  readonly code?: string;

  constructor(message: string, status: number, detail: string, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.code = code;
  }
}

function resolveBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL;
  if (fromEnv && fromEnv.trim().length > 0) {
    return fromEnv.replace(/\/+$/, "");
  }
  // Isolated default — safe for local development against the FastAPI backend.
  return "http://localhost:8000";
}

async function parseErrorBody(response: Response): Promise<ApiErrorBody | null> {
  try {
    const body = (await response.json()) as ApiErrorBody | string;
    if (typeof body === "string") {
      return { error: "error", detail: body };
    }
    return body;
  } catch {
    return null;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${resolveBaseUrl()}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(
      "network_error",
      0,
      "Unable to reach the valuation service. Please check that the API is running.",
      "network_error",
    );
  }

  if (!response.ok) {
    const errorBody = await parseErrorBody(response);
    const detail = errorBody?.detail ?? `Request failed with status ${response.status}.`;
    throw new ApiError(
      detail,
      response.status,
      detail,
      errorBody?.error,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  getBaseUrl: resolveBaseUrl,

  getLocations(): Promise<string[]> {
    return request<string[]>("/api/locations", { method: "GET" });
  },

  predict(body: PredictRequest): Promise<PredictResponse> {
    return request<PredictResponse>("/api/predict", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  recommend(body: RecommendRequest): Promise<RecommendResponse> {
    return request<RecommendResponse>("/api/recommend", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getProperty(id: number): Promise<PropertyDetail> {
    return request<PropertyDetail>(`/api/properties/${id}`, {
      method: "GET",
    });
  },

  health(): Promise<HealthResponse> {
    return request<HealthResponse>("/health", { method: "GET" });
  },
};

export default api;