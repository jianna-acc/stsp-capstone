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

## Create Quiz With Questions

```text
public.create_quiz_with_questions(...)
```

Atomically persists Quiz metadata and its private generated questions.

## Start Quiz Attempt

```text
public.start_quiz_attempt(...)
```

Creates one fresh owned Quiz attempt through the trusted backend.

## Submit Quiz Attempt Answer

```text
public.submit_quiz_attempt_answer(...)
```

Atomically validates attempt state, grades the expected question, stores safe submitted-answer history, and advances or completes the attempt.

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
# Reviewer API

Reviewer endpoints require authenticated Supabase bearer authentication.

The backend derives the trusted student identity from the validated access token. Reviewer requests must not provide or override `user_id`.

---

## Generate Reviewer

```http
POST /api/reviewers/generate
```

The endpoint generates and saves one reviewer from processed study material owned by the authenticated student.

Supported scopes:

```text
file
subject
```

Supported reviewer lengths:

```text
short
medium
long
```

### File-Scope Request

```json
{
  "scope_type": "file",
  "subject_id": "subject-uuid",
  "study_file_id": "study-file-uuid",
  "reviewer_length": "medium"
}
```

For file scope:

- `subject_id` is required.
- `study_file_id` is required.
- The selected file must belong to the authenticated student.
- The file must belong to the selected subject.
- The file must be in the `ready` processing state.

### Subject-Scope Request

```json
{
  "scope_type": "subject",
  "subject_id": "subject-uuid",
  "study_file_id": null,
  "reviewer_length": "long"
}
```

For subject scope:

- `subject_id` is required.
- `study_file_id` must be omitted or `null`.
- Reviewer generation uses ready study files owned by the authenticated student within that subject.

Reviewer generation loads processed source-aware chunks in deterministic file and chunk order.

It does not use similarity-based RAG retrieval.

---

## Reviewer Response

Representative response:

```json
{
  "id": "reviewer-uuid",
  "subject_id": "subject-uuid",
  "study_file_id": "study-file-uuid",
  "scope_type": "file",
  "title": "Biology Notes Reviewer",
  "reviewer_length": "medium",
  "content": {
    "overview": "Overview of the selected study material.",
    "topics": [
      {
        "title": "Photosynthesis",
        "summary": "Summary of the topic.",
        "key_points": [
          "Plants convert light energy into chemical energy."
        ],
        "definitions": [
          {
            "term": "Photosynthesis",
            "definition": "Definition grounded in the selected material."
          }
        ]
      }
    ]
  },
  "sources": [
    {
      "study_file_id": "study-file-uuid",
      "source_name": "Biology Notes.pdf",
      "chunk_index": 0,
      "locator_type": "page",
      "locator_label": "Page 1"
    }
  ],
  "generation_model": "gemini-generation-model",
  "generation_count": 1,
  "generated_at": "2026-08-07T00:00:00Z",
  "created_at": "2026-08-07T00:00:00Z",
  "updated_at": "2026-08-07T00:00:00Z"
}
```

The response does not expose a trusted `user_id`.

The `sources` array records which processed study-file chunks were used for the reviewer.

---

## List Reviewers

```http
GET /api/reviewers
```

Optional query parameter:

```text
limit
```

Valid range:

```text
1 to 100
```

Default:

```text
20
```

Representative response:

```json
{
  "items": [
    {
      "id": "reviewer-uuid",
      "subject_id": "subject-uuid",
      "study_file_id": "study-file-uuid",
      "scope_type": "file",
      "title": "Biology Notes Reviewer",
      "reviewer_length": "medium",
      "content": {
        "overview": "Overview.",
        "topics": []
      },
      "sources": [],
      "generation_model": "gemini-generation-model",
      "generation_count": 1,
      "generated_at": "2026-08-07T00:00:00Z",
      "created_at": "2026-08-07T00:00:00Z",
      "updated_at": "2026-08-07T00:00:00Z"
    }
  ]
}
```

Only reviewers owned by the authenticated student are returned.

---

## Get Reviewer

```http
GET /api/reviewers/{reviewer_id}
```

Returns one reviewer owned by the authenticated student.

A reviewer that does not exist or is not owned by the authenticated student returns a safe not-found response.

---

## Delete Reviewer

```http
DELETE /api/reviewers/{reviewer_id}
```

Successful response:

```text
204 No Content
```

The client must not attempt to parse a JSON body from the successful 204 response.

---

# Reviewer API Errors

