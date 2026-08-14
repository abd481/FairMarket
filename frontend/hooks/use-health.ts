"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

export function useHealth(enabled = false) {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => api.health(),
    enabled,
    staleTime: 30 * 1000,
  });
}