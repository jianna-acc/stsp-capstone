// File: /frontend/features/quizzes/types.ts
// Purpose: Defines Quiz generation, attempts, history, review,
// filter-option, response, and error contracts for the frontend.

export type QuizScopeType =
  | "subject"
  | "file";

export type QuizType =
  | "multiple_choice"
  | "true_false"
  | "identification"
  | "mixed";

export type QuizQuestionType =
  | "multiple_choice"
  | "true_false"
  | "identification";

export type QuizDifficulty =
  | "easy"
  | "medium"
  | "hard";

export type QuizAttemptStatus =
  | "in_progress"
  | "completed";


export interface QuizGenerateRequest {
  scope_type: QuizScopeType;

  subject_id: string;

  study_file_id?: string | null;

  quiz_type: QuizType;

  difficulty: QuizDifficulty;

  question_count: number;
}


export interface QuizQuestionResponse {
  id: string;

  position: number;

  question_type: QuizQuestionType;

  topic: string;

  question: string;

  choices: string[];
}


export interface QuizResponse {
  id: string;

  subject_id: string;

  study_file_id: string | null;

  scope_type: QuizScopeType;

  title: string;

  quiz_type: QuizType;

  difficulty: QuizDifficulty;

  question_count: number;

  questions: QuizQuestionResponse[];

  generation_model: string;

  generation_count: number;

  generated_at: string;

  created_at: string;

  updated_at: string;
}


export interface QuizAttemptResponse {
  id: string;

  quiz_id: string;

  status: QuizAttemptStatus;

  current_position: number;

  correct_count: number;

  question_count: number;

  score_percentage: number;

  started_at: string;

  completed_at: string | null;

  created_at: string;

  updated_at: string;
}


export interface QuizAnswerFeedbackResponse {
  attempt_id: string;

  quiz_question_id: string;

  position: number;

  is_correct: boolean;

  correct_answer: string;

  explanation: string;

  next_position: number | null;

  attempt_completed: boolean;
}


export interface QuizAnswerSubmissionResponse {
  attempt: QuizAttemptResponse;

  feedback: QuizAnswerFeedbackResponse;
}


export interface QuizTopicResult {
  topic: string;

  correct_count: number;

  question_count: number;

  accuracy_percentage: number;
}


export interface QuizAttemptResultResponse {
  attempt_id: string;

  quiz_id: string;

  correct_count: number;

  question_count: number;

  score_percentage: number;

  strong_topics: QuizTopicResult[];

  weak_topics: QuizTopicResult[];

  completed_at: string;
}


export interface QuizSummaryResponse {
  id: string;

  subject_id: string;

  study_file_id: string | null;

  scope_type: QuizScopeType;

  title: string;

  quiz_type: QuizType;

  difficulty: QuizDifficulty;

  question_count: number;

  attempt_count: number;

  latest_attempt: QuizAttemptResponse | null;

  generated_at: string;

  created_at: string;

  updated_at: string;
}


export interface QuizListResponse {
  items: QuizSummaryResponse[];
}


export interface QuizAttemptListResponse {
  quiz_id: string;

  items: QuizAttemptResponse[];
}


export interface QuizAttemptReviewAnswerResponse {
  answer_id: string;

  question: QuizQuestionResponse;

  submitted_answer: string;

  is_correct: boolean;

  correct_answer: string;

  explanation: string;

  answered_at: string;
}


export interface QuizAttemptReviewResponse {
  attempt: QuizAttemptResponse;

  answers: QuizAttemptReviewAnswerResponse[];

  result: QuizAttemptResultResponse;
}


export interface QuizApiErrorResponse {
  error_code?: string;

  message?: string;

  detail?: unknown;
}


export interface QuizSubjectOption {
  id: string;

  name: string;
}


export interface QuizFileOption {
  id: string;

  subjectId: string;

  originalFilename: string;
}


export interface QuizFilterOptions {
  subjects: QuizSubjectOption[];

  studyFiles: QuizFileOption[];

  loadError: string | null;
}