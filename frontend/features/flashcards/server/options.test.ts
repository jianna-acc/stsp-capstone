// File: /frontend/features/flashcards/server/options.test.ts
// Purpose: Tests authenticated Flashcard subject and ready-file
// option loading from Supabase.

import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

const mocks = vi.hoisted(
  () => ({
    createClient: vi.fn(),
    redirect: vi.fn(),
  }),
);

vi.mock(
  "server-only",
  () => ({}),
);

vi.mock(
  "@/lib/supabase/server",
  () => ({
    createClient:
      mocks.createClient,
  }),
);

vi.mock(
  "next/navigation",
  () => ({
    redirect:
      mocks.redirect,
  }),
);

import {
  getFlashcardFilterOptions,
} from "./options";

interface SubjectRow {
  id: string;
  name: string;
}

interface StudyFileRow {
  id: string;
  subject_id: string;
  original_filename: string;
}

interface QueryResult<T> {
  data: T[] | null;
  error: unknown;
}

interface FakeSupabaseOptions {
  authenticated?: boolean;
  authError?: unknown;

  subjectsResult?: QueryResult<
    SubjectRow
  >;

  studyFilesResult?: QueryResult<
    StudyFileRow
  >;
}

function createFakeSupabase({
  authenticated = true,
  authError = null,

  subjectsResult = {
    data: [
      {
        id: "subject-1",
        name: "Biology",
      },
      {
        id: "subject-2",
        name: "Chemistry",
      },
    ],
    error: null,
  },

  studyFilesResult = {
    data: [
      {
        id: "file-1",
        subject_id:
          "subject-1",
        original_filename:
          "Biology Notes.pdf",
      },
      {
        id: "file-2",
        subject_id:
          "subject-2",
        original_filename:
          "Chemistry Slides.pptx",
      },
    ],
    error: null,
  },
}: FakeSupabaseOptions = {}) {
  const getUser =
    vi.fn().mockResolvedValue({
      data: {
        user:
          authenticated
            ? {
                id:
                  "user-1",
              }
            : null,
      },

      error:
        authError,
    });

  const subjectsOrder =
    vi.fn().mockResolvedValue(
      subjectsResult,
    );

  const subjectsEq =
    vi.fn().mockReturnValue({
      order:
        subjectsOrder,
    });

  const subjectsSelect =
    vi.fn().mockReturnValue({
      eq:
        subjectsEq,
    });

  const studyFilesOrder =
    vi.fn().mockResolvedValue(
      studyFilesResult,
    );

  const studyFilesStatusEq =
    vi.fn().mockReturnValue({
      order:
        studyFilesOrder,
    });

  const studyFilesUserEq =
    vi.fn().mockReturnValue({
      eq:
        studyFilesStatusEq,
    });

  const studyFilesSelect =
    vi.fn().mockReturnValue({
      eq:
        studyFilesUserEq,
    });

  const from =
    vi.fn(
      (
        table: string,
      ) => {
        if (
          table ===
          "subjects"
        ) {
          return {
            select:
              subjectsSelect,
          };
        }

        if (
          table ===
          "study_files"
        ) {
          return {
            select:
              studyFilesSelect,
          };
        }

        throw new Error(
          `Unexpected table: ${table}`,
        );
      },
    );

  return {
    client: {
      auth: {
        getUser,
      },

      from,
    },

    getUser,
    from,

    subjectsSelect,
    subjectsEq,
    subjectsOrder,

    studyFilesSelect,
    studyFilesUserEq,
    studyFilesStatusEq,
    studyFilesOrder,
  };
}

describe(
  "getFlashcardFilterOptions",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      mocks.redirect
        .mockImplementation(
          (
            path: string,
          ) => {
            throw new Error(
              `REDIRECT:${path}`,
            );
          },
        );
    });

    it(
      "loads owned subjects and ready study files",
      async () => {
        const fake =
          createFakeSupabase();

        mocks.createClient
          .mockResolvedValue(
            fake.client,
          );

        const result =
          await getFlashcardFilterOptions();

        expect(result).toEqual({
          subjects: [
            {
              id:
                "subject-1",
              name:
                "Biology",
            },
            {
              id:
                "subject-2",
              name:
                "Chemistry",
            },
          ],

          studyFiles: [
            {
              id:
                "file-1",
              subjectId:
                "subject-1",
              originalFilename:
                "Biology Notes.pdf",
            },
            {
              id:
                "file-2",
              subjectId:
                "subject-2",
              originalFilename:
                "Chemistry Slides.pptx",
            },
          ],

          loadError: null,
        });

        expect(
          fake.getUser,
        ).toHaveBeenCalledTimes(1);

        expect(
          fake.subjectsSelect,
        ).toHaveBeenCalledWith(
          "id, name",
        );

        expect(
          fake.subjectsEq,
        ).toHaveBeenCalledWith(
          "user_id",
          "user-1",
        );

        expect(
          fake.studyFilesSelect,
        ).toHaveBeenCalledWith(
          "id, subject_id, original_filename",
        );

        expect(
          fake.studyFilesUserEq,
        ).toHaveBeenCalledWith(
          "user_id",
          "user-1",
        );

        expect(
          fake.studyFilesStatusEq,
        ).toHaveBeenCalledWith(
          "processing_status",
          "ready",
        );
      },
    );

    it(
      "redirects when no authenticated user exists",
      async () => {
        const fake =
          createFakeSupabase({
            authenticated:
              false,
          });

        mocks.createClient
          .mockResolvedValue(
            fake.client,
          );

        await expect(
          getFlashcardFilterOptions(),
        ).rejects.toThrow(
          "REDIRECT:/login",
        );

        expect(
          mocks.redirect,
        ).toHaveBeenCalledWith(
          "/login",
        );

        expect(
          fake.from,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "fails safely when subject loading fails",
      async () => {
        const fake =
          createFakeSupabase({
            subjectsResult: {
              data: null,
              error: {
                message:
                  "Subject query failed",
              },
            },
          });

        mocks.createClient
          .mockResolvedValue(
            fake.client,
          );

        const result =
          await getFlashcardFilterOptions();

        expect(result).toEqual({
          subjects: [],
          studyFiles: [],
          loadError:
            "Your subjects and ready study materials could not be loaded. Flashcard generation is temporarily unavailable.",
        });
      },
    );

    it(
      "fails safely when ready-file loading fails",
      async () => {
        const fake =
          createFakeSupabase({
            studyFilesResult: {
              data: null,
              error: {
                message:
                  "Study-file query failed",
              },
            },
          });

        mocks.createClient
          .mockResolvedValue(
            fake.client,
          );

        const result =
          await getFlashcardFilterOptions();

        expect(result).toEqual({
          subjects: [],
          studyFiles: [],
          loadError:
            "Your subjects and ready study materials could not be loaded. Flashcard generation is temporarily unavailable.",
        });
      },
    );
  },
);