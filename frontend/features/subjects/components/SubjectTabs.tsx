// File: /frontend/features/subjects/components/SubjectTabs.tsx
// Purpose: Lets students switch between subject workspaces
// while keeping file management inside the Subjects feature.

"use client";

import {
  ColorSwatch,
  Group,
  ScrollArea,
  Tabs,
  Text,
} from "@mantine/core";
import { useRouter } from "next/navigation";

import type { SubjectSummary } from "../types";

interface SubjectTabsProps {
  subjects: SubjectSummary[];
  activeSubjectId: string;
}

export function SubjectTabs({
  subjects,
  activeSubjectId,
}: SubjectTabsProps) {
  const router = useRouter();

  return (
    <ScrollArea
      type="auto"
      offsetScrollbars
    >
      <Tabs
        value={activeSubjectId}
        variant="pills"
        onChange={(subjectId) => {
          if (!subjectId) {
            return;
          }

          router.push(
            `/subjects/${subjectId}`,
          );
        }}
      >
        <Tabs.List
          style={{
            flexWrap: "nowrap",
            minWidth: "max-content",
          }}
        >
          {subjects.map((subject) => (
            <Tabs.Tab
              key={subject.id}
              value={subject.id}
              leftSection={
                <ColorSwatch
                  size={11}
                  color={`var(--mantine-color-${subject.color}-6)`}
                />
              }
            >
              <Group gap={6}>
                <Text
                  component="span"
                  size="sm"
                  fw={600}
                >
                  {subject.name}
                </Text>
              </Group>
            </Tabs.Tab>
          ))}
        </Tabs.List>
      </Tabs>
    </ScrollArea>
  );
}