// File: /frontend/features/reviewers/server/options.test.ts
// Purpose: Tests authenticated subject and ready study-file
// option loading for reviewer generation.

import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

const mocks = vi.hoisted(
  () => ({
    createClient:
      vi.fn(),
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

import {
  getReviewerFilterOptions,
} from "./options";

interface MockClientOptions {
  userResult?: {
    data: {
      user: {
        id: string;
      } | null;
    };

    error:
      Error | null;
  };

  subjectsResult?: {
    data:
      | Array<{
          id: string;
          name: string;
        }>
      | null;

    error:
      Error | null;
  };

  studyFilesResult?: {
    data:
      | Array<{
          id: string;
          subject_id: string;
          original_filename:
            string;
        }>
      | null;

    error:
      Error | null;
  };
}

function createMockClient({
  userResult = {
    data: {
      user: {
        id: "student-id",
      },
    },

    error: null,
  },

  subjectsResult = {
    data: [
      {
        id:
          "biology-subject",

        name:
          "Biology",
      },
    ],

    error: null,
  },

  studyFilesResult = {
    data: [
      {
        id:
          "biology-file",

        subject_id:
          "biology-subject",

        original_filename:
          "Biology Notes.pdf",
      },
    ],

    error: null,
  },
}: MockClientOptions = {}) {
  const subjectsOrder =
    vi.fn().mockResolvedValue(
      subjectsResult,
    );

  const subjectsUserEq =
    vi.fn().mockReturnValue({
      order:
        subjectsOrder,
    });

  const subjectsSelect =
    vi.fn().mockReturnValue({
      eq:
        subjectsUserEq,
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

  const from = vi.fn(
    (
      tableName: string,
    ) => {
      if (
        tableName ===
        "subjects"
      ) {
        return {
          select:
            subjectsSelect,
        };
      }

      if (
        tableName ===
        "study_files"
      ) {
        return {
          select:
            studyFilesSelect,
        };
      }

      throw new Error(
        `Unexpected table: ${tableName}`,
      );
    },
  );

  return {
    client: {
      auth: {
        getUser:
          vi.fn()
            .mockResolvedValue(
              userResult,
            ),
      },

      from,
    },

    subjectsUserEq,
    studyFilesUserEq,
    studyFilesStatusEq,
  };
}

describe(
  "getReviewerFilterOptions",
  () => {
    beforeEach(() => {
      mocks.createClient
        .mockReset();
    });

    it(
      "loads subjects and ready study files for the authenticated student",
      async () => {
        const {
          client,
          subjectsUserEq,
          studyFilesUserEq,
          studyFilesStatusEq,
        } = createMockClient();

        mocks.createClient
          .mockResolvedValue(
            client,
          );

        const result =
          await getReviewerFilterOptions();

        expect(
          result,
        ).toEqual({
          subjects: [
            {
              id:
                "biology-subject",

              name:
                "Biology",
            },
          ],

          studyFiles: [
            {
              id:
                "biology-file",

              subjectId:
                "biology-subject",

              originalFilename:
                "Biology Notes.pdf",
            },
          ],

          loadError: null,
        });

        expect(
          subjectsUserEq,
        ).toHaveBeenCalledWith(
          "user_id",
          "student-id",
        );

        expect(
          studyFilesUserEq,
        ).toHaveBeenCalledWith(
          "user_id",
          "student-id",
        );

        expect(
          studyFilesStatusEq,
        ).toHaveBeenCalledWith(
          "processing_status",
          "ready",
        );
      },
    );

    it(
      "returns safe empty options when authentication fails",
      async () => {
        const {
          client,
        } = createMockClient({
          userResult: {
            data: {
              user: null,
            },

            error:
              new Error(
                "Invalid session",
              ),
          },
        });

        mocks.createClient
          .mockResolvedValue(
            client,
          );

        const result =
          await getReviewerFilterOptions();

        expect(
          result,
        ).toEqual({
          subjects: [],
          studyFiles: [],

          loadError:
            "Your subjects and ready study materials could not be loaded. Reviewer generation is temporarily unavailable.",
        });

        expect(
          client.from,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "returns safe empty options when subject or file loading fails",
      async () => {
        const {
          client,
        } = createMockClient({
          studyFilesResult: {
            data: null,

            error:
              new Error(
                "Study file query failed",
              ),
          },
        });

        mocks.createClient
          .mockResolvedValue(
            client,
          );

        const result =
          await getReviewerFilterOptions();

        expect(
          result.subjects,
        ).toEqual([]);

        expect(
          result.studyFiles,
        ).toEqual([]);

        expect(
          result.loadError,
        ).toBe(
          "Your subjects and ready study materials could not be loaded. Reviewer generation is temporarily unavailable.",
        );
      },
    );
  },
);