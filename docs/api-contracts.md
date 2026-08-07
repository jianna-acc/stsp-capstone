<!-- File: /docs/api-contracts.md -->
<!-- Purpose: Documents implemented communication contracts between the frontend, FastAPI backend, worker, AI services, and Supabase. -->

# API Contracts

This document records the implemented application API and important database RPC contracts.

---

# General API Information

| Item | Value |
|---|---|
| Development backend | `http://127.0.0.1:8000` |
| API prefix | `/api` |
| Format | JSON |
| Backend | FastAPI |
| Frontend | Next.js |

Protected student endpoints use:

```http
Authorization: Bearer <Supabase access token>
```

The backend validates the access token and derives the authenticated user ID.

Clients must not submit a trusted `user_id`.

---

# Public Endpoint

## Health Check

```http
GET /api/health
```

Authentication is not required.

Representative response:

```json
{
  "status": "healthy",
  "service": "STS Capstone API",
  "version": "0.1.0",
  "environment": "development"
}
```

---

# Internal File Processing Security

Internal processing routes require:

```http
X-Processor-Key: <private configured value>
```

The value comes from:

```text
backend/.env
```

Environment variable:

```text
PROCESSOR_INTERNAL_KEY
```

The key must never be sent to browser code.

---

# Validate Study File Source

```http
POST /api/internal/file-processing/{file_id}/validate-source
```

Authentication:

```http
X-Processor-Key
```

The backend verifies:

- Study-file row exists
- Processing job exists
- Processing state is valid
- Storage path is valid
- Private object exists
- Object is not empty
- File does not exceed processing limits

Representative response:

```json
{
  "study_file_id": "uuid",
  "processing_job_id": "uuid",
  "filename": "lesson.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 245760,
  "processing_status": "queued",
  "job_status": "queued"
}
```

---

# Process Study File

```http
POST /api/internal/file-processing/{file_id}/process
```

Authentication:

```http
X-Processor-Key
```

The processing workflow performs:

1. Study-file validation
2. Private Storage download
3. Text extraction
4. Source-aware chunking
5. AI preparation
6. Embedding generation
7. Vector persistence
8. Extracted-content persistence
9. Final status update

Representative response:

```json
{
  "study_file_id": "uuid",
  "processing_job_id": "uuid",
  "filename": "lesson.pdf",
  "mime_type": "application/pdf",
  "character_count": 12540,
  "chunk_count": 8,
  "page_count": 6,
  "slide_count": null,
  "sheet_count": null,
  "processing_status": "ready",
  "job_status": "completed"
}
```

---

# Internal Processing Errors

| Status | Meaning |
|---:|---|
| 401 | Processor key missing |
| 403 | Processor key invalid |
| 404 | File, job, or Storage object not found |
| 409 | Invalid processing state |
| 413 | File too large |
| 422 | Content cannot be extracted |
| 500 | Unexpected processing failure |
| 502 | Supabase, Storage, or upstream dependency failure |

Public error bodies must not expose secrets.

---

# Study Assistant RAG Endpoint

## Request

```http
POST /api/rag/answer
Authorization: Bearer <Supabase access token>
Content-Type: application/json
```

Representative request:

```json
{
  "question": "What are the main ideas in my uploaded notes?",
  "conversation_id": "optional-conversation-uuid",
  "subject_id": "optional-subject-uuid",
  "study_file_id": "optional-study-file-uuid",
  "match_count": 5,
  "similarity_threshold": 0.5
}
```

| Field | Required | Description |
|---|---:|---|
| `question` | Yes | Student question |
| `conversation_id` | No | Continues an owned saved conversation |
| `subject_id` | No | Restricts retrieval to one owned subject |
| `study_file_id` | No | Restricts retrieval to one owned ready study file |
| `match_count` | No | Maximum retrieved chunks |
| `similarity_threshold` | No | Minimum similarity |

A first question may omit `conversation_id`.

The backend then creates a conversation and returns its ID.

---

## Answered Response

```json
{
  "conversation_id": "conversation-uuid",
  "outcome": "answered",
  "answer": "The uploaded material explains ... [Source 1]",
  "sources": [
    {
      "source_number": 1,
      "source_name": "Biology Notes.pdf",
      "chunk_index": 2,
      "similarity_score": 0.91
    }
  ],
  "retrieved_count": 3,
  "source_count": 1,
  "context_available": true
}
```

---

## No-Context Response

```json
{
  "conversation_id": "conversation-uuid",
  "outcome": "no_context",
  "answer": "I could not find enough relevant information in your uploaded study materials to answer this question.",
  "sources": [],
  "retrieved_count": 0,
  "source_count": 0,
  "context_available": false
}
```

A no-context result is a normal successful application result.

---

# Saved Conversation API

Base path:

```text
/api/study-conversations
```

All routes require bearer authentication.

---

## Create Conversation

```http
POST /api/study-conversations
```

Representative request:

```json
{
  "title": "Biology review",
  "subject_id": "optional-subject-uuid",
  "study_file_id": "optional-study-file-uuid"
}
```

Successful status:

```text
201 Created
```

Representative response:

```json
{
  "id": "conversation-uuid",
  "title": "Biology review",
  "subject_id": null,
  "study_file_id": null,
  "created_at": "2026-08-07T00:00:00Z",
  "updated_at": "2026-08-07T00:00:00Z",
  "last_message_at": "2026-08-07T00:00:00Z"
}
```