Controlled reviewer errors use:

```json
{
  "error_code": "REVIEWER_NOT_FOUND",
  "message": "The requested reviewer or study material was not found."
}
```

Current controlled error mappings include:

| HTTP | Error Code | Meaning |
|---|---|---|
| `400` | `REVIEWER_VALIDATION_FAILED` | Reviewer operation is invalid |
| `404` | `REVIEWER_NOT_FOUND` | Reviewer or owned source material was not found |
| `409` | `REVIEWER_SOURCE_UNAVAILABLE` | Selected source material is not ready or usable |
| `500` | `REVIEWER_GENERATION_RESPONSE_FAILED` | Generated reviewer output could not be processed |
| `500` | `REVIEWER_RESPONSE_FAILED` | Reviewer response could not be completed |
| `502` | `REVIEWER_GENERATION_FAILED` | AI generation provider failed |
| `503` | `REVIEWER_PERSISTENCE_FAILED` | Reviewer storage is temporarily unavailable |
| `503` | `REVIEWER_SOURCE_STORAGE_FAILED` | Study-material source loading is temporarily unavailable |

Authentication failures continue to use the existing protected-API authentication behavior.

---

# Reviewer Security Contract

Reviewer API security requirements:

1. The authenticated bearer token determines the trusted student identity.
2. The request body cannot choose `user_id`.
3. File-scope reviewers must use a study file owned by the authenticated student.
4. Subject-scope reviewers only load ready files owned by the authenticated student.
5. Reviewer source chunks are loaded through trusted backend operations.
6. Browser clients cannot directly insert or update reviewer records.
7. Saved reviewer reads and deletes remain ownership scoped.
8. Generated reviewer content must be grounded in the selected processed study material.
9. Study-material content is treated as untrusted prompt content.
10. Raw backend secrets, provider errors, and database details must not appear in public API errors.

---

# Flashcard API

Flashcard endpoints require authenticated Supabase bearer authentication.

The backend derives the trusted student identity from the validated access token. Flashcard requests must not provide or override `user_id`.

---

## Generate Flashcards

```http
POST /api/flashcards/generate
```

The endpoint generates and saves one Flashcard deck from processed study material owned by the authenticated student.

Supported scopes:

```text
file
subject
```

Supported card count:

```text
minimum: 5
default: 20
maximum: 50
```

### File-Scope Request

```json
{
  "scope_type": "file",
  "subject_id": "subject-uuid",
  "study_file_id": "study-file-uuid",
  "card_count": 20
}
```

For file scope:

- `subject_id` is required.
- `study_file_id` is required.
- The selected file must belong to the authenticated student.
- The selected file must belong to the selected subject.
- The file must be in the `ready` processing state.

### Subject-Scope Request

```json
{
  "scope_type": "subject",
  "subject_id": "subject-uuid",
  "study_file_id": null,
  "card_count": 20
}
```

For subject scope:

- `subject_id` is required.
- `study_file_id` must be omitted or `null`.
- Generation uses ready study files owned by the authenticated student within the selected subject.

Flashcard generation loads processed source-aware chunks in deterministic file and chunk order.

It does not use similarity-based RAG retrieval.

Flashcard generation supports both normal single-pass and large-material multi-pass processing.

For source collections at or below 80,000 characters, generation uses one complete source-grounded prompt.

For source collections above 80,000 characters, the backend partitions the complete ordered source bundle into deterministic batches with a default maximum of 60,000 source characters per batch.

Batching occurs only at existing source-chunk boundaries. Source chunks are not silently truncated, dropped, duplicated, or reordered.

Each batch produces validated candidate Flashcards. The backend then performs a final synthesis pass over the ordered candidate decks and returns exactly the number of Flashcards requested by the student.

The final persisted deck continues to reference the complete original source bundle rather than the intermediate candidate generations.

Large-material processing does not change the public `POST /api/flashcards/generate` request or response contract.


---

## Flashcard Deck Response

Representative response:

```json
{
  "id": "deck-uuid",
  "subject_id": "subject-uuid",
  "study_file_id": "study-file-uuid",
  "scope_type": "file",
  "title": "Biology Notes Flashcards",
  "requested_card_count": 5,
  "cards": [
    {
      "question": "What is photosynthesis?",
      "answer": "The process described in the selected study material."
    }
  ],
  "sources": [
    {
      "study_file_id": "study-file-uuid",
      "source_name": "Biology Notes.pdf",
      "chunk_index": 0,
      "locator_type": "page",
      "locator_label": "Page 1"
    }
  ],
  "generation_model": "gemini-generation-model",
  "generation_count": 1,
  "generated_at": "2026-08-09T00:00:00Z",
  "created_at": "2026-08-09T00:00:00Z",
  "updated_at": "2026-08-09T00:00:00Z"
}
```

