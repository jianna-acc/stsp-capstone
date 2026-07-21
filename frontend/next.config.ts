// File: /frontend/next.config.ts
// Purpose: Configures Next.js and sets the frontend as the Turbopack root.

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;