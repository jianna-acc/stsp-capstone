// File: /frontend/features/study-assistant/conversations-api.test.ts
// Purpose: Tests authenticated list, detail, rename, delete,
// response validation, and controlled conversation API errors.

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
  deleteStudyConversation,
  getStudyConversation,
  listStudyConversations,
  renameStudyConversation,
  StudyConversationApiError,
} from "./conversations-api";

const CONVERSATION = {
  id: "conversation-id",
  title: "Biology review",
  subject_id:
    "biology-subject",
  study_file_id:
    "biology-file",
  created_at:
    "2026-08-06T12:00:00Z",
  updated_at:
    "2026-08-06T12:05:00Z",
  last_message_at:
    "2026-08-06T12:05:00Z",
} as const;

const DETAIL_RESPONSE = {
  conversation:
    CONVERSATION,

  messages: [
    {
      id: "user-message",
      conversation_id:
        "conversation-id",
      role: "user",
      content:
        "Explain photosynthesis.",
      outcome: null,
      sources: [],
      created_at:
        "2026-08-06T12:01:00Z",
    },
    {
      id: "assistant-message",
      conversation_id:
        "conversation-id",
      role: "assistant",
      content:
        "Photosynthesis converts light energy. [Source 1]",
      outcome: "answered",
      sources: [
        {
          source_number: 1,
          source_name:
            "Biology Notes.pdf",
          chunk_index: 2,
          similarity_score: 0.91,
        },
      ],
      created_at:
        "2026-08-06T12:02:00Z",
    },
  ],
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
      .mockResolvedValue(payload),
  } as unknown as Response;
}

function createEmptyResponse(
  status: number,
): Response {
  return {
    ok:
      status >= 200 &&
      status < 300,

    status,

    json: vi.fn(),
  } as unknown as Response;
}

describe(
  "saved conversation API",
  () => {
    beforeEach(() => {
      process.env
        .NEXT_PUBLIC_API_BASE_URL =
        "http://127.0.0.1:8000";

      mocks.createClient.mockReturnValue({
        auth: {
          getSession:
            mocks.getSession,
        },
      });

      mocks.getSession.mockResolvedValue({
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
      "lists authenticated saved conversations",
      async () => {
        mocks.fetch.mockResolvedValue(
          createJsonResponse({
            items: [
              CONVERSATION,
            ],
          }),
        );

        const result =
          await listStudyConversations({
            limit: 25,
          });

        expect(result.items).toEqual([
          CONVERSATION,
        ]);

        expect(
          mocks.fetch,
        ).toHaveBeenCalledWith(
          "http://127.0.0.1:8000/api/study-conversations?limit=25",
          expect.objectContaining({
            method: "GET",
            cache: "no-store",
            headers:
              expect.objectContaining({
                Authorization:
                  "Bearer test-access-token",
              }),
          }),
        );
      },
    );

    it(
      "loads one conversation and its messages",
      async () => {
        mocks.fetch.mockResolvedValue(
          createJsonResponse(
            DETAIL_RESPONSE,
          ),
        );

        const result =
          await getStudyConversation(
            "conversation-id",
            {
              messageLimit: 300,
            },
          );

        expect(result).toEqual(
          DETAIL_RESPONSE,
        );

        expect(
          mocks.fetch,
        ).toHaveBeenCalledWith(
          "http://127.0.0.1:8000/api/study-conversations/conversation-id?message_limit=300",
          expect.objectContaining({
            method: "GET",
          }),
        );
      },
    );

    it(
      "renames a saved conversation",
      async () => {
        const renamedConversation = {
          ...CONVERSATION,
          title:
            "Photosynthesis review",
        };

        mocks.fetch.mockResolvedValue(
          createJsonResponse(
            renamedConversation,
          ),
        );

        const result =
          await renameStudyConversation(
            "conversation-id",
            "  Photosynthesis review  ",
          );

        expect(result).toEqual(
          renamedConversation,
        );

        const [
          requestUrl,
          requestOptions,
        ] = mocks.fetch.mock
          .calls[0] as [
          string,
          RequestInit,
        ];

        expect(requestUrl).toBe(
          "http://127.0.0.1:8000/api/study-conversations/conversation-id",
        );

        expect(
          requestOptions.method,
        ).toBe("PATCH");

        expect(
          JSON.parse(
            String(
              requestOptions.body,
            ),
          ),
        ).toEqual({
          title:
            "Photosynthesis review",
        });
      },
    );

    it(
      "deletes a saved conversation using the 204 contract",
      async () => {
        const response =
          createEmptyResponse(204);

        mocks.fetch.mockResolvedValue(
          response,
        );

        await expect(
          deleteStudyConversation(
            "conversation-id",
          ),
        ).resolves.toBeUndefined();

        expect(
          mocks.fetch,
        ).toHaveBeenCalledWith(
          "http://127.0.0.1:8000/api/study-conversations/conversation-id",
          expect.objectContaining({
            method: "DELETE",
          }),
        );

        expect(
          response.json,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "rejects requests without an authenticated session",
      async () => {
        mocks.getSession.mockResolvedValue({
          data: {
            session: null,
          },
          error: null,
        });

        await expect(
          listStudyConversations(),
        ).rejects.toMatchObject({
          name:
            "StudyConversationApiError",
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
      "maps controlled conversation errors",
      async () => {
        mocks.fetch.mockResolvedValue(
          createJsonResponse(
            {
              error_code:
                "STUDY_CONVERSATION_NOT_FOUND",
              message:
                "The requested conversation was not found.",
            },
            404,
          ),
        );

        await expect(
          getStudyConversation(
            "missing-conversation",
          ),
        ).rejects.toMatchObject({
          status: 404,
          code:
            "STUDY_CONVERSATION_NOT_FOUND",
          message:
            "The requested conversation was not found.",
        });
      },
    );

    it(
      "rejects malformed conversation detail responses",
      async () => {
        mocks.fetch.mockResolvedValue(
          createJsonResponse({
            conversation:
              CONVERSATION,
            messages: [
              {
                id:
                  "invalid-message",
                conversation_id:
                  "another-conversation",
                role: "user",
                content:
                  "Invalid ownership.",
                outcome: null,
                sources: [],
                created_at:
                  "2026-08-06T12:03:00Z",
              },
            ],
          }),
        );

        const requestPromise =
          getStudyConversation(
            "conversation-id",
          );

        await expect(
          requestPromise,
        ).rejects.toBeInstanceOf(
          StudyConversationApiError,
        );

        await expect(
          requestPromise,
        ).rejects.toMatchObject({
          status: 502,
          code:
            "INVALID_CONVERSATION_DETAIL_RESPONSE",
        });
      },
    );

    it(
      "reports network errors without exposing the access token",
      async () => {
        mocks.fetch.mockRejectedValue(
          new TypeError(
            "Network unavailable",
          ),
        );

        const requestPromise =
          listStudyConversations();

        await expect(
          requestPromise,
        ).rejects.toMatchObject({
          status: null,
          code:
            "CONVERSATION_API_UNREACHABLE",
          message:
            "The Study Assistant could not connect to conversation storage.",
        });

        await requestPromise.catch(
          (error: unknown) => {
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
