// File: /frontend/features/auth/actions/logout.ts
// Purpose: Ends the current Supabase authentication session,
// clears cached authenticated layouts, and redirects to login.

"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

export async function logoutAction(): Promise<never> {
  const supabase = await createClient();

  /*
   * Because the Supabase server client is cookie-aware,
   * signOut() also updates the authentication cookies through
   * the cookie handlers defined in server.ts.
   */
  const { error } = await supabase.auth.signOut();

  if (error) {
    redirect("/dashboard?logoutError=1");
  }

  /*
   * Clear previously rendered authenticated layouts so the
   * browser cannot continue using cached protected content.
   */
  revalidatePath("/", "layout");

  redirect("/login?loggedOut=1");
}