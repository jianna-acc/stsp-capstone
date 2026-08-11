// File: /frontend/features/academic-tasks/types.ts
// Purpose: Defines Academic Task CRUD, priority, request,
// response, and frontend API error contracts.

export type AcademicTaskDifficulty =
  | "easy"
  | "medium"
  | "hard";

export type AcademicTaskType =
  | "assignment"
  | "project"
  | "exam"
  | "quiz"
  | "reading"
  | "presentation"
  | "research"
  | "other";

export type AcademicTaskOutputType =
  | "writing"
  | "computation"
  | "research"
  | "presentation"
  | "creative"
  | "reading_analysis"
  | "memorization"
  | "mixed"
  | "other";

export type AcademicTaskStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "cancelled";

export interface AcademicTaskCreateRequest {
  subject_id: string;
  title: string;
  description?: string | null;
  deadline: string;
  estimated_minutes: number;
  difficulty: AcademicTaskDifficulty;
  task_type: AcademicTaskType;
  output_type: AcademicTaskOutputType;
}

export interface AcademicTaskUpdateRequest {
  subject_id?: string;
  title?: string;
  description?: string | null;
  deadline?: string;
  estimated_minutes?: number;
  difficulty?: AcademicTaskDifficulty;
  task_type?: AcademicTaskType;
  output_type?: AcademicTaskOutputType;
}

export interface AcademicTaskStatusUpdateRequest {
  status: AcademicTaskStatus;
}

export interface AcademicTaskResponse {
  id: string;
  subject_id: string;
  title: string;
  description: string | null;
  deadline: string;
  estimated_minutes: number;
  difficulty: AcademicTaskDifficulty;
  task_type: AcademicTaskType;
  output_type: AcademicTaskOutputType;
  status: AcademicTaskStatus;
  created_at: string;
  updated_at: string;
}

export interface AcademicTaskListResponse {
  items: AcademicTaskResponse[];
}

export interface AcademicTaskPriorityBreakdown {
  total_score: number;
  deadline_score: number;
  difficulty_score: number;
  estimated_time_score: number;
  output_confidence_score: number;
  previous_performance_score: number;
  available_study_time_score: number;
  status_score: number;
}

export interface AcademicTaskPriorityResponse {
  task: AcademicTaskResponse;
  priority: AcademicTaskPriorityBreakdown;
}

export interface AcademicTaskPriorityListResponse {
  items: AcademicTaskPriorityResponse[];
}

export interface AcademicTaskApiErrorResponse {
  error_code?: string;
  message?: string;
  detail?: unknown;
}

export interface AcademicTaskRequestOptions {
  signal?: AbortSignal;
}

export interface AcademicTaskListOptions
  extends AcademicTaskRequestOptions {
  limit?: number;
}