// File: /frontend/app/(protected)/files/page.tsx
// Purpose: Redirects the former separate Files route to the
// combined subject and learning-material workspace.

import { redirect } from "next/navigation";

export default function FilesPage(): never {
  redirect("/subjects");
}