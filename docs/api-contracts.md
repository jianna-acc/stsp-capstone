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

Only conversations owned by the authenticated student are returned.

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

## Rename Conversation

```http
PATCH /api/study-conversations/{conversation_id}
```

Representative request:

```json
{
  "title": "Exam reviewer"
}
```

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

## Replace Learning Output Confidences

```text
public.replace_learning_output_confidences(...)
```

Persists the authenticated student's academic output-confidence values.

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

The backend derives the trusted student identity from the validated access token.

Reviewer requests must not provide or override `user_id`.

## Generate Reviewer

```http
POST /api/reviewers/generate
```

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

### Subject-Scope Request

```json
{
  "scope_type": "subject",
  "subject_id": "subject-uuid",
  "study_file_id": null,
  "reviewer_length": "long"
}
```

Reviewer generation loads processed source-aware chunks in deterministic file and chunk order.

It does not use similarity-based RAG retrieval.

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

## Get Reviewer

```http
GET /api/reviewers/{reviewer_id}
```

Returns one reviewer owned by the authenticated student.

## Delete Reviewer

```http
DELETE /api/reviewers/{reviewer_id}
```

Successful response:

```text
204 No Content
```

## Regenerate Reviewer

```http
POST /api/reviewers/{reviewer_id}/regenerate
```

Regenerates an existing reviewer using its authenticated owner and persisted reviewer scope.

The request cannot override the trusted owner.

---

# Reviewer API Errors

Controlled reviewer errors use safe public error responses.

Current controlled mappings include:

| HTTP | Error Code | Meaning |
|---:|---|---|
| `400` | `REVIEWER_VALIDATION_FAILED` | Reviewer operation is invalid |
| `404` | `REVIEWER_NOT_FOUND` | Reviewer or owned source material was not found |
| `409` | `REVIEWER_SOURCE_UNAVAILABLE` | Selected source material is not ready or usable |
| `500` | `REVIEWER_GENERATION_RESPONSE_FAILED` | Generated reviewer output could not be processed |
| `500` | `REVIEWER_RESPONSE_FAILED` | Reviewer response could not be completed |
| `502` | `REVIEWER_GENERATION_FAILED` | AI generation provider failed |
| `503` | `REVIEWER_PERSISTENCE_FAILED` | Reviewer storage is temporarily unavailable |
| `503` | `REVIEWER_SOURCE_STORAGE_FAILED` | Study-material source loading is temporarily unavailable |

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
8. Generated reviewer content must be grounded in selected processed study material.
9. Study-material content is treated as untrusted prompt content.
10. Raw backend secrets, provider errors, and database details must not appear in public API errors.

---

# Academic Tasks API

Base path:

```text
/api/academic-tasks
```

All Academic Task routes require:

```http
Authorization: Bearer <Supabase access token>
```

The backend derives the trusted student identity from the validated bearer token.

Clients must not submit a trusted `user_id`.

Supported difficulty values:

```text
easy
medium
hard
```

Supported task types:

```text
assignment
project
exam
quiz
reading
presentation
research
other
```

Supported academic output types:

```text
writing
computation
research
presentation
creative
reading_analysis
memorization
mixed
other
```

Supported statuses:

```text
pending
in_progress
completed
cancelled
```

## Create Academic Task

```http
POST /api/academic-tasks
```

Successful status:

```text
201 Created
```

Representative request:

```json
{
  "subject_id": "subject-uuid",
  "title": "Final research paper",
  "description": "Complete the final draft.",
  "deadline": "2026-08-20T12:00:00Z",
  "estimated_minutes": 180,
  "difficulty": "hard",
  "task_type": "assignment",
  "output_type": "writing"
}
```

`status` is not required during creation and defaults to:

```text
pending
```

Representative response:

```json
{
  "id": "task-uuid",
  "subject_id": "subject-uuid",
  "title": "Final research paper",
  "description": "Complete the final draft.",
  "deadline": "2026-08-20T12:00:00Z",
  "estimated_minutes": 180,
  "difficulty": "hard",
  "task_type": "assignment",
  "output_type": "writing",
  "status": "pending",
  "created_at": "2026-08-09T12:00:00Z",
  "updated_at": "2026-08-09T12:00:00Z"
}
```

The selected subject must belong to the authenticated student.

---

## List Academic Tasks

```http
GET /api/academic-tasks
```

Optional query parameter:

| Parameter | Type | Default | Rules |
|---|---|---:|---|
| `limit` | integer | 100 | 1–100 |

Representative response:

