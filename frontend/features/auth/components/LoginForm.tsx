// File: /frontend/features/auth/components/LoginForm.tsx
// Purpose: Displays the email-and-password login form and
// connects it to the password-login Server Action.

"use client";

import { useActionState } from "react";

import {
  Alert,
  Button,
  PasswordInput,
  Stack,
  TextInput,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconLogin2,
} from "@tabler/icons-react";

import { loginAction } from "@/features/auth/actions/login";
import {
  initialLoginActionState,
  type LoginActionState,
} from "@/features/auth/types";

interface LoginFormProps {
  nextPath: string;
}

export function LoginForm({
  nextPath,
}: Readonly<LoginFormProps>) {
  const initialState: LoginActionState = {
    ...initialLoginActionState,
    values: {
      ...initialLoginActionState.values,
      nextPath,
    },
  };

  const [
    state,
    formAction,
    isPending,
  ] = useActionState(
    loginAction,
    initialState,
  );

  return (
    <form
      action={formAction}
      noValidate
    >
      <input
        name="next"
        type="hidden"
        value={
          state.values.nextPath ||
          nextPath
        }
      />

      <Stack gap="md">
        {state.status === "error" && (
          <Alert
            color="red"
            icon={
              <IconAlertCircle size={18} />
            }
            title="Sign-in needs attention"
          >
            {state.message}
          </Alert>
        )}

        <TextInput
          autoCapitalize="none"
          autoComplete="email"
          autoFocus
          defaultValue={state.values.email}
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
          autoComplete="current-password"
          disabled={isPending}
          error={
            state.fieldErrors.password
          }
          label="Password"
          name="password"
          placeholder="Enter your password"
          required
          size="md"
        />

        <Button
          fullWidth
          leftSection={
            <IconLogin2 size={18} />
          }
          loading={isPending}
          size="md"
          type="submit"
        >
          Sign in
        </Button>
      </Stack>
    </form>
  );
}