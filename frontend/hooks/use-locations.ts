"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

export function useLocations() {
  return useQuery({
    queryKey: ["locations"],
    queryFn: () => api.getLocations(),
    staleTime: 24 * 60 * 60 * 1000,
    gcTime: 24 * 60 * 60 * 1000,
  });
}