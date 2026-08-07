// File: /frontend/types/study-conversation.ts
// Purpose: Defines frontend contracts for saved Study
// Assistant conversations, messages, and controlled errors.

import type {
  RagAnswerOutcome,
  RagSourceResponse,
} from "@/types/rag";

export type StudyMessageRole =
  | "user"
  | "assistant";

export type StudyMessageOutcome =
  RagAnswerOutcome;

export interface StudyConversationResponse {
  id: string;
  title: string;
  subject_id: string | null;
  study_file_id: string | null;
  created_at: string;
  updated_at: string;
  last_message_at: string;
}

export interface StudyMessageResponse {
  id: string;
  conversation_id: string;
  role: StudyMessageRole;
  content: string;
  outcome: StudyMessageOutcome | null;
  sources: RagSourceResponse[];
  created_at: string;
}

export interface StudyConversationListResponse {
  items: StudyConversationResponse[];
}

export interface StudyConversationDetailResponse {
  conversation: StudyConversationResponse;
  messages: StudyMessageResponse[];
}

export interface StudyConversationApiErrorResponse {
  error_code?: string;
  code?: string;
  message?: string;
  detail?: unknown;
}
