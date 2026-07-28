// File: /frontend/features/auth/components/RegisterForm.tsx
// Purpose: Displays the registration fields and connects them
// to the registration Server Action.

"use client";

import {
  useActionState,
} from "react";

import {
  Alert,
  Button,
  Checkbox,
  PasswordInput,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconUserPlus,
} from "@tabler/icons-react";

import {
  registerAction,
} from "@/features/auth/actions/register";
import {
  initialRegisterActionState,
} from "@/features/auth/types";

import classes from "./RegisterForm.module.css";

export function RegisterForm() {
  const [
    state,
    formAction,
    isPending,
  ] = useActionState(
    registerAction,
    initialRegisterActionState,
  );

  return (
    <form
      action={formAction}
      className={classes.form}
      noValidate
    >
      <Stack gap="md">
        {state.status === "error" && (
          <Alert
            color="red"
            icon={
              <IconAlertCircle size={18} />
            }
            title="Registration needs attention"
          >
            {state.message}
          </Alert>
        )}

        <TextInput
          autoComplete="name"
          defaultValue={
            state.values.fullName
          }
          disabled={isPending}
          error={
            state.fieldErrors.fullName
          }
          label="Full name"
          name="fullName"
          placeholder="Enter your full name"
          required
          size="md"
        />

        <TextInput
          autoCapitalize="none"
          autoComplete="email"
          defaultValue={
            state.values.email
          }
          disabled={isPending}
          error={state.fieldErrors.email}
          inputMode="email"
          label="Email address"
          name="email"
          placeholder="student@example.com"
          required
          size="md"
          type="email"
        />

        <PasswordInput
          autoComplete="new-password"
          disabled={isPending}
          error={
            state.fieldErrors.password
          }
          label="Password"
          name="password"
          placeholder="Create a secure password"
          required
          size="md"
        />

        <Text className={classes.passwordHint}>
          Use at least eight characters with
          at least one letter and one number.
        </Text>

        <PasswordInput
          autoComplete="new-password"
          disabled={isPending}
          error={
            state.fieldErrors
              .confirmPassword
          }
          label="Confirm password"
          name="confirmPassword"
          placeholder="Enter your password again"
          required
          size="md"
        />

        <Checkbox
          defaultChecked={
            state.values.termsAccepted
          }
          disabled={isPending}
          label="I agree to follow the platform's acceptable-use and academic-integrity rules."
          name="terms"
          size="sm"
        />

        {state.fieldErrors.terms && (
          <Text
            className={classes.termsError}
          >
            {state.fieldErrors.terms}
          </Text>
        )}

        <Button
          fullWidth
          leftSection={
            <IconUserPlus size={18} />
          }
          loading={isPending}
          size="md"
          type="submit"
        >
          Create account
        </Button>
      </Stack>
    </form>
  );
}