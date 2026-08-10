// File: /frontend/features/quizzes/server/options.test.ts
// Purpose: Tests authenticated subject and ready-file
// loading for Quiz generation options.

import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

vi.mock(
  "server-only",
  () => ({}),
);

const mocks =
  vi.hoisted(
    () => ({
      getUser:
        vi.fn(),

      from:
        vi.fn(),
    }),
  );

vi.mock(
  "@/lib/supabase/server",
  () => ({
    createClient:
      async () => ({
        auth: {
          getUser:
            mocks.getUser,
        },

        from:
          mocks.from,
      }),
  }),
);

import {
  getQuizFilterOptions,
} from "./options";

function createQuery(
  result: unknown,
) {
  const query = {
    select:
      vi.fn(),

    eq:
      vi.fn(),

    order:
      vi.fn(),
  };

  query.select
    .mockReturnValue(
      query,
    );

  query.eq
    .mockReturnValue(
      query,
    );

  query.order
    .mockResolvedValue(
      result,
    );

  return query;
}

describe(
  "getQuizFilterOptions",
  () => {
    beforeEach(
      () => {
        mocks.getUser
          .mockReset();

        mocks.from
          .mockReset();
      },
    );

    it(
      "loads owned subjects and ready study files",
      async () => {
        mocks.getUser
          .mockResolvedValue({
            data: {
              user: {
                id:
                  "student-id",
              },
            },
            error:
              null,
          });

        const subjectsQuery =
          createQuery({
            data: [
              {
                id:
                  "subject-1",

                name:
                  "Biology",
              },
            ],
            error:
              null,
          });

        const filesQuery =
          createQuery({
            data: [
              {
                id:
                  "file-1",

                subject_id:
                  "subject-1",

                original_filename:
                  "Cells.pdf",
              },
            ],
            error:
              null,
          });

        mocks.from
          .mockImplementation(
            (
              tableName:
                string,
            ) => {
              if (
                tableName ===
                "subjects"
              ) {
                return subjectsQuery;
              }

              if (
                tableName ===
                "study_files"
              ) {
                return filesQuery;
              }

              throw new Error(
                `Unexpected table: ${tableName}`,
              );
            },
          );

        const result =
          await getQuizFilterOptions();

        expect(
          result,
        ).toEqual({
          subjects: [
            {
              id:
                "subject-1",

              name:
                "Biology",
            },
          ],

          studyFiles: [
            {
              id:
                "file-1",

              subjectId:
                "subject-1",

              originalFilename:
                "Cells.pdf",
            },
          ],

          loadError:
            null,
        });

        expect(
          mocks.from,
        ).toHaveBeenCalledWith(
          "subjects",
        );

        expect(
          mocks.from,
        ).toHaveBeenCalledWith(
          "study_files",
        );
      },
    );

    it(
      "returns unavailable options without an authenticated user",
      async () => {
        mocks.getUser
          .mockResolvedValue({
            data: {
              user:
                null,
            },
            error:
              null,
          });

        const result =
          await getQuizFilterOptions();

        expect(
          result.subjects,
        ).toEqual(
          [],
        );

        expect(
          result.studyFiles,
        ).toEqual(
          [],
        );

        expect(
          result.loadError,
        ).toContain(
          "could not be loaded",
        );

        expect(
          mocks.from,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "returns unavailable options when a database query fails",
      async () => {
        mocks.getUser
          .mockResolvedValue({
            data: {
              user: {
                id:
                  "student-id",
              },
            },
            error:
              null,
          });

        const subjectsQuery =
          createQuery({
            data:
              null,

            error: {
              message:
                "database failure",
            },
          });

        const filesQuery =
          createQuery({
            data:
              [],

            error:
              null,
          });

        mocks.from
          .mockImplementation(
            (
              tableName:
                string,
            ) =>
              tableName ===
                "subjects"
                ? subjectsQuery
                : filesQuery,
          );

        const result =
          await getQuizFilterOptions();

        expect(
          result.subjects,
        ).toEqual(
          [],
        );

        expect(
          result.studyFiles,
        ).toEqual(
          [],
        );

        expect(
          result.loadError,
        ).not.toBeNull();
      },
    );
  },
);