```json
{
  "items": [
    {
      "id": "task-uuid",
      "subject_id": "subject-uuid",
      "title": "Final research paper",
      "description": null,
      "deadline": "2026-08-20T12:00:00Z",
      "estimated_minutes": 180,
      "difficulty": "hard",
      "task_type": "assignment",
      "output_type": "writing",
      "status": "pending",
      "created_at": "2026-08-09T12:00:00Z",
      "updated_at": "2026-08-09T12:00:00Z"
    }
  ]
}
```

Only tasks owned by the authenticated student are returned.

---

## List Prioritized Academic Tasks

```http
GET /api/academic-tasks/prioritized
```

Optional query parameter:

| Parameter | Type | Default | Rules |
|---|---|---:|---|
| `limit` | integer | 100 | 1–100 |

Representative response:

```json
{
  "items": [
    {
      "task": {
        "id": "task-uuid",
        "subject_id": "subject-uuid",
        "title": "Final research paper",
        "description": null,
        "deadline": "2026-08-20T12:00:00Z",
        "estimated_minutes": 180,
        "difficulty": "hard",
        "task_type": "assignment",
        "output_type": "writing",
        "status": "pending",
        "created_at": "2026-08-09T12:00:00Z",
        "updated_at": "2026-08-09T12:00:00Z"
      },
      "priority": {
        "total_score": 72.5,
        "deadline_score": 85.0,
        "difficulty_score": 100.0,
        "estimated_time_score": 60.0,
        "output_confidence_score": 75.0,
        "previous_performance_score": 50.0,
        "available_study_time_score": 80.0,
        "status_score": 50.0
      }
    }
  ]
}
```

Tasks are sorted deterministically by:

```text
1. total_score descending
2. deadline ascending
3. created_at ascending
4. task ID
```

The browser does not calculate or override the priority score.

---

## Get Academic Task

```http
GET /api/academic-tasks/{task_id}
```

Returns one Academic Task owned by the authenticated student.

Missing or unowned tasks receive the same safe not-found response.

---

## Update Academic Task

```http
PATCH /api/academic-tasks/{task_id}
```

Editable fields are:

```text
subject_id
title
description
deadline
estimated_minutes
difficulty
task_type
output_type
```

Representative request:

```json
{
  "deadline": "2026-08-25T12:00:00Z",
  "estimated_minutes": 90,
  "difficulty": "medium",
  "output_type": "research"
}
```

The response is the updated Academic Task.

Task status is intentionally changed through the dedicated status endpoint.

---

## Change Academic Task Status

```http
PATCH /api/academic-tasks/{task_id}/status
```

Representative request:

```json
{
  "status": "in_progress"
}
```

The response contains the updated Academic Task.

The Academic Tasks frontend requests the prioritized endpoint again after a successful status change.

Completed and cancelled tasks receive:

```text
total priority = 0
```

---

## Delete Academic Task

```http
DELETE /api/academic-tasks/{task_id}
```

Successful response:

```text
204 No Content
```

The client must not attempt to parse JSON from the successful 204 response.

---

# Academic Task Priority Contract

Priority calculation is deterministic and backend-owned.

The configured factors are:

| Factor | Weight |
|---|---:|
| Deadline proximity | 30% |
| Difficulty | 20% |
| Estimated completion time | 15% |
| Academic output confidence | 15% |
| Previous performance | 10% |
| Available study time | 5% |
| Task status | 5% |

Priority context is loaded from authenticated student data.

The browser cannot submit a trusted calculated priority.

Previous performance currently uses a neutral fallback until a real performance subsystem is connected.

---

# Academic Task Error Contract

Controlled Academic Task errors include:

| HTTP | Error Code | Meaning |
|---:|---|---|
| `400` | `ACADEMIC_TASK_VALIDATION_FAILED` | Academic Task request is invalid |
| `404` | `ACADEMIC_TASK_NOT_FOUND` | Task does not exist or is not owned by the authenticated student |
| `500` | `ACADEMIC_TASK_RESPONSE_FAILED` | Stored Academic Task data could not be processed |
| `500` | `ACADEMIC_TASK_FAILED` | Unexpected Academic Task operation failure |
| `503` | `ACADEMIC_TASK_PERSISTENCE_FAILED` | Academic Task storage is temporarily unavailable |

Authentication failures use the existing protected-API authentication behavior.

---

# Academic Task Security Contract

Academic Task API security requirements:

1. The bearer token determines the trusted student identity.
2. Request bodies cannot select or override `user_id`.
3. Academic Tasks are scoped to their authenticated owner.
4. Selected subjects must belong to the same student.
5. Database Row Level Security protects direct student access.
6. Priority context is loaded by trusted backend services.
7. The browser cannot submit a trusted priority score.
8. The browser cannot submit trusted study availability or output-confidence context for priority calculation.
9. Priority calculation does not call Gemini.
10. Public errors must not expose backend credentials, tokens, SQL details, or stack traces.

---
# Study Plan API

