"use client";

import { useMutation } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  PredictRequest,
  PredictResponse,
  RecommendRequest,
  RecommendResponse,
} from "@/types/api";

export function usePredict() {
  return useMutation({
    mutationFn: (body: PredictRequest) => api.predict(body),
  });
}

export function useRecommend() {
  return useMutation({
    mutationFn: (body: RecommendRequest) => api.recommend(body),
  });
}

export type { PredictResponse, RecommendResponse };
