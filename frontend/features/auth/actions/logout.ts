// File: /frontend/features/auth/actions/logout.ts
// Purpose: Ends the current Supabase authentication session and
// redirects the student to the public login page.

"use server";

import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

export async function logoutAction():
  Promise<never> {
  const supabase = await createClient();

  const { error } =
    await supabase.auth.signOut();

  if (error) {
    redirect(
      "/dashboard?logoutError=1",
    );
  }

  redirect("/login?loggedOut=1");
}