// File: /frontend/features/learning-profile/server/errors.ts
// Purpose: Defines safe internal error categories for the
// server-side learning-profile data layer.

export type LearningProfileDataErrorCode =
  | "UNAUTHENTICATED"
  | "PROFILE_NOT_FOUND"
  | "QUERY_FAILED"
  | "MUTATION_FAILED"
  | "ONBOARDING_INCOMPLETE";

export class LearningProfileDataError
  extends Error {
  readonly code:
    LearningProfileDataErrorCode;

  constructor(
    code: LearningProfileDataErrorCode,
    message: string,
    options?: ErrorOptions,
  ) {
    super(message, options);

    this.name =
      "LearningProfileDataError";

    this.code = code;
  }
}