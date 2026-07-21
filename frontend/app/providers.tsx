// File: /frontend/app/providers.tsx
// Purpose: Provides the Mantine theme, notifications, and modal
// management to every page in the application.

"use client";

import { MantineProvider } from "@mantine/core";
import { ModalsProvider } from "@mantine/modals";
import { Notifications } from "@mantine/notifications";

import { theme } from "@/theme/theme";

type ProvidersProps = Readonly<{
  children: React.ReactNode;
}>;

export function Providers({
  children,
}: ProvidersProps) {
  return (
    <MantineProvider
      theme={theme}
      defaultColorScheme="light"
    >
      <ModalsProvider
        labels={{
          confirm: "Confirm",
          cancel: "Cancel",
        }}
      >
        <Notifications
          position="top-right"
          limit={3}
        />

        {children}
      </ModalsProvider>
    </MantineProvider>
  );
}