// File: /frontend/features/flashcards/api.test.ts
// Purpose: Tests authenticated Flashcard generation, saved-deck,
// review operations, response validation, and safe API errors.

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

const mocks = vi.hoisted(
  () => ({
    createClient: vi.fn(),
    getSession: vi.fn(),
    fetch: vi.fn(),
  }),
);

vi.mock(
  "@/lib/supabase/client",
  () => ({
    createClient:
      mocks.createClient,
  }),
);

import {
  deleteFlashcardDeck,
  generateFlashcards,
  getFlashcardDeck,
  listFlashcardDecks,
  recordFlashcardReview,
} from "./api";

const FLASHCARD_DECK_RESPONSE = {
  id: "deck-id",
  subject_id: "subject-id",
  study_file_id: "file-id",
  scope_type: "file",
  title: "Biology Notes Flashcards",
  requested_card_count: 5,

  cards: [
    {
      question:
        "What is photosynthesis?",
      answer:
        "A process that converts light energy into chemical energy.",
    },
    {
      question:
        "Where does photosynthesis mainly occur?",
      answer:
        "It mainly occurs in chloroplasts.",
    },
    {
      question:
        "What pigment absorbs light energy?",
      answer:
        "Chlorophyll absorbs light energy.",
    },
    {
      question:
        "What sugar can be produced through photosynthesis?",
      answer:
        "Glucose can be produced.",
    },
    {
      question:
        "What gas is released during photosynthesis?",
      answer:
        "Oxygen is released.",
    },
  ],

  sources: [
    {
      study_file_id:
        "file-id",

      source_name:
        "Biology Notes.pdf",

      chunk_index: 2,

      locator_type:
        "page",

      locator_label:
        "Page 3",
    },
  ],

  generation_model:
    "gemini-test-model",

  generation_count: 1,

  generated_at:
    "2026-08-09T08:00:00Z",

  created_at:
    "2026-08-09T08:00:00Z",

  updated_at:
    "2026-08-09T08:00:00Z",
} as const;

const FLASHCARD_LIST_RESPONSE = {
  items: [
    {
      id:
        "deck-id",

      subject_id:
        "subject-id",

      study_file_id:
        "file-id",

      scope_type:
        "file",

      title:
        "Biology Notes Flashcards",

      requested_card_count: 5,

      generation_model:
        "gemini-test-model",

      generation_count: 1,

      generated_at:
        "2026-08-09T08:00:00Z",

      created_at:
        "2026-08-09T08:00:00Z",

      updated_at:
        "2026-08-09T08:00:00Z",
    },
  ],
} as const;

const FLASHCARD_REVIEW_RESPONSE = {
  id:
    "review-id",

  deck_id:
    "deck-id",

  card_position: 1,

  outcome:
    "known",

  reviewed_at:
    "2026-08-11T08:00:00Z",
} as const;

function createJsonResponse(
  payload: unknown,
  status = 200,
): Response {
  return {
    ok:
      status >= 200 &&
      status < 300,

    status,

    json: vi
      .fn()
      .mockResolvedValue(
        payload,
      ),
  } as unknown as Response;
}

