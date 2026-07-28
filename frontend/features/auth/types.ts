// File: /frontend/features/auth/types.ts
// Purpose: Defines serializable form values, validation errors,
// and Server Action results shared by authentication features.

// ============================================================
// Registration types
// ============================================================

export interface RegistrationFormValues {
  fullName: string;
  email: string;
  termsAccepted: boolean;
}

export interface RegistrationFieldErrors {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  terms?: string;
}

export interface RegisterActionState {
  status: "idle" | "error";
  message: string;
  fieldErrors: RegistrationFieldErrors;
  values: RegistrationFormValues;
}

export interface ValidatedRegistrationInput {
  fullName: string;
  email: string;
  password: string;
}

export const initialRegisterActionState:
  RegisterActionState = {
    status: "idle",
    message: "",
    fieldErrors: {},
    values: {
      fullName: "",
      email: "",
      termsAccepted: false,
    },
  };

// ============================================================
// Login types
// ============================================================

export interface LoginFormValues {
  email: string;
  nextPath: string;
}

export interface LoginFieldErrors {
  email?: string;
  password?: string;
}

export interface LoginActionState {
  status: "idle" | "error";
  message: string;
  fieldErrors: LoginFieldErrors;
  values: LoginFormValues;
}

export interface ValidatedLoginInput {
  email: string;
  password: string;
  nextPath: string;
}

export const initialLoginActionState:
  LoginActionState = {
    status: "idle",
    message: "",
    fieldErrors: {},
    values: {
      email: "",
      nextPath: "/dashboard",
    },
  };