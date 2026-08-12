// File: /frontend/features/flashcards/types.ts
// Purpose: Defines Flashcard generation, saved-deck, source,
// filter-option, review, and API error contracts for the frontend.

export type FlashcardScopeType =
  | "subject"
  | "file";

export type FlashcardLocatorType =
  | "page"
  | "slide"
  | "sheet"
  | "section"
  | "document";

export interface FlashcardItem {
  question: string;
  answer: string;
}

export type FlashcardReviewOutcome =
  | "known"
  | "review_again";

export interface FlashcardReviewCreateRequest {
  card_position: number;
  outcome: FlashcardReviewOutcome;
}

export interface FlashcardReviewResponse {
  id: string;
  deck_id: string;
  card_position: number;
  outcome: FlashcardReviewOutcome;
  reviewed_at: string;
}

export interface FlashcardSource {
  study_file_id: string;
  source_name: string;
  chunk_index: number;
  locator_type:
    | FlashcardLocatorType
    | null;
  locator_label: string | null;
}

export interface FlashcardGenerateRequest {
  scope_type: FlashcardScopeType;
  subject_id: string;
  study_file_id?: string | null;
  card_count: number;
}

export interface FlashcardDeckResponse {
  id: string;
  subject_id: string;
  study_file_id: string | null;
  scope_type: FlashcardScopeType;
  title: string;
  requested_card_count: number;
  cards: FlashcardItem[];
  sources: FlashcardSource[];
  generation_model: string;
  generation_count: number;
  generated_at: string;
  created_at: string;
  updated_at: string;
}

export interface FlashcardDeckSummary {
  id: string;
  subject_id: string;
  study_file_id: string | null;
  scope_type: FlashcardScopeType;
  title: string;
  requested_card_count: number;
  generation_model: string;
  generation_count: number;
  generated_at: string;
  created_at: string;
  updated_at: string;
}

export interface FlashcardListResponse {
  items: FlashcardDeckSummary[];
}

export interface FlashcardApiErrorResponse {
  error_code?: string;
  message?: string;
  detail?: unknown;
}

export interface FlashcardSubjectOption {
  id: string;
  name: string;
}

export interface FlashcardFileOption {
  id: string;
  subjectId: string;
  originalFilename: string;
}

export interface FlashcardFilterOptions {
  subjects: FlashcardSubjectOption[];
  studyFiles: FlashcardFileOption[];
  loadError: string | null;
}