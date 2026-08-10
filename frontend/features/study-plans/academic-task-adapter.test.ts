// File: /frontend/features/study-plans/academic-task-adapter.test.ts
// Purpose: Tests conversion from prioritized Academic Tasks
// into Track D scheduler tasks.

import {
  describe,
  expect,
  it,
} from "vitest";

import {
  academicTasksToSchedulableTasks,
  academicTaskToSchedulableTask,
  priorityScoreToWeight,
} from "./academic-task-adapter";


describe(
  "academic task adapter",
  () => {
    it(
      "converts priority scores into scheduler weights",
      () => {
        expect(
          priorityScoreToWeight(
            0,
          ),
        ).toBe(
          1,
        );

        expect(
          priorityScoreToWeight(
            20,
          ),
        ).toBe(
          1,
        );

        expect(
          priorityScoreToWeight(
            21,
          ),
        ).toBe(
          2,
        );

        expect(
          priorityScoreToWeight(
            60,
          ),
        ).toBe(
          3,
        );

        expect(
          priorityScoreToWeight(
            80,
          ),
        ).toBe(
          4,
        );

        expect(
          priorityScoreToWeight(
            100,
          ),
        ).toBe(
          5,
        );
      },
    );


    it(
      "converts a pending academic task",
      () => {
        const result =
          academicTaskToSchedulableTask({
            task: {
              id:
                "task-1",
              subject_id:
                "subject-1",
              title:
                "Finish research paper",
              deadline:
                "2026-08-20T23:59:00+08:00",
              estimated_minutes:
                360,
              status:
                "pending",
            },
            priority: {
              total_score:
                87,
            },
          });

        expect(
          result,
        ).toEqual({
          task_id:
            "task-1",
          subject_id:
            "subject-1",
          title:
            "Finish research paper",
          deadline:
            "2026-08-20T23:59:00+08:00",
          estimated_minutes:
            360,
          priority_weight:
            5,
        });
      },
    );


    it(
      "keeps in-progress tasks schedulable",
      () => {
        const result =
          academicTaskToSchedulableTask({
            task: {
              id:
                "task-2",
              subject_id:
                "subject-1",
              title:
                "Study for exam",
              deadline:
                "2026-08-18T08:00:00+08:00",
              estimated_minutes:
                180,
              status:
                "in_progress",
            },
            priority: {
              total_score:
                72,
            },
          });

        expect(
          result?.priority_weight,
        ).toBe(
          4,
        );
      },
    );


    it(
      "excludes completed and cancelled tasks",
      () => {
        const result =
          academicTasksToSchedulableTasks([
            {
              task: {
                id:
                  "pending-task",
                subject_id:
                  "subject-1",
                title:
                  "Pending task",
                deadline:
                  "2026-08-20T12:00:00+08:00",
                estimated_minutes:
                  60,
                status:
                  "pending",
              },
              priority: {
                total_score:
                  50,
              },
            },
            {
              task: {
                id:
                  "completed-task",
                subject_id:
                  "subject-1",
                title:
                  "Completed task",
                deadline:
                  "2026-08-20T12:00:00+08:00",
                estimated_minutes:
                  60,
                status:
                  "completed",
              },
              priority: {
                total_score:
                  90,
              },
            },
            {
              task: {
                id:
                  "cancelled-task",
                subject_id:
                  "subject-1",
                title:
                  "Cancelled task",
                deadline:
                  "2026-08-20T12:00:00+08:00",
                estimated_minutes:
                  60,
                status:
                  "cancelled",
              },
              priority: {
                total_score:
                  90,
              },
            },
          ]);

        expect(
          result,
        ).toHaveLength(
          1,
        );

        expect(
          result[0]
            ?.task_id,
        ).toBe(
          "pending-task",
        );
      },
    );
  },
);