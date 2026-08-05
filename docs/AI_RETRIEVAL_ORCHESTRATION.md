<!-- File: /docs/AI_RETRIEVAL_ORCHESTRATION.md -->

# AI Retrieval Orchestration

## Purpose

Phase 5C connects the Phase 5B query-embedding service to the Phase 5A Supabase vector-search RPC.

The completed workflow is:

```text
Student question
→ validated retrieval-orchestration request
→ Gemini retrieval-query embedding
→ Supabase vector-search RPC
→ validated study-material chunks
→ matches or normal no-context result
```

Phase 5C performs retrieval only. It does not yet generate the final AI answer.

## Main Components

### Retrieval contracts

File:

`backend/app/ai/retrieval_contracts.py`

This file defines:

- `RetrievalRequest`
- `RetrievedStudyChunk`
- `RetrievalResult`
- `RetrievalOutcome`
- Stable retrieval failure codes
- Query-vector validation
- RPC-row validation
- Filter validation
- Normal no-context handling

The current retrieval vector size is exactly 768 dimensions.

The default retrieval settings are:

- Match count: 8
- Minimum match count: 1
- Maximum match count: 20
- Similarity threshold: 0.60

## Retrieval Persistence

File:

`backend/app/ai/retrieval_persistence.py`

The `SupabaseRetrievalPersistence` adapter calls:

`public.search_study_file_ai_chunks`

The adapter:

1. Converts the validated request into exact RPC parameters.
2. Uses the trusted backend Supabase administrator service.
3. Calls the service-role-only retrieval RPC.
4. Validates the returned JSON rows.
5. Converts rows into immutable `RetrievedStudyChunk` objects.
6. Returns a normal no-context result when no rows match.

## Trusted Supabase RPC Wrapper

File:

`backend/app/services/supabase_admin.py`

Phase 5C exposes the existing JSON RPC helper through:

`call_rpc_json(function_name, payload)`

This keeps the Supabase secret key inside the backend and avoids creating another Supabase client pattern.

## Retrieval Orchestration Service

File:

`backend/app/services/retrieval_orchestration.py`

The `RetrievalOrchestrationService` performs the complete retrieval workflow:

1. Validates the user ID, question, filters, threshold, and match count.
2. Calls the Phase 5B `QueryEmbeddingService`.
3. Creates a validated `RetrievalRequest` using the generated embedding.
4. Calls `SupabaseRetrievalPersistence`.
5. Verifies that the retrieval response matches the generated request.
6. Returns safe retrieval metadata and retrieved study chunks.

The orchestration result does not expose the raw 768-dimensional query vector.

## FastAPI Dependency

File:

`backend/app/api/retrieval_orchestration_dependency.py`

The dependency constructs:

- `QueryEmbeddingService`
- `SupabaseAdminService`
- `SupabaseRetrievalPersistence`
- `RetrievalOrchestrationService`

No public RAG route is added during Phase 5C.

## Outcomes

A successful retrieval has one of two outcomes:

| Outcome | Meaning |
|---|---|
| `matches` | One or more relevant study chunks were found. |
| `no_context` | No chunks passed the filters and similarity threshold. |

`no_context` is a valid result and not a system failure.

## Failure Codes

| Failure code | Meaning |
|---|---|
| `RETRIEVAL_VALIDATION_FAILED` | The retrieval input is invalid. |
| `RETRIEVAL_REQUEST_FAILED` | The trusted Supabase RPC request failed. |
| `RETRIEVAL_RESPONSE_FAILED` | Supabase returned an invalid or inconsistent response. |

Query-embedding failures continue to use the stable Phase 5B failure codes.

## Live Smoke Test

Script:

`backend/scripts/smoke_live_retrieval_orchestration.py`

The script runs one guarded live workflow:

```text
Gemini query embedding
→ Supabase vector search
→ validated retrieval result
```

Run it from the backend directory as a module:

```powershell
python -m scripts.smoke_live_retrieval_orchestration
```

The script is protected by:

`AI_LIVE_SMOKE_TESTS_ENABLED`

Its safe default is `false`.

Live smoke output does not print:

- Gemini credentials
- Supabase credentials
- Raw embedding vectors
- Complete study-file content
- The complete student question

## Test Coverage

Phase 5C adds:

- `backend/tests/test_retrieval_contracts.py`
- `backend/tests/test_retrieval_persistence.py`
- `backend/tests/test_retrieval_orchestration.py`
- `backend/tests/test_retrieval_orchestration_dependency.py`
- `backend/tests/test_live_retrieval_orchestration_smoke_script.py`

The tests cover:

- Request defaults and validation
- Exact RPC parameters
- Returned chunk validation
- Similarity ordering
- Duplicate-chunk rejection
- File and subject filters
- Normal no-context behavior
- Supabase request failures
- Invalid Supabase responses
- Embedding-to-retrieval orchestration
- Dependency construction
- Safe live-smoke behavior

Normal automated tests use fake providers and do not call Gemini or Supabase.

## Security Boundaries

- Gemini is called only by the backend.
- Supabase service-role credentials remain backend-only.
- Raw query vectors are not returned to the frontend.
- The retrieval RPC enforces user ownership.
- Only ready and indexed study files are eligible.
- File and subject filters are validated before and after retrieval.
- Live smoke testing is disabled by default.

## Phase 5D Handoff

Phase 5D will use the validated retrieved chunks to generate a grounded answer.

Phase 5D should:

- Build a controlled context prompt from retrieved chunks.
- Prevent unsupported answers when no context is available.
- Generate an answer using Gemini.
- Preserve source references for later citations.
- Avoid exposing raw vectors or backend credentials.