The response does not expose a trusted `user_id`.

The `cards` array contains the validated ordered question-and-answer cards.

The `sources` array contains safe metadata for the processed study-file chunks used during generation.

---

## List Flashcard Decks

```http
GET /api/flashcards
```

Optional query parameter:

```text
subject_id
```

When supplied, only saved decks for that owned subject are returned.

Representative response:

```json
{
  "items": [
    {
      "id": "deck-uuid",
      "subject_id": "subject-uuid",
      "study_file_id": "study-file-uuid",
      "scope_type": "file",
      "title": "Biology Notes Flashcards",
      "requested_card_count": 20,
      "generation_model": "gemini-generation-model",
      "generation_count": 1,
      "generated_at": "2026-08-09T00:00:00Z",
      "created_at": "2026-08-09T00:00:00Z",
      "updated_at": "2026-08-09T00:00:00Z"
    }
  ]
}
```

Only Flashcard decks owned by the authenticated student are returned.

---

## Get Flashcard Deck

```http
GET /api/flashcards/{deck_id}
```

Returns one complete Flashcard deck owned by the authenticated student.

A deck that does not exist or is not owned by the authenticated student returns a safe not-found response.

---

## Delete Flashcard Deck

```http
DELETE /api/flashcards/{deck_id}
```

Successful response:

```text
204 No Content
```

Deleting the deck also removes its child Flashcards through database cascade behavior.

The client must not attempt to parse a JSON body from a successful `204` response.

---

## Record Flashcard Review

```http
POST /api/flashcards/{deck_id}/reviews
```

Persists one authenticated student self-assessment for a Flashcard after its answer is revealed.

Representative request:

```json
{
  "card_position": 0,
  "outcome": "known"
}
```

Supported outcomes:

```text
known
review_again
```

Representative response:

```json
{
  "id": "review-uuid",
  "deck_id": "deck-uuid",
  "card_position": 0,
  "outcome": "known",
  "reviewed_at": "2026-08-11T08:00:00Z"
}
```

The authenticated student's UUID is derived from the bearer token and cannot be supplied by the request body.

The backend verifies that:

- the deck belongs to the authenticated student;
- the requested card position exists in that deck;
- the outcome is one of the supported self-assessment values.

Successful status:

```text
201 Created
```

---

# Flashcard API Errors

Controlled Flashcard errors use:

```json
{
  "error_code": "FLASHCARD_NOT_FOUND",
  "message": "The requested Flashcard deck was not found."
}
```

Current controlled mappings include:

| HTTP | Error Code | Meaning |
|---|---|---|
| `400` | `FLASHCARD_VALIDATION_FAILED` | Flashcard operation is invalid |
| `404` | `FLASHCARD_NOT_FOUND` | Deck or owned source material was not found |
| `409` | `FLASHCARD_SOURCE_UNAVAILABLE` | Selected study material is not ready |
| `500` | `FLASHCARD_GENERATION_RESPONSE_FAILED` | Generated Flashcard output could not be processed |
| `500` | `FLASHCARD_RESPONSE_FAILED` | Flashcard response could not be completed |
| `502` | `FLASHCARD_GENERATION_FAILED` | AI generation provider failed |
| `503` | `FLASHCARD_PERSISTENCE_FAILED` | Flashcard storage is temporarily unavailable |
| `503` | `FLASHCARD_SOURCE_STORAGE_FAILED` | Study-material source loading is temporarily unavailable |
| `400` | Flashcard review validation failure | Review request is invalid |
| `404` | Flashcard review target not found | Deck/card review target is missing or not owned |
| `500` | Flashcard review response failure | Persisted review response could not be processed |
| `503` | Flashcard review persistence failure | Review storage is temporarily unavailable |

Authentication failures continue to use the existing protected-API authentication behavior.

---

# Flashcard Security Contract

Flashcard API security requirements:

1. The authenticated bearer token determines the trusted student identity.
2. The request body cannot choose `user_id`.
3. File-scope generation must use a study file owned by the authenticated student.
4. Subject-scope generation loads only ready files owned by the authenticated student.
5. Source chunks are loaded through trusted backend operations.
6. Browser clients cannot directly create generated Flashcard decks or cards.
7. The trusted persistence RPC is executable only by the backend `service_role`.
8. Saved-deck reads and deletes remain ownership scoped.
9. Generated Flashcard content must be grounded in selected processed study material.
10. Study-material content is treated as untrusted prompt content.
11. Generated output must pass schema, exact-card-count, and duplicate validation before persistence.
12. Raw backend secrets, provider errors, and database details must not appear in public API errors.
13. Flashcard review requests cannot provide a trusted `user_id`.
14. Flashcard reviews are accepted only for owned decks and valid card positions.
15. Browser clients cannot directly insert `flashcard_review_events`; writes pass through the trusted backend.
16. Authenticated browser reads of Flashcard review events are owner-scoped through RLS.

---

# Quiz API

Quiz endpoints require authenticated Supabase bearer authentication.

The backend derives the trusted student identity from the validated access token. Quiz requests cannot provide or override `user_id`.

## Generate Quiz

```http
POST /api/quizzes/generate
```

Representative subject-scope request:

```json
{
  "scope_type": "subject",
  "subject_id": "subject-uuid",
  "study_file_id": null,
  "quiz_type": "mixed",
  "difficulty": "medium",
  "question_count": 10
}
```

Representative file-scope request:

```json
{
  "scope_type": "file",
  "subject_id": "subject-uuid",
  "study_file_id": "study-file-uuid",
  "quiz_type": "multiple_choice",
  "difficulty": "hard",
  "question_count": 10
}
```

Supported Quiz types:

```text
multiple_choice
true_false
identification
mixed
```

Supported difficulty:

```text
easy
medium
hard
```

Question count:

```text
1 to 50
```

For file scope, the selected study file must be owned by the authenticated student, belong to the selected subject, and be in the `ready` processing state.

Subject scope uses owned ready study materials from the selected subject.

Quiz generation loads processed source-aware chunks and generates structured Quiz content grounded in the selected material.

### Student-Safe Quiz Response

Representative shape:

```json
{
  "id": "quiz-uuid",
  "subject_id": "subject-uuid",
  "study_file_id": null,
  "scope_type": "subject",
  "title": "Biology Practice Quiz",
  "quiz_type": "mixed",
  "difficulty": "medium",
  "question_count": 2,
  "questions": [
    {
      "id": "question-uuid",
      "position": 1,
      "question_type": "multiple_choice",
      "topic": "Cells",
      "question": "Which structure contains genetic material?",
      "choices": [
        "Nucleus",
        "Cell wall",
        "Cytoplasm",
        "Ribosome"
      ]
    }
  ],
  "generation_model": "configured-generation-model",
  "generation_count": 1,
  "generated_at": "2026-08-10T00:00:00Z",
  "created_at": "2026-08-10T00:00:00Z",
  "updated_at": "2026-08-10T00:00:00Z"
}
```

Normal Quiz responses deliberately exclude:

```text
correct_answer
accepted_answers
explanation
```

---

## List Saved Quizzes

```http
GET /api/quizzes
```

Returns saved Quizzes owned by the authenticated student, newest first.

Each item includes safe Quiz metadata plus:

```text
attempt_count
latest_attempt
```

`latest_attempt` is `null` when the Quiz has never been started.

---

## Get Saved Quiz

```http
GET /api/quizzes/{quiz_id}
```

Returns one owned saved Quiz with public question fields.

Private answer-key fields are not included.

---

## Delete Saved Quiz

```http
DELETE /api/quizzes/{quiz_id}
```

Successful response:

```text
204 No Content
```

Deleting a Quiz removes the related Quiz questions and attempt history through configured database cascades.

The frontend requires confirmation before requesting deletion.

---

# Quiz Attempt API

## Start Attempt

```http
POST /api/quizzes/{quiz_id}/attempts
```

Starts a fresh attempt for one owned saved Quiz.

Successful status:

```text
201 Created
```

Representative response:

```json
{
  "id": "attempt-uuid",
  "quiz_id": "quiz-uuid",
  "status": "in_progress",
  "current_position": 1,
  "correct_count": 0,
  "question_count": 10,
  "score_percentage": 0,
  "started_at": "2026-08-10T00:00:00Z",
  "completed_at": null,
  "created_at": "2026-08-10T00:00:00Z",
  "updated_at": "2026-08-10T00:00:00Z"
}
```

---

## List Quiz Attempts

