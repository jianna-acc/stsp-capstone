// File: /frontend/features/study-plans/academic-task-adapter.test.ts
// Purpose: Tests conversion from real prioritized Academic Tasks
// into Track D schedulable tasks.

import {
  describe,
  expect,
  it,
} from "vitest";

import type {
  AcademicTaskPriorityResponse,
  AcademicTaskStatus,
} from "@/features/academic-tasks/types";

import {
  academicTasksToSchedulableTasks,
  academicTaskToSchedulableTask,
  priorityScoreToWeight,
} from "./academic-task-adapter";


function createPriorityItem({
  id = "11111111-1111-4111-8111-111111111111",
  status = "pending",
  totalScore = 50,
}: {
  id?: string;
  status?: AcademicTaskStatus;
  totalScore?: number;
} = {}): AcademicTaskPriorityResponse {
  return {
    task: {
      id,
      subject_id:
        "22222222-2222-4222-8222-222222222222",
      title:
        "Study for Biology exam",
      description:
        null,
      deadline:
        "2026-08-20T18:00:00+08:00",
      estimated_minutes:
        180,
      difficulty:
        "hard",
      task_type:
        "exam",
      output_type:
        "memorization",
      status,
      created_at:
        "2026-08-10T08:00:00Z",
      updated_at:
        "2026-08-10T08:00:00Z",
    },

    priority: {
      total_score:
        totalScore,
      deadline_score:
        80,
      difficulty_score:
        100,
      estimated_time_score:
        50,
      output_confidence_score:
        50,
      previous_performance_score:
        50,
      available_study_time_score:
        50,
      status_score:
        50,
    },
  };
}


describe(
  "academic task adapter",
  () => {
    it(
      "converts priority scores into scheduler weights",
      () => {
        expect(
          priorityScoreToWeight(0),
        ).toBe(1);

        expect(
          priorityScoreToWeight(20),
        ).toBe(1);

        expect(
          priorityScoreToWeight(21),
        ).toBe(2);

        expect(
          priorityScoreToWeight(60),
        ).toBe(3);

        expect(
          priorityScoreToWeight(80),
        ).toBe(4);

        expect(
          priorityScoreToWeight(100),
        ).toBe(5);
      },
    );


    it(
      "converts a pending academic task",
      () => {
        const result =
          academicTaskToSchedulableTask(
            createPriorityItem({
              totalScore:
                87,
            }),
          );

        expect(
          result,
        ).toEqual({
          task_id:
            "11111111-1111-4111-8111-111111111111",
          subject_id:
            "22222222-2222-4222-8222-222222222222",
          title:
            "Study for Biology exam",
          deadline:
            "2026-08-20T18:00:00+08:00",
          estimated_minutes:
            180,
          priority_weight:
            5,
        });
      },
    );


    it(
      "keeps in-progress tasks schedulable",
      () => {
        const result =
          academicTaskToSchedulableTask(
            createPriorityItem({
              status:
                "in_progress",
              totalScore:
                72,
            }),
          );

        expect(
          result?.priority_weight,
        ).toBe(4);
      },
    );


    it(
      "excludes completed and cancelled tasks",
      () => {
        const result =
          academicTasksToSchedulableTasks([
            createPriorityItem({
              id:
                "11111111-1111-4111-8111-111111111111",
              status:
                "pending",
            }),
            createPriorityItem({
              id:
                "33333333-3333-4333-8333-333333333333",
              status:
                "completed",
            }),
            createPriorityItem({
              id:
                "44444444-4444-4444-8444-444444444444",
              status:
                "cancelled",
            }),
          ]);

        expect(
          result,
        ).toHaveLength(1);

        expect(
          result[0]?.task_id,
        ).toBe(
          "11111111-1111-4111-8111-111111111111",
        );
      },
    );
  },
);