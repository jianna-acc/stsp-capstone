// File: /frontend/features/study-plans/types.ts
// Purpose: Defines Track D frontend contracts for study plans,
// sessions, schedule generation, and safe API errors.

export type StudyPlanStatus =
  | "draft"
  | "active"
  | "completed"
  | "archived";

export type StudyPlanGenerationMode =
  | "manual"
  | "generated";

export type StudySessionStatus =
  | "planned"
  | "completed"
  | "skipped";

export type StudySessionOrigin =
  | "manual"
  | "generated";


export interface StudyPlan {
  id: string;
  title: string;
  starts_on: string;
  ends_on: string;
  status: StudyPlanStatus;
  generation_mode:
    StudyPlanGenerationMode;
  generated_at: string | null;
  created_at: string;
  updated_at: string;
}


export interface StudyPlanListResponse {
  items: StudyPlan[];
}


export interface StudyPlanCreateRequest {
  title: string;
  starts_on: string;
  ends_on: string;
}


export interface StudySession {
  id: string;
  study_plan_id: string;
  subject_id: string;
  title: string;
  starts_at: string;
  ends_at: string;
  status: StudySessionStatus;
  origin: StudySessionOrigin;
  notes: string | null;
  created_at: string;
  updated_at: string;
}


export interface StudySessionListResponse {
  items: StudySession[];
}


export interface StudySessionCreateRequest {
  subject_id: string;
  title: string;
  starts_at: string;
  ends_at: string;
  notes?: string | null;
}


export interface SchedulableTask {
  task_id: string;
  subject_id: string;
  title: string;
  deadline: string;
  estimated_minutes: number;
  priority_weight: number;
}


export interface UnscheduledTask {
  task_id: string;
  remaining_minutes: number;
}


export interface StudyPlanGenerationRequest {
  title: string;
  starts_on: string;
  ends_on: string;
  tasks: SchedulableTask[];
}


export interface StudyPlanGenerationResponse {
  plan: StudyPlan;
  sessions: StudySession[];
  unscheduled_tasks: UnscheduledTask[];
}


export interface StudyPlanApiErrorResponse {
  error_code?: string;
  message?: string;
  detail?: unknown;
}


export interface StudyPlanApiRequestOptions {
  signal?: AbortSignal;
}