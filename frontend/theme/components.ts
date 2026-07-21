// File: /frontend/theme/components.ts
// Purpose: Defines shared default properties for Mantine components.

import {
  Button,
  Card,
  Input,
  Paper,
} from "@mantine/core";

export const componentOverrides = {
  Button: Button.extend({
    defaultProps: {
      radius: "md",
      fw: 600,
    },
  }),

  Input: Input.extend({
    defaultProps: {
      radius: "md",
      size: "md",
    },
  }),

  Card: Card.extend({
    defaultProps: {
      radius: "xl",
      withBorder: true,
      shadow: "sm",
    },
  }),

  Paper: Paper.extend({
    defaultProps: {
      radius: "xl",
    },
  }),
};