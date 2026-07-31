// File: /frontend/features/subjects/types.ts
// Purpose: Defines shared subject records, form values, and
// Server Action results for Phase 3 subject management.

import type { Database } from "@/types/database";

type SubjectRow =
  Database["public"]["Tables"]["subjects"]["Row"];

export type SubjectSummary = Pick<
  SubjectRow,
  "id" | "name" | "color" | "created_at" | "updated_at"
>;

export type SubjectInput = {
  name: string;
  color: string;
};

export type SubjectFieldErrors = {
  name?: string;
  color?: string;
};

export type SubjectMutationResult =
  | {
      success: true;
      message: string;
      subject: SubjectSummary;
    }
  | {
      success: false;
      message: string;
      fieldErrors?: SubjectFieldErrors;
    };

export type SubjectDeleteResult =
  | {
      success: true;
      message: string;
      deletedId: string;
    }
  | {
      success: false;
      message: string;
    };