```http
GET /api/quizzes/{quiz_id}/attempts
```

Returns attempts for one owned Quiz, newest first.

Representative response:

```json
{
  "quiz_id": "quiz-uuid",
  "items": []
}
```

---

## Get Attempt

```http
GET /api/quiz-attempts/{attempt_id}
```

Returns the current public state of one owned Quiz attempt.

---

## Submit Answer

```http
POST /api/quiz-attempts/{attempt_id}/questions/{position}/answer
```

Representative request:

```json
{
  "answer": "Nucleus"
}
```

The backend atomically validates the expected position, grades the answer, stores the submitted-answer history, and advances the attempt.

Representative response:

```json
{
  "attempt": {
    "id": "attempt-uuid",
    "quiz_id": "quiz-uuid",
    "status": "in_progress",
    "current_position": 2,
    "correct_count": 1,
    "question_count": 10,
    "score_percentage": 10,
    "started_at": "2026-08-10T00:00:00Z",
    "completed_at": null,
    "created_at": "2026-08-10T00:00:00Z",
    "updated_at": "2026-08-10T00:01:00Z"
  },
  "feedback": {
    "attempt_id": "attempt-uuid",
    "quiz_question_id": "question-uuid",
    "position": 1,
    "is_correct": true,
    "correct_answer": "Nucleus",
    "explanation": "Explanation grounded in the generated Quiz content.",
    "next_position": 2,
    "attempt_completed": false
  }
}
```

Immediate feedback is returned only after that answer has been submitted.

---

## Get Final Result

```http
GET /api/quiz-attempts/{attempt_id}/result
```

Results are available only for a completed owned attempt.

Representative response:

```json
{
  "attempt_id": "attempt-uuid",
  "quiz_id": "quiz-uuid",
  "correct_count": 8,
  "question_count": 10,
  "score_percentage": 80,
  "strong_topics": [
    {
      "topic": "Cells",
      "correct_count": 4,
      "question_count": 5,
      "accuracy_percentage": 80
    }
  ],
  "weak_topics": [],
  "completed_at": "2026-08-10T00:10:00Z"
}
```

Topic classification threshold:

```text
Strong: accuracy >= 70%
Weak:   accuracy < 70%
```

---

## Review Completed Attempt

```http
GET /api/quiz-attempts/{attempt_id}/review
```

Review is available only after an owned attempt is completed.

The response contains the completed attempt, final result, and reviewed answers including:

```text
question
submitted_answer
is_correct
correct_answer
explanation
answered_at
```

An in-progress attempt returns a controlled conflict response instead of exposing the full answer key.

---

# Quiz API Errors

Quiz-generation controlled errors include:

| HTTP | Error Code | Meaning |
|---|---|---|
| `400` | `QUIZ_VALIDATION_FAILED` | Quiz operation is invalid |
| `404` | `QUIZ_NOT_FOUND` | Quiz or owned source material was not found |
| `409` | `QUIZ_SOURCE_UNAVAILABLE` | Selected study material is not ready |
| `500` | `QUIZ_GENERATION_RESPONSE_FAILED` | Generated Quiz output could not be processed |
| `500` | `QUIZ_RESPONSE_FAILED` | Quiz response could not be completed |
| `502` | `QUIZ_GENERATION_FAILED` | AI generation failed |
| `503` | `QUIZ_PERSISTENCE_FAILED` | Quiz storage is temporarily unavailable |
| `503` | `QUIZ_SOURCE_STORAGE_FAILED` | Study-material loading is temporarily unavailable |

Quiz-attempt controlled errors include:

| HTTP | Error Code | Meaning |
|---|---|---|
| `400` | `QUIZ_ATTEMPT_VALIDATION_FAILED` | Attempt request is invalid |
| `404` | `QUIZ_ATTEMPT_NOT_FOUND` | Quiz or attempt was not found |
| `409` | `QUIZ_ATTEMPT_CONFLICT` | Attempt is not in the required state |
| `500` | `QUIZ_ATTEMPT_RESPONSE_FAILED` | Attempt response could not be completed |
| `503` | `QUIZ_ATTEMPT_PERSISTENCE_FAILED` | Attempt storage is temporarily unavailable |

---

# Quiz Security Contract

