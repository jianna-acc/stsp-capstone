<!-- File: /docs/AI_RAG_API_ENDPOINT.md -->

# Protected RAG API Endpoint

## Purpose

Phase 5E exposes the completed retrieval and grounded-answer pipeline through a protected FastAPI endpoint.

The endpoint allows an authenticated student to ask a question using only eligible study materials owned by that student.

The completed workflow is:

```text
Student bearer token
→ Supabase Auth validation
→ authenticated student UUID
→ query embedding
→ Supabase vector retrieval
→ bounded grounded-answer generation
→ safe answer and source response
```

## Endpoint

```http
POST /api/rag/answer
```

The endpoint is registered under the `rag` OpenAPI tag.

Only `POST` is supported.

Requests using `GET`, `PUT`, `PATCH`, or `DELETE` receive an HTTP `405 Method Not Allowed` response.

## Authentication

The endpoint requires:

```http
Authorization: Bearer <supabase-access-token>
```

The access token is validated using Supabase Auth.

The backend calls:

```text
supabase_client.auth.get_user(access_token)
```

The authenticated Supabase user ID is converted into a UUID and stored in:

```text
AuthenticatedUser.user_id
```

The access token is not preserved in the authenticated-user object.

## Authentication Boundary

The RAG endpoint does not accept a `user_id` from the request body.

The ownership identity is derived only from the validated bearer token.

This prevents a client from attempting to retrieve another student's study materials by submitting a different user UUID.

The endpoint does not use the internal processor credential:

```http
X-Processor-Key
```

The processor key remains limited to backend-only file-processing operations.

## Authenticated User Dependency

File:

`backend/app/api/authenticated_user_dependency.py`

The dependency:

1. Reads bearer credentials using FastAPI `HTTPBearer`.
2. Rejects missing or non-bearer authentication.
3. Validates the access token through Supabase Auth.
4. Extracts `UserResponse.user.id`.
5. Converts the value into a UUID.
6. Returns an `AuthenticatedUser`.
7. Returns a safe HTTP `401` response for invalid or expired tokens.

Authentication failures include:

```text
Student authentication is required.
```

and:

```text
The authentication token is invalid or expired.
```

Authentication failures include:

```http
WWW-Authenticate: Bearer
```

## Request Schema

File:

`backend/app/schemas/rag.py`

The public request schema is:

```json
{
  "question": "Explain photosynthesis.",
  "study_file_id": "optional-study-file-uuid",
  "subject_id": "optional-subject-uuid",
  "match_count": 8,
  "similarity_threshold": 0.6
}
```

### Request fields

| Field | Required | Purpose |
|---|---:|---|
| `question` | Yes | Student question answered using eligible uploaded materials. |
| `study_file_id` | No | Limits retrieval to one eligible study file. |
| `subject_id` | No | Limits retrieval to one eligible subject. |
| `match_count` | No | Maximum retrieved chunks. Default: `8`. Allowed range: `1–20`. |
| `similarity_threshold` | No | Minimum accepted similarity. Default: `0.60`. Allowed range: `0.0–1.0`. |

Unknown fields are rejected.

The request cannot contain internal fields such as:

- `user_id`
- `chunk_id`
- `embedding`
- `access_token`
- `processor_key`

## Combined RAG Orchestration

File:

`backend/app/services/rag_orchestration.py`

The `RagOrchestrationService` combines Phase 5C retrieval and Phase 5D grounded-answer generation.

The service:

1. Validates the authenticated RAG request.
2. Converts it into a retrieval request.
3. Uses the authenticated user's UUID for ownership filtering.
4. Runs query embedding and vector retrieval.
5. Builds a grounded-answer request from retrieved chunks.
6. Generates the answer.
7. Validates that answer chunks remain an ordered subset of retrieved chunks.
8. Returns one combined `RagOrchestrationResult`.

## Combined Dependency Wiring

File:

`backend/app/api/rag_orchestration_dependency.py`

The combined dependency receives:

- `RetrievalOrchestrationService`
- `GroundedAnswerGenerationService`

It then creates:

```text
RagOrchestrationService
```

The combined dependency does not close child services directly.

FastAPI's existing child dependencies retain responsibility for their own resource cleanup. This prevents duplicate provider or client closure.

## Protected Route

File:

`backend/app/api/routes/rag.py`

The route:

1. Receives a validated `RagAnswerRequest`.
2. Receives an `AuthenticatedUser`.
3. Receives a configured `RagOrchestrationService`.
4. Builds the internal request using `authenticated_user.user_id`.
5. Runs the combined orchestration service.
6. Converts internal sources into safe public sources.
7. Maps controlled failures to stable HTTP responses.

## Successful Answer Response

Example:

```json
{
  "outcome": "answered",
  "answer": "Photosynthesis converts light energy into chemical energy. [Source 1]",
  "sources": [
    {
      "source_number": 1,
      "source_name": "Biology Notes.pdf",
      "chunk_index": 2,
      "similarity_score": 0.93
    }
  ],
  "retrieved_count": 1,
  "source_count": 1,
  "context_available": true
}
```

## No-Context Response

When retrieval returns no eligible relevant chunks, the endpoint returns HTTP `200` with:

```json
{
  "outcome": "no_context",
  "answer": "I could not find enough relevant information in your uploaded study materials to answer this question.",
  "sources": [],
  "retrieved_count": 0,
  "source_count": 0,
  "context_available": false
}
```

A no-context response is a normal result, not a provider error.

## Safe Public Sources

The API source response includes only:

- `source_number`
- `source_name`
- `chunk_index`
- `similarity_score`

The response excludes:

