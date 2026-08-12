// File: /frontend/features/study-timer/types.ts
// Purpose: Defines frontend contracts for persisted actual
// Study Activity timer state and lifecycle operations.

export type StudyActivityStatus =
  | "running"
  | "paused"
  | "completed";

export type StudyActivityMode =
  | "focus"
  | "break";

export interface StudyActivity {
  id: string;
  subject_id: string | null;
  study_plan_id: string | null;
  study_session_id: string | null;
  title: string;
  status: StudyActivityStatus;
  mode: StudyActivityMode;
  started_at: string;
  ended_at: string | null;
  segment_started_at: string | null;
  focus_seconds: number;
  break_seconds: number;
  created_at: string;
  updated_at: string;
}

export interface StudyActivityStartRequest {
  subject_id?: string | null;
  title?: string | null;
  study_plan_id?: string | null;
  study_session_id?: string | null;
}

export interface StudyActivityApiRequestOptions {
  signal?: AbortSignal;
}

export interface StudyActivityApiErrorResponse {
  error_code?: string;
  message?: string;
  detail?: unknown;
}