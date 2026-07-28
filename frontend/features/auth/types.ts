// File: /frontend/features/auth/types.ts
// Purpose: Defines serializable form values, validation errors,
// and Server Action results shared by authentication features.

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