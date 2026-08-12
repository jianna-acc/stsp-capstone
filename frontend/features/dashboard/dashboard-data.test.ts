// File: /frontend/features/dashboard/dashboard-data.test.ts
// Purpose: Verifies Dashboard study-session selection behavior.

import {
  describe,
  expect,
  it,
} from "vitest";

import type {
  StudyPlan,
  StudySession,
} from "@/features/study-plans/types";

import {
  selectNextStudySession,
} from "./dashboard-data";


const plan:
  StudyPlan = {
    id:
      "plan-1",
    title:
      "Semester Study Plan",
    starts_on:
      "2026-08-01",
    ends_on:
      "2026-08-31",
    status:
      "active",
    generation_mode:
      "manual",
    generated_at:
      null,
    created_at:
      "2026-08-01T00:00:00.000Z",
    updated_at:
      "2026-08-01T00:00:00.000Z",
  };


function createSession(
  overrides:
    Partial<StudySession> = {},
): StudySession {
  return {
    id:
      "session-1",
    study_plan_id:
      plan.id,
    subject_id:
      "subject-1",
    title:
      "Database Review",
    starts_at:
      "2026-08-12T09:00:00.000Z",
    ends_at:
      "2026-08-12T10:00:00.000Z",
    status:
      "planned",
    origin:
      "manual",
    notes:
      null,
    created_at:
      "2026-08-01T00:00:00.000Z",
    updated_at:
      "2026-08-01T00:00:00.000Z",
    ...overrides,
  };
}


describe(
  "selectNextStudySession",
  () => {
    const now =
      new Date(
        "2026-08-12T08:00:00.000Z",
      );

    it(
      "returns the nearest future planned session",
      () => {
        const laterSession =
          createSession({
            id:
              "later",
            starts_at:
              "2026-08-12T11:00:00.000Z",
            ends_at:
              "2026-08-12T12:00:00.000Z",
          });

        const nextSession =
          createSession({
            id:
              "next",
            starts_at:
              "2026-08-12T09:00:00.000Z",
            ends_at:
              "2026-08-12T10:00:00.000Z",
          });

        const result =
          selectNextStudySession(
            [
              {
                plan,
                session:
                  laterSession,
              },
              {
                plan,
                session:
                  nextSession,
              },
            ],
            now,
          );

        expect(
          result?.session.id,
        ).toBe(
          "next",
        );
      },
    );

    it(
      "keeps an ongoing planned session eligible",
      () => {
        const ongoingSession =
          createSession({
            id:
              "ongoing",
            starts_at:
              "2026-08-12T07:30:00.000Z",
            ends_at:
              "2026-08-12T08:30:00.000Z",
          });

        const futureSession =
          createSession({
            id:
              "future",
            starts_at:
              "2026-08-12T09:00:00.000Z",
            ends_at:
              "2026-08-12T10:00:00.000Z",
          });

        const result =
          selectNextStudySession(
            [
              {
                plan,
                session:
                  futureSession,
              },
              {
                plan,
                session:
                  ongoingSession,
              },
            ],
            now,
          );

        expect(
          result?.session.id,
        ).toBe(
          "ongoing",
        );
      },
    );

    it(
      "ignores completed, skipped, and already-ended sessions",
      () => {
        const result =
          selectNextStudySession(
            [
              {
                plan,
                session:
                  createSession({
                    id:
                      "completed",
                    status:
                      "completed",
                  }),
              },
              {
                plan,
                session:
                  createSession({
                    id:
                      "skipped",
                    status:
                      "skipped",
                  }),
              },
              {
                plan,
                session:
                  createSession({
                    id:
                      "ended",
                    starts_at:
                      "2026-08-12T06:00:00.000Z",
                    ends_at:
                      "2026-08-12T07:00:00.000Z",
                  }),
              },
            ],
            now,
          );

        expect(
          result,
        ).toBeNull();
      },
    );

    it(
      "returns null when no usable session exists",
      () => {
        const result =
          selectNextStudySession(
            [],
            now,
          );

        expect(
          result,
        ).toBeNull();
      },
    );
  },
);