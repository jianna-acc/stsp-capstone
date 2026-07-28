// File: /frontend/features/auth/validation.ts
// Purpose: Reads and validates authentication FormData without
// returning password values to the user interface.

import {
  DEFAULT_AFTER_LOGIN_PATH,
  getSafeInternalPath,
} from "./redirects";
import type {
  LoginFieldErrors,
  LoginFormValues,
  RegistrationFieldErrors,
  RegistrationFormValues,
  ValidatedLoginInput,
  ValidatedRegistrationInput,
} from "./types";

const EMAIL_PATTERN =
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const PASSWORD_LETTER_PATTERN = /[A-Za-z]/;
const PASSWORD_NUMBER_PATTERN = /\d/;

// ============================================================
// Shared helpers
// ============================================================

function getTextValue(
  formData: FormData,
  fieldName: string,
): string {
  const value = formData.get(fieldName);

  return typeof value === "string"
    ? value.trim()
    : "";
}

function getPasswordValue(
  formData: FormData,
  fieldName: string,
): string {
  const value = formData.get(fieldName);

  /*
   * Passwords are intentionally not trimmed.
   *
   * Spaces may be part of a student's password and changing
   * them would make valid credentials fail unexpectedly.
   */
  return typeof value === "string"
    ? value
    : "";
}

// ============================================================
// Registration validation
// ============================================================

export interface RegistrationValidationResult {
  values: RegistrationFormValues;
  input: ValidatedRegistrationInput;
  errors: RegistrationFieldErrors;
}

export function validateRegistrationForm(
  formData: FormData,
): RegistrationValidationResult {
  const fullName = getTextValue(
    formData,
    "fullName",
  );

  const email = getTextValue(
    formData,
    "email",
  ).toLowerCase();

  const password = getPasswordValue(
    formData,
    "password",
  );

  const confirmPassword = getPasswordValue(
    formData,
    "confirmPassword",
  );

  const termsAccepted =
    formData.get("terms") === "on";

  const errors: RegistrationFieldErrors = {};

  if (!fullName) {
    errors.fullName =
      "Enter your full name.";
  } else if (fullName.length < 2) {
    errors.fullName =
      "Your name must contain at least two characters.";
  } else if (fullName.length > 120) {
    errors.fullName =
      "Your name cannot exceed 120 characters.";
  }

  if (!email) {
    errors.email =
      "Enter your email address.";
  } else if (!EMAIL_PATTERN.test(email)) {
    errors.email =
      "Enter a valid email address.";
  } else if (email.length > 254) {
    errors.email =
      "Your email address is too long.";
  }

  if (!password) {
    errors.password =
      "Create a password.";
  } else if (password.length < 8) {
    errors.password =
      "Use at least eight characters.";
  } else if (
    !PASSWORD_LETTER_PATTERN.test(password)
  ) {
    errors.password =
      "Include at least one letter.";
  } else if (
    !PASSWORD_NUMBER_PATTERN.test(password)
  ) {
    errors.password =
      "Include at least one number.";
  }

  if (!confirmPassword) {
    errors.confirmPassword =
      "Confirm your password.";
  } else if (password !== confirmPassword) {
    errors.confirmPassword =
      "The passwords do not match.";
  }

  if (!termsAccepted) {
    errors.terms =
      "Confirm that you agree to the platform rules.";
  }

  return {
    values: {
      fullName,
      email,
      termsAccepted,
    },
    input: {
      fullName,
      email,
      password,
    },
    errors,
  };
}

export function hasRegistrationErrors(
  errors: RegistrationFieldErrors,
): boolean {
  return Object.keys(errors).length > 0;
}

// ============================================================
// Login validation
// ============================================================

export interface LoginValidationResult {
  values: LoginFormValues;
  input: ValidatedLoginInput;
  errors: LoginFieldErrors;
}

export function validateLoginForm(
  formData: FormData,
): LoginValidationResult {
  const email = getTextValue(
    formData,
    "email",
  ).toLowerCase();

  const password = getPasswordValue(
    formData,
    "password",
  );

  const nextPath = getSafeInternalPath(
    getTextValue(formData, "next"),
    DEFAULT_AFTER_LOGIN_PATH,
  );

  const errors: LoginFieldErrors = {};

  if (!email) {
    errors.email =
      "Enter your email address.";
  } else if (!EMAIL_PATTERN.test(email)) {
    errors.email =
      "Enter a valid email address.";
  } else if (email.length > 254) {
    errors.email =
      "Your email address is too long.";
  }

  if (!password) {
    errors.password =
      "Enter your password.";
  }

  return {
    values: {
      email,
      nextPath,
    },
    input: {
      email,
      password,
      nextPath,
    },
    errors,
  };
}

export function hasLoginErrors(
  errors: LoginFieldErrors,
): boolean {
  return Object.keys(errors).length > 0;
}