"use client";

import * as React from "react";
import type {
  PredictRequest,
  PredictResponse,
  Recommendation,
} from "@/types/api";

const STORAGE_KEY = "fairmarket:valuation";

export interface ValuationState {
  request: PredictRequest;
  result: PredictResponse;
}

type Listener = () => void;

class ValuationStore {
  private state: ValuationState | null = null;
  private listeners = new Set<Listener>();

  constructor() {
    if (typeof window === "undefined") return;
    try {
      const raw = window.sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        this.state = JSON.parse(raw) as ValuationState;
      }
    } catch {
      this.state = null;
    }
  }

  getSnapshot(): ValuationState | null {
    return this.state;
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  set(value: ValuationState): void {
    this.state = value;
    if (typeof window !== "undefined") {
      try {
        window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(value));
      } catch {
        // Storage unavailable (e.g. private mode) — keep in memory only.
      }
    }
    this.emit();
  }

  clear(): void {
    this.state = null;
    if (typeof window !== "undefined") {
      try {
        window.sessionStorage.removeItem(STORAGE_KEY);
      } catch {
        // ignore
      }
    }
    this.emit();
  }

  private emit(): void {
    this.listeners.forEach((listener) => listener());
  }
}

const store = new ValuationStore();

export function useValuationState(): {
  state: ValuationState | null;
  setState: (value: ValuationState) => void;
  clearState: () => void;
} {
  const state = React.useSyncExternalStore(
    (cb) => store.subscribe(cb),
    () => store.getSnapshot(),
    () => store.getSnapshot(),
  );

  return {
    state,
    setState: store.set.bind(store),
    clearState: store.clear.bind(store),
  };
}

export function sortRecommendations(items: Recommendation[]): Recommendation[] {
  return [...items].sort((a, b) => b.similarity - a.similarity);
}