All Study Plan endpoints require authenticated bearer access.

The authenticated student identity is derived from the bearer token and cannot be supplied through request bodies.

## Create Manual Study Plan

```http
POST /api/study-plans
```

Representative request:

```json
{
  "title": "Finals Study Plan",
  "starts_on": "2026-08-11",
  "ends_on": "2026-08-17"
}
```

Successful response:

```text
201 Created
```

---

## List Study Plans

```http
GET /api/study-plans?limit=50
```

Returns the authenticated student's saved study plans.

---

## Get Study Plan

```http
GET /api/study-plans/{study_plan_id}
```

The plan must belong to the authenticated student.

---

## Delete Study Plan

```http
DELETE /api/study-plans/{study_plan_id}
```

Successful response:

```text
204 No Content
```

---

## Create Manual Study Session

```http
POST /api/study-plans/{study_plan_id}/sessions
```

Representative request:

```json
{
  "subject_id": "subject-uuid",
  "title": "Review Chapter 4",
  "starts_at": "2026-08-12T18:00:00+08:00",
  "ends_at": "2026-08-12T19:00:00+08:00",
  "notes": "Focus on cell division"
}
```

Created sessions use:

```text
origin = manual
status = planned
```

---

## List Study Sessions

```http
GET /api/study-plans/{study_plan_id}/sessions?limit=200
```

Returns sessions belonging to one owned study plan.

---

## Delete Study Session

```http
DELETE /api/study-plans/{study_plan_id}/sessions/{study_session_id}
```

Successful response:

```text
204 No Content
```

---

# Study Plan Generation API

## Generate Study Plan

```http
POST /api/study-plan-generation
```

Representative request:

```json
{
  "title": "Generated Finals Plan",
  "starts_on": "2026-08-11",
  "ends_on": "2026-08-20",
  "tasks": [
    {
      "task_id": "task-uuid",
      "subject_id": "subject-uuid",
      "title": "Study for Biology exam",
      "deadline": "2026-08-20T18:00:00+08:00",
      "estimated_minutes": 180,
      "priority_weight": 5
    }
  ]
}
```

Successful response:

```text
201 Created
```

The response contains:

```text
plan
sessions
unscheduled_tasks
```

`unscheduled_tasks` contains work that could not fit into valid study availability before its deadline.

Scheduling preferences are loaded by the backend from authenticated student data.

---

## Regenerate Generated Study Plan

```http
POST /api/study-plan-generation/{study_plan_id}/regenerate
```

Representative request:

```json
{
  "tasks": [
    {
      "task_id": "task-uuid",
      "subject_id": "subject-uuid",
      "title": "Study for Biology exam",
      "deadline": "2026-08-20T18:00:00+08:00",
      "estimated_minutes": 180,
      "priority_weight": 5
    }
  ]
}
```

Successful response:

```text
200 OK
```

Regeneration:

- keeps the existing study-plan ID
- reloads current scheduling preferences
- uses the latest eligible Academic Tasks
- treats manual sessions as unavailable scheduling time
- prevents new generated sessions from being scheduled in the past
- replaces only generated sessions
- preserves manual sessions
- returns the refreshed plan, sessions, and unscheduled work

---

# Study Plan Error Contract

| HTTP | Error Code | Meaning |
|---:|---|---|
| `400` | `STUDY_PLAN_VALIDATION_FAILED` | Study-plan or scheduling operation is invalid |
| `404` | `STUDY_PLAN_NOT_FOUND` | Plan does not exist or is not owned by the authenticated student |
| `500` | `STUDY_PLAN_RESPONSE_FAILED` | Stored Study Plan data could not be converted into a valid response |
| `503` | `STUDY_PLAN_PERSISTENCE_FAILED` | Study Plan persistence is temporarily unavailable |

---

# Study Plan Security Contract

1. Bearer authentication determines the trusted student identity.
2. Requests cannot provide or override `user_id`.
3. Study plans and sessions are ownership scoped.
4. Subjects used by sessions must belong to the authenticated student.
5. Scheduling context is loaded by trusted backend services.
6. The browser cannot provide trusted timezone or availability context.
7. Manual sessions are preserved during regeneration.
8. Regeneration replaces only generated sessions.
9. Transactional generated-session replacement is restricted to trusted backend execution.
10. Public errors must not expose credentials, tokens, SQL details, or stack traces.

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
POST   /api/reviewers/{reviewer_id}/regenerate

POST   /api/academic-tasks
GET    /api/academic-tasks
GET    /api/academic-tasks/prioritized
GET    /api/academic-tasks/{task_id}
PATCH  /api/academic-tasks/{task_id}
PATCH  /api/academic-tasks/{task_id}/status
DELETE /api/academic-tasks/{task_id}
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