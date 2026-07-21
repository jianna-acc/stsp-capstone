// File: /frontend/theme/theme.ts
// Purpose: Combines the color palette, typography, shapes, shadows,
// and component defaults into the global Mantine theme.

import { createTheme } from "@mantine/core";

import { brandColors } from "./colors";
import { componentOverrides } from "./components";

export const theme = createTheme({
  primaryColor: "brand",
  primaryShade: 6,

  colors: {
    brand: brandColors,
  },

    fontFamily:
    "var(--font-inter), Inter, Arial, Helvetica, sans-serif",

  headings: {
    fontFamily:
     "var(--font-inter), Inter, Arial, Helvetica, sans-serif",
    fontWeight: "700",
  },

  defaultRadius: "md",

  radius: {
    xs: "6px",
    sm: "8px",
    md: "12px",
    lg: "16px",
    xl: "20px",
  },

  shadows: {
    xs: "0 2px 8px rgba(24, 24, 27, 0.04)",
    sm: "0 4px 16px rgba(24, 24, 27, 0.05)",
    md: "0 8px 30px rgba(24, 24, 27, 0.06)",
    lg: "0 12px 40px rgba(24, 24, 27, 0.08)",
    xl: "0 18px 60px rgba(24, 24, 27, 0.10)",
  },

  components: componentOverrides,
});