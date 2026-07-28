// File: /frontend/features/auth/validation.ts
// Purpose: Reads and validates registration FormData without
// returning password values to the user interface.

import type {
  RegistrationFieldErrors,
  RegistrationFormValues,
  ValidatedRegistrationInput,
} from "./types";

const EMAIL_PATTERN =
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const PASSWORD_LETTER_PATTERN = /[A-Za-z]/;
const PASSWORD_NUMBER_PATTERN = /\d/;

export interface RegistrationValidationResult {
  values: RegistrationFormValues;
  input: ValidatedRegistrationInput;
  errors: RegistrationFieldErrors;
}

function getTextValue(
  formData: FormData,
  fieldName: string,
): string {
  const value = formData.get(fieldName);

  return typeof value === "string"
    ? value.trim()
    : "";
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

  const password = getTextValue(
    formData,
    "password",
  );

  const confirmPassword = getTextValue(
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