- Authenticated user UUID
- Chunk UUID
- Study-file UUID
- Subject UUID
- Raw chunk content
- Chunk metadata
- Embedding vectors
- Embedding provider metadata
- Generation provider metadata
- Access tokens
- Supabase credentials
- Gemini credentials

## Error Mapping

Controlled combined RAG failures use stable machine-readable codes.

| HTTP status | Error code | Meaning |
|---:|---|---|
| `400` | `RAG_ORCHESTRATION_VALIDATION_FAILED` | The combined RAG request was invalid. |
| `401` | FastAPI authentication detail | Authentication was missing, invalid, or expired. |
| `422` | Safe validation-detail response | The public request schema was invalid. |
| `500` | `RAG_ORCHESTRATION_RESPONSE_FAILED` | Internal retrieval and generation results were inconsistent. |
| `502` | `RAG_ORCHESTRATION_GENERATION_FAILED` | The configured generation provider failed. |
| `503` | `RAG_ORCHESTRATION_RETRIEVAL_FAILED` | Query embedding or vector retrieval failed. |

Private provider and internal exception messages are not returned to the client.

## Safe Validation Errors

Files:

- `backend/app/api/validation_error_handler.py`
- `backend/app/main.py`

FastAPI's default request-validation response can include the rejected input value.

Phase 5E registers a custom `RequestValidationError` handler that returns only:

- Validation error type
- Field location
- Safe validation message

It removes:

- Raw rejected input
- Internal validation context
- Secret-like unknown-field values

Example:

```json
{
  "detail": [
    {
      "type": "extra_forbidden",
      "loc": [
        "body",
        "access_token"
      ],
      "msg": "Extra inputs are not permitted"
    }
  ]
}
```

## OpenAPI Contract

The application OpenAPI document exposes:

```text
POST /api/rag/answer
```

The operation documents:

- `RagAnswerRequest`
- `RagAnswerResponse`
- `RagSourceResponse`
- `RagApiErrorResponse`
- Bearer-token security
- HTTP `200`
- HTTP `400`
- HTTP `401`
- HTTP `422`
- HTTP `500`
- HTTP `502`
- HTTP `503`

## Guarded Live API Smoke Test

Script:

`backend/scripts/smoke_live_rag_api_endpoint.py`

Run from the backend directory:

```powershell
python -m scripts.smoke_live_rag_api_endpoint
```

The script is guarded by:

```text
AI_LIVE_SMOKE_TESTS_ENABLED
```

The safe default is:

```text
false
```

The script requires a process-only student bearer token when live testing is explicitly enabled.

The token must not be stored in:

- `.env`
- Source code
- Documentation
- Git
- Screenshots
- Test fixtures

## Live-Test Environment Variables

| Variable | Required during live test | Purpose |
|---|---:|---|
| `RAG_API_SMOKE_ACCESS_TOKEN` | Yes | Temporary Supabase access token. |
| `RAG_API_SMOKE_STUDY_FILE_ID` | Yes for targeted validation | Indexed study-file filter. |
| `RAG_API_SMOKE_QUESTION` | No | Safe test question. |
| `RAG_API_SMOKE_SUBJECT_ID` | No | Optional subject filter. |
| `RAG_API_SMOKE_MATCH_COUNT` | No | Maximum retrieval matches. |
| `RAG_API_SMOKE_SIMILARITY_THRESHOLD` | No | Retrieval threshold. |
| `RAG_API_SMOKE_REQUIRE_CONTEXT` | No | Fails the smoke test when no context is returned. |

The script prints only safe status information.

It does not print:

- Access token
- User UUID
- Study-file UUID
- Subject UUID
- Student question
- Generated answer
- Source filename
- Chunk content
- Embeddings
- Provider credentials

## Live Validation Result

Phase 5E completed a guarded live request through the protected endpoint.

The live validation returned:

```text
HTTP status: 200
Outcome: answered
Context available: True
Retrieved count: 3
Source count: 3
Answer present: True
```

This confirmed:

- Supabase student authentication
- User UUID extraction
- Protected API routing
- Query embedding
- Ownership-bound vector retrieval
- Grounded answer generation
- Source preservation
- Safe response serialization
- Safe live-script output
- Resource cleanup
- Restoration of the disabled live-test default

## Test Coverage

Phase 5E adds tests for:

- Public request and response schemas
- Request defaults and limits
- Unknown-field rejection
- Authenticated-user resolution
- Missing and invalid bearer tokens
- Invalid Supabase user responses
- Token exclusion from authenticated-user data
- Combined RAG orchestration
- Retrieval failure mapping
- Generation failure mapping
- Internal-result consistency
- Combined dependency construction
- Protected endpoint success
- Normal no-context responses
- Controlled HTTP error mapping
- User ownership binding
- Processor-key rejection
- Request-method restrictions
- OpenAPI schemas and security
- Safe request-validation responses
- Secret-value non-echoing
- Guarded live-script behavior
- Live-script safe output

Offline tests use fake Supabase and AI dependencies.

Normal automated tests do not make live Gemini or Supabase requests.

## Security Boundaries

- Student identity comes only from a validated Supabase access token.
- The request body cannot override the authenticated user UUID.
- Retrieval remains scoped to the authenticated user.
- The processor key cannot authenticate a student request.
- Raw tokens are not preserved or returned.
- Raw vectors and chunk content are excluded from API responses.
- Validation errors do not echo rejected input values.
- Provider failures use controlled public messages.
- External live testing remains disabled by default.

## Next Integration Handoff

The next phase can connect the frontend study assistant to:

```text
POST /api/rag/answer
```

The frontend should:

- Send the current student's Supabase bearer token
- Submit the question and optional filters
- Display answered and no-context outcomes
- Render safe source references
- Handle HTTP `401`, `422`, `500`, `502`, and `503`
- Never place backend provider credentials in browser code