---

## List Conversations

```http
GET /api/study-conversations
```

Optional query parameter:

```text
limit
```

Allowed range:

```text
1 to 50
```

Representative response:

```json
{
  "items": [
    {
      "id": "conversation-uuid",
      "title": "Biology review",
      "subject_id": null,
      "study_file_id": null,
      "created_at": "2026-08-07T00:00:00Z",
      "updated_at": "2026-08-07T00:10:00Z",
      "last_message_at": "2026-08-07T00:10:00Z"
    }
  ]
}
```

Only conversations owned by the authenticated student are returned.

---

## Get Conversation Detail

```http
GET /api/study-conversations/{conversation_id}
```

Optional query parameter:

```text
message_limit
```

Allowed range:

```text
1 to 500
```

Representative response:

```json
{
  "conversation": {
    "id": "conversation-uuid",
    "title": "Biology review",
    "subject_id": null,
    "study_file_id": null,
    "created_at": "2026-08-07T00:00:00Z",
    "updated_at": "2026-08-07T00:10:00Z",
    "last_message_at": "2026-08-07T00:10:00Z"
  },
  "messages": [
    {
      "id": "message-uuid",
      "conversation_id": "conversation-uuid",
      "role": "user",
      "content": "Explain photosynthesis.",
      "outcome": null,
      "sources": [],
      "created_at": "2026-08-07T00:01:00Z"
    }
  ]
}
```

---

## Rename Conversation

```http
PATCH /api/study-conversations/{conversation_id}
```

Current frontend usage:

```json
{
  "title": "Exam reviewer"
}
```

The backend returns the updated conversation.

---

## Delete Conversation

```http
DELETE /api/study-conversations/{conversation_id}
```

Successful response:

```text
204 No Content
```

The frontend must not attempt to parse a JSON body from the 204 response.

---

# Conversation API Errors

Controlled conversation errors use a safe structure such as:

```json
{
  "error_code": "CONVERSATION_NOT_FOUND",
  "message": "The conversation could not be found."
}
```

Possible controlled conditions include:

- Missing conversation
- Unowned conversation
- Invalid filters
- Invalid title
- Conflicting subject/file filters
- Authentication failure

---

# Conversation Security Contract

The frontend may send:

```text
conversation_id
question
subject_id
study_file_id
title
```

The frontend must not send:

```text
user_id
conversation memory
summary_text
summarized_message_count
summary_updated_at
summary_version
raw embeddings
raw retrieved chunks
```

---

# File Processing Worker Contract

Worker module:

```text
backend/app/workers/file_processing_worker.py
```

Typical development command:

```bash
python -m app.workers.file_processing_worker \
  --poll-seconds 2 \
  --recovery-interval-seconds 30 \
  --stale-after-minutes 30 \
  --max-attempts 3
```

Important options:

| Option | Purpose |
|---|---|
| `--once` | Process at most one job |
| `--poll-seconds` | Empty-queue delay |
| `--recovery-interval-seconds` | Stale-recovery interval |
| `--stale-after-minutes` | Stale threshold |
| `--max-attempts` | Permanent-failure threshold |

---

# Important Database RPC Contracts

## Queue Processing

```text
public.queue_study_file_processing(uuid)
```

## Claim Next Job

```text
public.claim_next_file_processing_job()
```

Uses atomic locking and `SKIP LOCKED`.

## Start Processing

```text
public.start_study_file_processing(uuid)
```

## Mark Indexing

```text
public.mark_study_file_indexing(uuid)
```

## Complete Processing

```text
public.complete_study_file_processing(...)
```

## Fail Processing

```text
public.fail_study_file_processing(...)
```

## Recover Stale Jobs

```text
public.recover_stale_file_processing_jobs(integer, integer)
```

## Replace AI Vector Chunks

```text
public.replace_study_file_ai_chunks(...)
```

Persists validated backend-generated AI chunks and vectors.

## Complete Learning Profile

```text
public.complete_learning_profile_onboarding()
```

---

# HTTP Security Rules

Public responses must never expose:

- Supabase secret key
- Processor key
- Gemini API key
- Database password
- Access tokens
- Raw environment variables
- Raw embeddings
- Private Storage credentials
- Provider tracebacks

---

# OpenAPI Verification

Start FastAPI and open:

```text
http://127.0.0.1:8000/docs
```

Important implemented routes include:

```text
GET    /api/health

POST   /api/internal/file-processing/{file_id}/validate-source
POST   /api/internal/file-processing/{file_id}/process

POST   /api/rag/answer

POST   /api/study-conversations
GET    /api/study-conversations
GET    /api/study-conversations/{conversation_id}
PATCH  /api/study-conversations/{conversation_id}
DELETE /api/study-conversations/{conversation_id}
```

---

# API Change Rules

When an API or RPC changes:

1. Update the schema.
2. Update the implementation.
3. Update automated tests.
4. Update frontend consumers.
5. Update this file.
6. Update `ARCHITECTURE.md`.
7. Update `PROJECT_FILE_MAP.md`.
8. Use a new migration for database-function changes.
9. Regenerate database types after schema changes.
10. Re-run frontend and backend regression tests.