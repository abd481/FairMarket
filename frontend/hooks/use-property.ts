"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { PropertyDetail } from "@/types/api";

export function useProperty(id: number) {
  return useQuery({
    queryKey: ["property", id],
    queryFn: () => api.getProperty(id),
    enabled: Number.isInteger(id) && id > 0,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    retry: (failureCount, error) => {
      if ("status" in error && (error as { status: number }).status === 404) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export type { PropertyDetail };