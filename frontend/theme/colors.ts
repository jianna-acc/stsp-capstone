// File: /frontend/theme/colors.ts
// Purpose: Stores the shared brand palette and application color tokens.

import type { MantineColorsTuple } from "@mantine/core";

/**
 * Mantine palettes require ten shades.
 *
 * Index 0 is the lightest shade.
 * Index 9 is the darkest shade.
 */
export const brandColors: MantineColorsTuple = [
  "#F8F5FF",
  "#F2ECFF",
  "#E9DFFF",
  "#DCCBFF",
  "#C4A5FF",
  "#9F72F7",
  "#7C3AED",
  "#6D28D9",
  "#5B21B6",
  "#4C1D95",
];

/**
 * Application colors used outside Mantine component props,
 * such as CSS Modules and custom visualizations.
 */
export const appColors = {
  primary: "#7C3AED",
  primaryDark: "#5B21B6",
  primarySoft: "#F2ECFF",
  background: "#F7F7FA",
  card: "#FFFFFF",
  text: "#18181B",
  textSecondary: "#71717A",
  success: "#22A06B",
  warning: "#F59E0B",
  danger: "#DC2626",
  border: "#E8E8EE",
} as const;