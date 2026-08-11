// File: /frontend/features/academic-tasks/priority-presentation.ts
// Purpose: Converts deterministic Academic Task priority scores
// into consistent frontend labels and presentation metadata.

export type AcademicTaskPriorityLevel =
  | "highest"
  | "high"
  | "medium"
  | "low";

export interface AcademicTaskPriorityPresentation {
  level: AcademicTaskPriorityLevel;
  label: string;
  color: string;
}

export function getAcademicTaskPriorityPresentation(
  score: number,
): AcademicTaskPriorityPresentation {
  if (score >= 75) {
    return {
      level: "highest",
      label: "Highest priority",
      color: "red",
    };
  }

  if (score >= 50) {
    return {
      level: "high",
      label: "High priority",
      color: "orange",
    };
  }

  if (score >= 25) {
    return {
      level: "medium",
      label: "Medium priority",
      color: "yellow",
    };
  }

  return {
    level: "low",
    label: "Low priority",
    color: "green",
  };
}

export function formatAcademicTaskPriorityScore(
  score: number,
): string {
  return `${score.toFixed(1)}/100`;
}