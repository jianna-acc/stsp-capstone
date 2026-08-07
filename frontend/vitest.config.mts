// File: /frontend/vitest.config.mts
// Purpose: Configures Vitest, React Testing Library, jsdom,
// and the frontend TypeScript path aliases.

import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    tsconfigPaths(),
    react(),
  ],

  test: {
    environment: "jsdom",

    setupFiles: [
      "./tests/setup.ts",
    ],

    clearMocks: true,
    mockReset: true,
    restoreMocks: true,

    css: true,
  },
});