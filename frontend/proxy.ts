// File: /frontend/proxy.ts
// Purpose: Runs the Supabase session-refresh utility before
// matched Next.js requests are completed.

import type { NextRequest } from "next/server";

import { updateSession } from "@/lib/supabase/proxy";

export async function proxy(
  request: NextRequest,
) {
  return updateSession(request);
}

export const config = {
  matcher: [
    /*
     * Match application requests except static framework files,
     * optimized images, the favicon, and common image assets.
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};