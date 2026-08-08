// File: /frontend/features/reviewers/types.ts
// Purpose: Defines reviewer generation, response, source,
// filter-option, and error contracts for the Reviewer frontend.

export type ReviewerScopeType =
  | "subject"
  | "file";

export type ReviewerLength =
  | "short"
  | "medium"
  | "long";

export type ReviewerLocatorType =
  | "page"
  | "slide"
  | "sheet"
  | "section"
  | "document";

export interface ReviewerDefinition {
  term: string;
  definition: string;
}

export interface ReviewerTopic {
  title: string;
  summary: string;
  key_points: string[];
  definitions: ReviewerDefinition[];
}

export interface ReviewerContent {
  overview: string;
  topics: ReviewerTopic[];
}

export interface ReviewerSource {
  study_file_id: string;
  source_name: string;
  chunk_index: number;
  locator_type:
    | ReviewerLocatorType
    | null;
  locator_label: string | null;
}

export interface ReviewerGenerateRequest {
  scope_type: ReviewerScopeType;
  subject_id: string;
  study_file_id?: string | null;
  reviewer_length: ReviewerLength;
}

export interface ReviewerResponse {
  id: string;
  subject_id: string;
  study_file_id: string | null;
  scope_type: ReviewerScopeType;
  title: string;
  reviewer_length: ReviewerLength;
  content: ReviewerContent;
  sources: ReviewerSource[];
  generation_model: string;
  generation_count: number;
  generated_at: string;
  created_at: string;
  updated_at: string;
}

export interface ReviewerListResponse {
  items: ReviewerResponse[];
}

export interface ReviewerApiErrorResponse {
  error_code?: string;
  message?: string;
  detail?: unknown;
}

export interface ReviewerSubjectOption {
  id: string;
  name: string;
}

export interface ReviewerFileOption {
  id: string;
  subjectId: string;
  originalFilename: string;
}

export interface ReviewerFilterOptions {
  subjects: ReviewerSubjectOption[];
  studyFiles: ReviewerFileOption[];
  loadError: string | null;
}