1. Bearer authentication determines the trusted student identity.
2. Quiz requests cannot choose `user_id`.
3. File and subject source loading is ownership scoped.
4. Normal Quiz responses exclude correct answers, accepted answers, and explanations.
5. `quiz_questions` answer-key data is accessed through trusted backend operations.
6. Starting and submitting attempts uses trusted RPCs rather than browser table writes.
7. Answer submission validates the expected current question position atomically.
8. Full attempt review is unavailable until the owned attempt is completed.
9. Saved Quiz listing, retrieval, attempt history, review, and deletion are ownership scoped.
10. Public errors must not expose provider traces, database details, tokens, or secrets.


# Analytics API

Analytics endpoints require authenticated Supabase bearer authentication.

The backend derives the trusted student UUID from the validated bearer token.

Analytics requests cannot provide or override `user_id`.

## Get Analytics Overview

```http
GET /api/analytics/overview
```

Optional query parameter:

```text
period
```

Supported values:

```text
all_time
last_7_days
last_30_days
```

Default:

```text
all_time
```

Representative response:

```json
{
  "period": "all_time",
  "data_state": "partial",
  "subject_count": {
    "availability": "available",
    "value": 3,
    "scope": "current_inventory",
    "message": null
  },
  "study_material_count": {
    "availability": "available",
    "value": 8,
    "scope": "current_inventory",
    "message": null
  },
  "ready_study_material_count": {
    "availability": "available",
    "value": 6,
    "scope": "current_inventory",
    "message": null
  },
  "quiz_accuracy_percent": {
    "availability": "available",
    "value": 80.0,
    "sample_size": 10,
    "message": null
  },
  "flashcard_performance_percent": {
    "availability": "available",
    "value": 75.0,
    "sample_size": 8,
    "message": null
  },
  "study_minutes": {
    "availability": "unavailable",
    "value": null,
    "sample_size": 0,
    "message": "General study duration is unavailable because no canonical study-activity duration source exists yet."
  },
  "strong_topics": [
    {
      "topic": "Algebra",
      "score_percent": 75.0,
      "sample_size": 4
    }
  ],
  "weak_topics": [
    {
      "topic": "Biology",
      "score_percent": 50.0,
      "sample_size": 4
    }
  ]
}
```

Current canonical data sources are:

```text
subjects
study_files
quiz_attempts
quiz_attempt_answers
flashcard_review_events
```

Inventory counts represent current stored resources and are not period-filtered.

Quiz accuracy uses completed attempts and is weighted by total completed question count.

Strong and weak Quiz topics follow Track B's 70% classification threshold.

Flashcard performance is a self-assessment metric calculated from persisted `known` and `review_again` review events.

General study minutes remain explicitly unavailable until a canonical duration source exists.

If the selected period has no completed Quiz attempts or no Flashcard review events, the corresponding source remains available while the metric value is `null` with `sample_size = 0`.

## Analytics Errors

| HTTP | Meaning |
|---|---|
| `401` | Authentication is missing, invalid, or expired |
| `422` | Reporting period is unsupported |
| `503` | Canonical Analytics data is temporarily unavailable |

## Analytics Security Contract

1. Bearer authentication determines the trusted student identity.
2. Analytics requests cannot choose `user_id`.
3. Subject and study-material queries are owner-scoped.
4. Quiz attempts are filtered to the authenticated student.
5. Topic evidence is read only for the selected owned completed attempts.
6. Flashcard review evidence is filtered to the authenticated student.
7. Analytics does not expose Quiz answer keys.
8. Controlled failures do not expose database credentials, backend secrets, or provider traces.

The Flashcard review persistence migration may be present on the Track E branch before it is applied to the shared remote database. Shared database application must be coordinated when other team migrations are in progress.

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

POST   /api/reviewers/generate
GET    /api/reviewers
GET    /api/reviewers/{reviewer_id}
DELETE /api/reviewers/{reviewer_id}

POST   /api/flashcards/generate
GET    /api/flashcards
GET    /api/flashcards/{deck_id}
POST   /api/flashcards/{deck_id}/reviews
DELETE /api/flashcards/{deck_id}

GET    /api/analytics/overview

POST   /api/quizzes/generate
GET    /api/quizzes
GET    /api/quizzes/{quiz_id}
DELETE /api/quizzes/{quiz_id}
GET    /api/quizzes/{quiz_id}/attempts
POST   /api/quizzes/{quiz_id}/attempts
GET    /api/quiz-attempts/{attempt_id}
POST   /api/quiz-attempts/{attempt_id}/questions/{position}/answer
GET    /api/quiz-attempts/{attempt_id}/result
GET    /api/quiz-attempts/{attempt_id}/review
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