describe(
  "Flashcard API",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      process.env
        .NEXT_PUBLIC_API_BASE_URL =
        "http://127.0.0.1:8000";

      mocks.createClient
        .mockReturnValue({
          auth: {
            getSession:
              mocks.getSession,
          },
        });

      mocks.getSession
        .mockResolvedValue({
          data: {
            session: {
              access_token:
                "test-access-token",
            },
          },

          error: null,
        });

      vi.stubGlobal(
        "fetch",
        mocks.fetch,
      );
    });

    afterEach(() => {
      delete process.env
        .NEXT_PUBLIC_API_BASE_URL;

      vi.unstubAllGlobals();
    });

    it(
      "rejects generation without an authenticated session",
      async () => {
        mocks.getSession
          .mockResolvedValue({
            data: {
              session: null,
            },

            error: null,
          });

        await expect(
          generateFlashcards({
            scope_type:
              "subject",

            subject_id:
              "subject-id",

            card_count: 20,
          }),
        ).rejects.toMatchObject({
          name:
            "FlashcardApiError",

          status: 401,

          code:
            "AUTHENTICATION_REQUIRED",
        });

        expect(
          mocks.fetch,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "sends authentication and generation options",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              FLASHCARD_DECK_RESPONSE,
              201,
            ),
          );

        const controller =
          new AbortController();

        const result =
          await generateFlashcards(
            {
              scope_type:
                "file",

              subject_id:
                "subject-id",

              study_file_id:
                "file-id",

              card_count: 5,
            },
            {
              signal:
                controller.signal,
            },
          );

        expect(result).toEqual(
          FLASHCARD_DECK_RESPONSE,
        );

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/flashcards/generate",
        );

        expect(
          requestOptions.method,
        ).toBe("POST");

        expect(
          requestOptions.cache,
        ).toBe("no-store");

        expect(
          requestOptions.signal,
        ).toBe(
          controller.signal,
        );

        expect(
          requestOptions.headers,
        ).toEqual({
          "Content-Type":
            "application/json",

          Authorization:
            "Bearer test-access-token",
        });

        expect(
          JSON.parse(
            String(
              requestOptions.body,
            ),
          ),
        ).toEqual({
          scope_type:
            "file",

          subject_id:
            "subject-id",

          study_file_id:
            "file-id",

          card_count: 5,
        });
      },
    );

    it(
      "supports an API base URL already ending in api",
      async () => {
        process.env
          .NEXT_PUBLIC_API_BASE_URL =
          "http://127.0.0.1:8000/api";

        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              FLASHCARD_DECK_RESPONSE,
              201,
            ),
          );

        await generateFlashcards({
          scope_type:
            "file",

          subject_id:
            "subject-id",

          study_file_id:
            "file-id",

          card_count: 5,
        });

        const [
          requestUrl,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/flashcards/generate",
        );
      },
    );

    it(
      "lists authenticated Flashcard decks with a subject filter",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              FLASHCARD_LIST_RESPONSE,
            ),
          );

        const result =
          await listFlashcardDecks(
            "subject-id",
          );

        expect(result).toEqual(
          FLASHCARD_LIST_RESPONSE,
        );

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/flashcards?subject_id=subject-id",
        );

        expect(
          requestOptions.method,
        ).toBe("GET");

        expect(
          requestOptions.headers,
        ).toEqual({
          Authorization:
            "Bearer test-access-token",
        });

        expect(
          requestOptions.cache,
        ).toBe("no-store");
      },
    );

    it(
      "retrieves one saved Flashcard deck",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              FLASHCARD_DECK_RESPONSE,
            ),
          );

        const result =
          await getFlashcardDeck(
            "deck-id",
          );

        expect(result).toEqual(
          FLASHCARD_DECK_RESPONSE,
        );

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/flashcards/deck-id",
        );

        expect(
          requestOptions.method,
        ).toBe("GET");
      },
    );

    it(
      "records authenticated Flashcard review evidence",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              FLASHCARD_REVIEW_RESPONSE,
              201,
            ),
          );

        const controller =
          new AbortController();

        const result =
          await recordFlashcardReview(
            "deck-id",
            {
              card_position: 1,
              outcome: "known",
            },
            {
              signal:
                controller.signal,
            },
          );

        expect(result).toEqual(
          FLASHCARD_REVIEW_RESPONSE,
        );

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/flashcards/deck-id/reviews",
        );

        expect(
          requestOptions.method,
        ).toBe("POST");

        expect(
          requestOptions.cache,
        ).toBe("no-store");

        expect(
          requestOptions.signal,
        ).toBe(
          controller.signal,
        );

        expect(
          requestOptions.headers,
        ).toEqual({
          "Content-Type":
            "application/json",

          Authorization:
            "Bearer test-access-token",
        });

        expect(
          JSON.parse(
            String(
              requestOptions.body,
            ),
          ),
        ).toEqual({
          card_position: 1,
          outcome: "known",
        });
      },
    );

    it(
      "supports review-again Flashcard evidence",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                ...FLASHCARD_REVIEW_RESPONSE,

                card_position: 2,

                outcome:
                  "review_again",
              },
              201,
            ),
          );

        const result =
          await recordFlashcardReview(
            "deck-id",
            {
              card_position: 2,
              outcome:
                "review_again",
            },
          );

        expect(
          result.outcome,
        ).toBe(
          "review_again",
        );

        expect(
          result.card_position,
        ).toBe(
          2,
        );
      },
    );

    it(
      "rejects an invalid review position before making a request",
      async () => {
        await expect(
          recordFlashcardReview(
            "deck-id",
            {
              card_position: -1,
              outcome: "known",
            },
          ),
        ).rejects.toMatchObject({
          status: 400,

          code:
            "FLASHCARD_REVIEW_POSITION_INVALID",
        });

        expect(
          mocks.fetch,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "rejects an empty review deck id before making a request",
      async () => {
        await expect(
          recordFlashcardReview(
            "   ",
            {
              card_position: 0,
              outcome: "known",
            },
          ),
        ).rejects.toMatchObject({
          status: 400,

          code:
            "FLASHCARD_DECK_ID_REQUIRED",
        });

        expect(
          mocks.fetch,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "rejects malformed successful Flashcard review responses",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                id:
                  "review-id",

                deck_id:
                  "deck-id",

                outcome:
                  "known",
              },
              201,
            ),
          );

        await expect(
          recordFlashcardReview(
            "deck-id",
            {
              card_position: 0,
              outcome: "known",
            },
          ),
        ).rejects.toMatchObject({
          status: 502,

          code:
            "INVALID_FLASHCARD_REVIEW_RESPONSE",
        });
      },
    );

    it(
      "maps a controlled Flashcard review backend error",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                error_code:
                  "FLASHCARD_REVIEW_NOT_FOUND",

                message:
                  "The Flashcard review target was not found.",
              },
              404,
            ),
          );

        await expect(
          recordFlashcardReview(
            "deck-id",
            {
              card_position: 0,
              outcome: "known",
            },
          ),
        ).rejects.toMatchObject({
          status: 404,

          code:
            "FLASHCARD_REVIEW_NOT_FOUND",

          message:
            "The Flashcard review target was not found.",
        });
      },
    );

    it(
      "deletes one saved Flashcard deck without parsing a 204 body",
      async () => {
        const json =
          vi.fn();

        mocks.fetch
          .mockResolvedValue({
            ok: true,
            status: 204,
            json,
          } as unknown as Response);

        await expect(
          deleteFlashcardDeck(
            "deck-id",
          ),
        ).resolves.toBeUndefined();

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(
          requestUrl,
        ).toBe(
          "http://127.0.0.1:8000/api/flashcards/deck-id",
        );

        expect(
          requestOptions.method,
        ).toBe("DELETE");

        expect(
          json,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "rejects an empty deck id before making a request",
      async () => {
        await expect(
          getFlashcardDeck(
            "   ",
          ),
        ).rejects.toMatchObject({
          status: 400,

          code:
            "FLASHCARD_DECK_ID_REQUIRED",
        });

        expect(
          mocks.fetch,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "maps a controlled backend Flashcard error",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                error_code:
                  "FLASHCARD_SOURCE_UNAVAILABLE",

                message:
                  "The selected study material is not ready for Flashcard generation.",
              },
              409,
            ),
          );

        await expect(
          generateFlashcards({
            scope_type:
              "file",

            subject_id:
              "subject-id",

            study_file_id:
              "file-id",

            card_count: 5,
          }),
        ).rejects.toMatchObject({
          status: 409,

          code:
            "FLASHCARD_SOURCE_UNAVAILABLE",

          message:
            "The selected study material is not ready for Flashcard generation.",
        });
      },
    );

    it(
      "rejects malformed successful deck responses",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                id:
                  "deck-id",

                title:
                  "Incomplete Flashcards",
              },
              201,
            ),
          );

        await expect(
          generateFlashcards({
            scope_type:
              "subject",

            subject_id:
              "subject-id",

            card_count: 5,
          }),
        ).rejects.toMatchObject({
          status: 502,

          code:
            "INVALID_FLASHCARD_RESPONSE",
        });
      },
    );

    it(
      "rejects inconsistent Flashcard scope responses",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse(
              {
                ...FLASHCARD_DECK_RESPONSE,

                scope_type:
                  "subject",

                study_file_id:
                  "file-id",
              },
              201,
            ),
          );

        await expect(
          generateFlashcards({
            scope_type:
              "subject",

            subject_id:
              "subject-id",

            card_count: 5,
          }),
        ).rejects.toMatchObject({
          status: 502,

          code:
            "INVALID_FLASHCARD_RESPONSE",
        });
      },
    );

    it(
      "rejects malformed saved-deck list responses",
      async () => {
        mocks.fetch
          .mockResolvedValue(
            createJsonResponse({
              items: [
                {
                  id:
                    "deck-id",

                  title:
                    "Incomplete deck",
                },
              ],
            }),
          );

        await expect(
          listFlashcardDecks(),
        ).rejects.toMatchObject({
          status: 502,

          code:
            "INVALID_FLASHCARD_LIST_RESPONSE",
        });
      },
    );

    it(
      "reports network failures without exposing the token",
      async () => {
        mocks.fetch
          .mockRejectedValue(
            new TypeError(
              "Network unavailable",
            ),
          );

        const requestPromise =
          listFlashcardDecks();

        await expect(
          requestPromise,
        ).rejects.toMatchObject({
          status: null,

          code:
            "FLASHCARD_API_UNREACHABLE",

          message:
            "Flashcards could not connect to the backend.",
        });

        await requestPromise.catch(
          (
            error: unknown,
          ) => {
            expect(
              String(error),
            ).not.toContain(
              "test-access-token",
            );
          },
        );
      },
    );
  },
);