// File: /frontend/types/rag.ts
// Purpose: Defines the public request, answer, source,
// filter-option, and error contracts used by the frontend
// Study Assistant.

export type RagAnswerOutcome =
  | "answered"
  | "no_context";

export interface RagAnswerRequest {
  question: string;
  study_file_id?: string;
  subject_id?: string;
  match_count?: number;
  similarity_threshold?: number;
}

export interface RagSourceResponse {
  source_number: number;
  source_name: string;
  chunk_index: number;
  similarity_score: number;
}

export interface RagAnswerResponse {
  outcome: RagAnswerOutcome;
  answer: string;
  sources: RagSourceResponse[];
  retrieved_count: number;
  source_count: number;
  context_available: boolean;
}

export interface RagApiErrorResponse {
  code?: string;
  message?: string;
  detail?: unknown;
}

export interface StudyAssistantSubjectOption {
  id: string;
  name: string;
}

export interface StudyAssistantFileOption {
  id: string;
  subjectId: string;
  originalFilename: string;
}

export interface StudyAssistantFilterOptions {
  subjects: StudyAssistantSubjectOption[];
  studyFiles: StudyAssistantFileOption[];
  loadError: string | null;
}