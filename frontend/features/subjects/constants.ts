// File: /frontend/features/subjects/constants.ts
// Purpose: Defines the subject colors supported by the
// Mantine interface and the database validation layer.

export const SUBJECT_COLORS = [
  "violet",
  "grape",
  "indigo",
  "blue",
  "cyan",
  "teal",
  "green",
  "lime",
  "yellow",
  "orange",
  "red",
  "pink",
] as const;

export type SubjectColor =
  (typeof SUBJECT_COLORS)[number];

export const SUBJECT_COLOR_OPTIONS =
  SUBJECT_COLORS.map((color) => ({
    value: color,
    label:
      color.charAt(0).toUpperCase() +
      color.slice(1),
  }));

export const DEFAULT_SUBJECT_COLOR: SubjectColor =
  "violet";