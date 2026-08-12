// File: /frontend/features/dashboard/dashboard-data.ts
// Purpose: Provides pure presentation helpers for selecting
// Dashboard study-plan information without duplicating backend logic.

import type {
  StudyPlan,
  StudySession,
} from "@/features/study-plans/types";


export interface DashboardStudySessionCandidate {
  plan: StudyPlan;
  session: StudySession;
}


function getTimestamp(
  value: string,
): number | null {
  const timestamp =
    new Date(
      value,
    ).getTime();

  return Number.isNaN(
    timestamp,
  )
    ? null
    : timestamp;
}


export function selectNextStudySession(
  candidates:
    readonly DashboardStudySessionCandidate[],
  now:
    Date = new Date(),
): DashboardStudySessionCandidate | null {
  const nowTimestamp =
    now.getTime();

  if (
    Number.isNaN(
      nowTimestamp,
    )
  ) {
    return null;
  }

  const eligibleCandidates =
    candidates
      .map(
        (
          candidate,
        ) => {
          const startTimestamp =
            getTimestamp(
              candidate.session.starts_at,
            );

          const endTimestamp =
            getTimestamp(
              candidate.session.ends_at,
            );

          return {
            candidate,
            startTimestamp,
            endTimestamp,
          };
        },
      )
      .filter(
        (
          item,
        ): item is {
          candidate:
            DashboardStudySessionCandidate;
          startTimestamp: number;
          endTimestamp: number;
        } =>
          item.candidate
            .session.status ===
            "planned" &&
          item.startTimestamp !==
            null &&
          item.endTimestamp !==
            null &&
          item.endTimestamp >
            nowTimestamp,
      )
      .sort(
        (
          left,
          right,
        ) =>
          left.startTimestamp -
          right.startTimestamp,
      );

  return (
    eligibleCandidates[0]
      ?.candidate ??
    null
  );
}