// File: /frontend/features/academic-tasks/components/AcademicTaskPriorityBreakdown.tsx
// Purpose: Explains the deterministic factor scores that contribute
// to an Academic Task's priority calculation.

"use client";

import {
  Button,
  Collapse,
  Group,
  Progress,
  Stack,
  Text,
} from "@mantine/core";
import {
  useDisclosure,
} from "@mantine/hooks";
import {
  IconChevronDown,
  IconChevronUp,
  IconInfoCircle,
} from "@tabler/icons-react";

import type {
  AcademicTaskPriorityBreakdown as AcademicTaskPriorityBreakdownData,
} from "../types";

interface AcademicTaskPriorityBreakdownProps {
  taskTitle: string;
  priority: AcademicTaskPriorityBreakdownData;
}

interface PriorityFactor {
  label: string;
  description: string;
  score: number;
}

function getPriorityFactors(
  priority: AcademicTaskPriorityBreakdownData,
): PriorityFactor[] {
  return [
    {
      label:
        "Deadline proximity",
      description:
        "Tasks with closer or overdue deadlines receive more priority pressure.",
      score:
        priority.deadline_score,
    },
    {
      label:
        "Difficulty",
      description:
        "More difficult tasks receive more priority pressure.",
      score:
        priority.difficulty_score,
    },
    {
      label:
        "Estimated completion time",
      description:
        "Tasks requiring more estimated work receive more priority pressure.",
      score:
        priority.estimated_time_score,
    },
    {
      label:
        "Output confidence",
      description:
        "Lower confidence in the task's required academic output raises priority pressure.",
      score:
        priority.output_confidence_score,
    },
    {
      label:
        "Previous performance",
      description:
        "Lower previous performance raises priority pressure when performance data is available.",
      score:
        priority.previous_performance_score,
    },
    {
      label:
        "Available study time",
      description:
        "Less available study time relative to the task workload raises priority pressure.",
      score:
        priority.available_study_time_score,
    },
    {
      label:
        "Task status",
      description:
        "The task's current status affects how urgently it should be prioritized.",
      score:
        priority.status_score,
    },
  ];
}

function formatFactorScore(
  score: number,
): string {
  return `${score.toFixed(1)}/100`;
}

export function AcademicTaskPriorityBreakdown({
  taskTitle,
  priority,
}: AcademicTaskPriorityBreakdownProps) {
  const [
    opened,
    {
      toggle,
    },
  ] =
    useDisclosure(false);

  const factors =
    getPriorityFactors(
      priority,
    );

  return (
    <Stack gap="xs">
      <Button
        variant="subtle"
        size="compact-sm"
        justify="space-between"
        leftSection={
          <IconInfoCircle
            size={16}
          />
        }
        rightSection={
          opened ? (
            <IconChevronUp
              size={16}
            />
          ) : (
            <IconChevronDown
              size={16}
            />
          )
        }
        aria-expanded={
          opened
        }
        aria-controls={
          `priority-breakdown-${taskTitle}`
        }
        onClick={
          toggle
        }
      >
        Why this priority?
      </Button>

        <Collapse
        expanded={opened}
        >
        <Stack
          id={
            `priority-breakdown-${taskTitle}`
          }
          gap="sm"
          pt="xs"
        >
          <Text
            size="xs"
            c="dimmed"
          >
            Each factor is scored from
            0 to 100. A higher factor
            score means that factor
            pushes this task higher in
            the priority ranking.
          </Text>

          {factors.map(
            (
              factor,
            ) => (
              <Stack
                key={
                  factor.label
                }
                gap={4}
              >
                <Group
                  justify="space-between"
                  gap="xs"
                >
                  <Text
                    size="sm"
                    fw={600}
                  >
                    {factor.label}
                  </Text>

                  <Text
                    size="xs"
                    fw={700}
                  >
                    {formatFactorScore(
                      factor.score,
                    )}
                  </Text>
                </Group>

                <Progress
                  value={
                    factor.score
                  }
                  size="xs"
                  radius="xl"
                  aria-label={
                    `${factor.label} priority factor for ${taskTitle}`
                  }
                />

                <Text
                  size="xs"
                  c="dimmed"
                >
                  {factor.description}
                </Text>
              </Stack>
            ),
          )}
        </Stack>
      </Collapse>
    </Stack>
  );
}