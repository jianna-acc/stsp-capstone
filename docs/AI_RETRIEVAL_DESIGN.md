<!-- File: /docs/AI_RETRIEVAL_DESIGN.md -->

# AI Retrieval Design

This document defines the Phase 5A vector-retrieval contract before its SQL and Python implementation.

## Purpose

Phase 4 implemented the indexing side of retrieval-augmented generation:

```text
Study material
? retrieval_document embedding
? pgvector storage
```

Phase 5 implements the retrieval side:

```text
Student question
? retrieval_query embedding
? cosine-similarity search
? relevant study-material chunks
? grounded answer and source citations
```

## Planned Retrieval RPC

The retrieval function will be:

```text
public.search_study_file_ai_chunks
```

Its planned signature is:

```sql
public.search_study_file_ai_chunks(
    p_user_id uuid,
    p_query_embedding jsonb,
    p_match_count integer default 8,
    p_similarity_threshold double precision default 0.60,
    p_study_file_id uuid default null,
    p_subject_id uuid default null
)
```

## Parameters

| Parameter | Required | Validation | Purpose |
|---|---:|---|---|
| `p_user_id` | Yes | Non-null UUID | Restricts results to study materials owned by one user |
| `p_query_embedding` | Yes | JSON array containing exactly 768 numeric and nonzero values | Carries the Gemini `retrieval_query` vector |
| `p_match_count` | No | Integer from 1 to 20 | Limits the number of returned chunks |
| `p_similarity_threshold` | No | Number from 0.00 to 1.00 | Removes semantically weak results |
| `p_study_file_id` | No | Owned study-file UUID or null | Restricts search to one file |
| `p_subject_id` | No | Owned subject UUID or null | Restricts search to files under one subject |

## Returned Fields

The retrieval RPC will return:

```text
chunk_id
study_file_id
subject_id
source_name
chunk_index
content
start_offset
end_offset
chunk_metadata
embedding_model
similarity_score
```

The stored embedding will not be returned.

## Eligibility Rules

A chunk may be returned only when:

- Its `user_id` matches `p_user_id`.
- Its source study file belongs to `p_user_id`.
- Its source study file has `processing_status = 'ready'`.
- Its `embedding_dimensions` value equals 768.
- Its `embedding_task_type` is `retrieval_document`.
- Its similarity is at or above `p_similarity_threshold`.
- It matches the optional study-file filter.
- It matches the optional subject filter.

When both optional filters are null, all ready indexed study files owned by the user are eligible.

## Cosine Similarity

The function will use the pgvector cosine-distance operator:

```sql
<=>
```

Similarity will be calculated as:

```sql
1 - (stored_embedding <=> query_embedding)
```

Results will be ordered by:

```text
similarity_score descending
study_file_id ascending
chunk_index ascending
```

The secondary ordering provides deterministic results when similarity scores are equal.

## Query-Vector Validation

The function will reject an embedding when:

- The value is null.
- The value is not a JSON array.
- The array does not contain exactly 768 elements.
- An element is not a JSON number.
- A value cannot be converted safely to a real number.
- Every vector value is zero.
- Conversion to `extensions.vector(768)` fails.

The Python service will validate the same contract before calling the RPC.

## Parameter Validation

The function will reject:

- A null user ID.
- A result count below 1.
- A result count above 20.
- A similarity threshold below 0.
- A similarity threshold above 1.

An empty matching result will return an empty result set rather than expose unrelated study materials.

## Security

The function will use:

```text
security definer
restricted search path
fully qualified database objects
```

Execution permissions will be:

| Role | Execute permission |
|---|---|
| `public` | Revoked |
| `anon` | Revoked |
| `authenticated` | Revoked |
| `service_role` | Granted |

The browser will not execute the retrieval function directly.

The protected execution flow will be:

```text
Authenticated frontend
? protected FastAPI endpoint
? verified user identity
? SupabaseAdminService
? service-role retrieval RPC
```

The function will still enforce `p_user_id` ownership even though the service role executes it.

## Planned Failure Boundaries

| Failure | Meaning |
|---|---|
| `QUERY_VALIDATION_FAILED` | The question or requested retrieval scope is invalid |
| `QUERY_EMBEDDING_FAILED` | Gemini did not return a valid query vector |
| `RETRIEVAL_FAILED` | The similarity-search database operation failed |
| `NO_RELEVANT_CONTEXT` | No owned chunk passed the relevance threshold |
| `RETRIEVAL_RESULT_INVALID` | The database returned malformed or inconsistent retrieval data |

## Planned Offline Tests

The Phase 5A migration tests will verify:

- RPC creation.
- Service-role-only execution.
- Query-array validation.
- Exact 768-dimensional validation.
- Nonzero query-vector validation.
- Result-count validation.
- Similarity-threshold validation.
- Owner filtering.
- Ready-file filtering.
- Study-file filtering.
- Subject filtering.
- `retrieval_document` filtering.
- Cosine-similarity calculation.
- Descending relevance order.
- Stable chunk-index order.
- Restricted search path.

Normal automated tests will not call hosted Supabase or Gemini.

## Scope Boundary

This design covers vector retrieval only.

It does not yet implement:

- Query-embedding execution.
- Python retrieval orchestration.
- Gemini grounded-answer generation.
- FastAPI chat endpoints.
- Frontend chat interfaces.

Those will be implemented in later Phase 5 checkpoints.
