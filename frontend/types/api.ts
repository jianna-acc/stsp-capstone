// File: /frontend/types/api.ts
// Purpose: Defines shared TypeScript types for responses returned
// by the FastAPI backend.

export type ApiEnvironment =
  | "development"
  | "testing"
  | "production";

export interface ApiHealthResponse {
  status: "healthy";
  service: string;
  version: string;
  environment: ApiEnvironment;
}