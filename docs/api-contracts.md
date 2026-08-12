<!-- File: /docs/api-contracts.md -->
<!-- Purpose: Documents implemented communication contracts between the frontend, FastAPI backend, worker, AI services, and Supabase. -->

**# API Contracts**

This document records the implemented application API and important database RPC contracts.

---

**# General API Information**

| Item | Value |
|---|---|
| Development backend | `http\://127.0.0.1:8000` |
| API prefix | `/api` |
| Format | JSON |
| Backend | FastAPI |
| Frontend | Next.js |

Protected student endpoints use:

```http
Authorization: Bearer <Supabase access token>
```

The backend validates the access token and derives the authenticated student ID.

Clients must not submit a trusted `user_id`.

---

**# Public Endpoint**

**## Health Check**

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

**# Internal File Processing Security**

Internal processing routes require:

```http
X-Processor-Key: <private configured value>
```

Environment variable:

```text
PROCESSOR_INTERNAL_KEY
```

The processor key must never be sent to browser code.

---

**# Validate Study File Source**

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

---

**# Process Study File**

```http
POST /api/internal/file-processing/{file_id}/process
```

Authentication:

```http
X-Processor-Key
```

The workflow performs:

1. Study-file validation
2. Private Storage download
3. Text extraction
4. Source-aware chunking
5. AI preparation
6. Embedding generation
7. Vector persistence
8. Extracted-content persistence
9. Final status update

---

**# Study Assistant RAG Endpoint**

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

The backend derives the trusted student identity from bearer authentication.

A first question may omit `conversation_id`.

A no-context result is a normal successful result.

---

**# Saved Conversation API**

Base path:

```text
/api/study-conversations
```

All routes require bearer authentication.

**## Create Conversation**

```http
POST /api/study-conversations
```

Successful status:

```text
201 Created
```

**## List Conversations**

```http
GET /api/study-conversations
```

Optional query:

```text
limit
```

Allowed range:

```text
1 to 50
```

**## Get Conversation**

```http
GET /api/study-conversations/{conversation_id}
```

Optional:

```text
message_limit
```

Allowed range:

```text
1 to 500
```

**## Rename Conversation**

```http
PATCH /api/study-conversations/{conversation_id}
```

**## Delete Conversation**

```http
DELETE /api/study-conversations/{conversation_id}
```

Successful status:

```text
204 No Content
```

The client must not parse JSON from the successful 204 response.

---

**# Important Database RPC Contracts**

**## File Processing**

```text
public.queue_study_file_processing(uuid)
public.claim_next_file_processing_job()
public.start_study_file_processing(uuid)
public.mark_study_file_indexing(uuid)
public.complete_study_file_processing(...)
public.fail_study_file_processing(...)
public.recover_stale_file_processing_jobs(integer, integer)
public.replace_study_file_ai_chunks(...)
```

**## Learning Profile**

```text
public.complete_learning_profile_onboarding()
public.replace_learning_output_confidences(...)
```

`replace_learning_output_confidences` persists the authenticated student's academic output-confidence values.

**## Flashcards**

```text
public.create_flashcard_deck_with_cards(...)
```

The trusted backend uses this RPC to atomically create the deck and ordered cards.

**## Quizzes**

```text
public.create_quiz_with_questions(...)
public.start_quiz_attempt(...)
public.submit_quiz_attempt_answer(...)
```

Quiz persistence and grading are trusted backend operations.

---

**# Reviewer API**

Reviewer endpoints require authenticated Supabase bearer authentication.

The backend derives the trusted student identity from the token.

Requests cannot provide or override a trusted `user_id`.

**## Generate Reviewer**

```http
POST /api/reviewers/generate
```

Supported scopes:

```text
file
subject
```

Supported lengths:

```text
short
medium
long
```

Reviewer generation uses processed owned study material.

It does not use similarity-based RAG retrieval.

**## List Reviewers**

```http
GET /api/reviewers
```

**## Get Reviewer**

```http
GET /api/reviewers/{reviewer_id}
```

**## Delete Reviewer**

```http
DELETE /api/reviewers/{reviewer_id}
```

Successful status:

```text
204 No Content
```

**## Regenerate Reviewer**

```http
POST /api/reviewers/{reviewer_id}/regenerate
```

Regeneration is owner-scoped and reuses the reviewer's saved scope.

**## Reviewer Security**

1. Bearer authentication determines the trusted student.
2. Requests cannot choose `user_id`.
3. Source loading is ownership scoped.
4. File-scope source material must be ready.
5. Browser clients cannot directly insert trusted reviewer records.
6. Public errors must not expose secrets, provider traces, or database details.

---

**# Flashcard API**

Flashcard endpoints require authenticated Supabase bearer authentication.

Requests cannot provide or override a trusted `user_id`.

**## Generate Flashcards**

```http
POST /api/flashcards/generate
```

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

Representative file-scope request:

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
- The file must belong to the authenticated student.
- The file must belong to the selected subject.
- The file must be `ready`.

For subject scope:

- `subject_id` is required.
- `study_file_id` must be `null` or omitted.
- Generation uses owned ready study files in the subject.

Large-material generation uses deterministic ordered source batches and final synthesis.

**## List Flashcard Decks**

```http
GET /api/flashcards
```

Optional query:

```text
subject_id
```

**## Get Flashcard Deck**

```http
GET /api/flashcards/{deck_id}
```

**## Delete Flashcard Deck**

```http
DELETE /api/flashcards/{deck_id}
```

Successful status:

```text
204 No Content
```

Deleting the deck cascades to its child Flashcards.

**## Flashcard Security**

---

**## Record Flashcard Review**

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

**# Flashcard API Errors**

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

**# Flashcard Security Contract**

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

**# Quiz API**

Quiz endpoints require authenticated Supabase bearer authentication.

Requests cannot provide or override a trusted `user_id`.

**## Generate Quiz**

```http
POST /api/quizzes/generate
```

Representative request:

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

Normal Quiz responses exclude:

```text
correct_answer
accepted_answers
explanation
```

**## List Saved Quizzes**

```http
GET /api/quizzes
```

**## Get Saved Quiz**

```http
GET /api/quizzes/{quiz_id}
```

**## Delete Saved Quiz**

```http
DELETE /api/quizzes/{quiz_id}
```

Successful status:

```text
204 No Content
```

---

**# Quiz Attempt API**

**## Start Attempt**

```http
POST /api/quizzes/{quiz_id}/attempts
```

Successful status:

```text
201 Created
```

**## List Attempts**

```http
GET /api/quizzes/{quiz_id}/attempts
```

**## Get Attempt**

```http
GET /api/quiz-attempts/{attempt_id}
```

**## Submit Answer**

```http
POST /api/quiz-attempts/{attempt_id}/questions/{position}/answer
```

Representative request:

```json
{
  "answer": "Nucleus"
}
```

The backend atomically:

1. validates the expected question position;
2. grades the answer;
3. persists the submitted answer;
4. updates the score;
5. advances or completes the attempt.

**## Get Final Result**

```http
GET /api/quiz-attempts/{attempt_id}/result
```

Result is available only for completed owned attempts.

Topic classification:

```text
Strong: accuracy >= 70%
Weak:   accuracy < 70%
```

**## Review Completed Attempt**

```http
GET /api/quiz-attempts/{attempt_id}/review
```

Review is only available after the owned attempt has completed.

**## Quiz Security**

1. Bearer authentication determines trusted student identity.
2. Requests cannot choose `user_id`.
3. Source loading is ownership scoped.
4. Normal Quiz responses exclude private answer keys.
5. Answer-key reads use trusted backend operations.
6. Answer submission validates the expected position atomically.
7. Full review requires a completed owned attempt.
8. Public errors must not expose secrets or backend internals.

---

**# Academic Tasks API**

Base path:

```text
/api/academic-tasks
```

All Academic Task routes require:

```http
Authorization: Bearer <Supabase access token>
```

The backend derives the trusted student identity from the validated bearer token.

Clients cannot submit a trusted `user_id`.

Supported difficulty:

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

---

**## Create Academic Task**

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

Status defaults to:

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

**## List Academic Tasks**

```http
GET /api/academic-tasks
```

Optional query:

| Parameter | Type | Default | Rules |
|---|---|---:|---|
| `limit` | integer | 100 | 1–100 |

Only tasks owned by the authenticated student are returned.

---

**## List Prioritized Academic Tasks**

```http
GET /api/academic-tasks/prioritized
```

Optional query:

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

Authoritative ordering:

```text
1. total_score descending
2. deadline ascending
3. created_at ascending
4. task ID
```

The browser does not calculate or override the priority score.

---

**## Get Academic Task**

```http
GET /api/academic-tasks/{task_id}
```

Returns one Academic Task owned by the authenticated student.

Missing and unowned tasks receive safe not-found behavior.

---

**## Update Academic Task**

```http
PATCH /api/academic-tasks/{task_id}
```

Editable fields:

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

Task status is changed through the dedicated status endpoint.

---

**## Change Academic Task Status**

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

Completed and cancelled tasks receive:

```text
total priority = 0
```

---

**## Delete Academic Task**

```http
DELETE /api/academic-tasks/{task_id}
```

Successful status:

```text
204 No Content
```

The client must not parse JSON from the successful 204 response.

---

**# Academic Task Priority Contract**

The deterministic backend priority engine uses:

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

The browser cannot provide a trusted calculated priority.

Previous performance currently uses a neutral fallback until a production performance source is connected.

---

**# Academic Task Error Contract**

Controlled Academic Task errors include:

| HTTP | Error Code | Meaning |
|---:|---|---|
| `400` | `ACADEMIC_TASK_VALIDATION_FAILED` | Academic Task request is invalid |
| `404` | `ACADEMIC_TASK_NOT_FOUND` | Task does not exist or is not owned by the student |
| `500` | `ACADEMIC_TASK_RESPONSE_FAILED` | Stored Academic Task data could not be processed |
| `500` | `ACADEMIC_TASK_FAILED` | Unexpected Academic Task operation failure |
| `503` | `ACADEMIC_TASK_PERSISTENCE_FAILED` | Academic Task storage is temporarily unavailable |

Authentication failures use the existing protected-API authentication behavior.

---

**# Academic Task Security Contract**

1. Bearer authentication determines trusted student identity.
2. Requests cannot choose or override `user_id`.
3. Academic Tasks are owner-scoped.
4. Selected subjects must belong to the authenticated student.
5. Database RLS protects direct student access.
6. Priority context is loaded by trusted backend services.
7. The browser cannot submit trusted priority scores.
8. The browser cannot submit trusted study availability or output-confidence context for priority calculation.
9. Priority calculation does not call Gemini.
10. Public errors must not expose secrets, tokens, SQL details, or stack traces.

---

**# HTTP Security Rules**

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
- Private Quiz answer keys before permitted feedback/review
- Trusted Academic Task priority context

---
**# Study Plan API**

All Study Plan endpoints require authenticated bearer access.

The authenticated student identity is derived from the bearer token and cannot be supplied through request bodies.

**## Create Manual Study Plan**

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

**## List Study Plans**

```http
GET /api/study-plans?limit=50
```

Returns the authenticated student's saved study plans.

---

**## Get Study Plan**

```http
GET /api/study-plans/{study_plan_id}
```

The plan must belong to the authenticated student.

---

**## Delete Study Plan**

```http
DELETE /api/study-plans/{study_plan_id}
```

Successful response:

```text
204 No Content
```

---

**## Create Manual Study Session**

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

**## List Study Sessions**

```http
GET /api/study-plans/{study_plan_id}/sessions?limit=200
```

Returns sessions belonging to one owned study plan.

---

**## Delete Study Session**

```http
DELETE /api/study-plans/{study_plan_id}/sessions/{study_session_id}
```

Successful response:

```text
204 No Content
```

---

**# Study Plan Generation API**

**## Generate Study Plan**

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

**## Regenerate Generated Study Plan**

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

**# Study Plan Error Contract**

| HTTP | Error Code | Meaning |
|---:|---|---|
| `400` | `STUDY_PLAN_VALIDATION_FAILED` | Study-plan or scheduling operation is invalid |
| `404` | `STUDY_PLAN_NOT_FOUND` | Plan does not exist or is not owned by the authenticated student |
| `500` | `STUDY_PLAN_RESPONSE_FAILED` | Stored Study Plan data could not be converted into a valid response |
| `503` | `STUDY_PLAN_PERSISTENCE_FAILED` | Study Plan persistence is temporarily unavailable |

---

**# Study Plan Security Contract**

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

**# Analytics API**

Analytics endpoints require authenticated Supabase bearer authentication.

The backend derives the trusted student UUID from the validated bearer token.

Analytics requests cannot provide or override `user_id`.

**## Get Analytics Overview**

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

**## Analytics Errors**

| HTTP | Meaning |
|---|---|
| `401` | Authentication is missing, invalid, or expired |
| `422` | Reporting period is unsupported |
| `503` | Canonical Analytics data is temporarily unavailable |

**## Analytics Security Contract**

1. Bearer authentication determines the trusted student identity.
2. Analytics requests cannot choose `user_id`.
3. Subject and study-material queries are owner-scoped.
4. Quiz attempts are filtered to the authenticated student.
5. Topic evidence is read only for the selected owned completed attempts.
6. Flashcard review evidence is filtered to the authenticated student.
7. Analytics does not expose Quiz answer keys.
8. Controlled failures do not expose database credentials, backend secrets, or provider traces.

The Flashcard review persistence migration is applied to the shared remote database. Linked migration history was re-inspected after the C/D synchronization merge, and a subsequent linked dry run confirmed that the remote database is up to date.

---

**# OpenAPI Verification**

Start FastAPI and open:

```text
http\://127.0.0.1:8000/docs
```

Important implemented routes include:

```text
GET    /api/health

POST   /api/internal/file-processing/{file_id}/validate-source
POST   /api/internal/file-processing/{file_id}/process

POST   /api/rag/answer

POST   /api/study-conversations
GET    /api/study-conversations
GET    /api/study-conversations/{conversation_id}
PATCH  /api/study-conversations/{conversation_id}
DELETE /api/study-conversations/{conversation_id}

POST   /api/reviewers/generate
GET    /api/reviewers
GET    /api/reviewers/{reviewer_id}
DELETE /api/reviewers/{reviewer_id}
POST   /api/reviewers/{reviewer_id}/regenerate

POST   /api/flashcards/generate
GET    /api/flashcards
GET    /api/flashcards/{deck_id}
POST   /api/flashcards/{deck_id}/reviews
DELETE /api/flashcards/{deck_id}

GET    /api/analytics/overview

POST   /api/quizzes/generate
GET    /api/quizzes
GET    /api/quizzes/{quiz_id}
DELETE /api/quizzes/{quiz_id}
GET    /api/quizzes/{quiz_id}/attempts
POST   /api/quizzes/{quiz_id}/attempts
GET    /api/quiz-attempts/{attempt_id}
POST   /api/quiz-attempts/{attempt_id}/questions/{position}/answer
GET    /api/quiz-attempts/{attempt_id}/result
GET    /api/quiz-attempts/{attempt_id}/review

POST   /api/academic-tasks
GET    /api/academic-tasks
GET    /api/academic-tasks/prioritized
GET    /api/academic-tasks/{task_id}
PATCH  /api/academic-tasks/{task_id}
PATCH  /api/academic-tasks/{task_id}/status
DELETE /api/academic-tasks/{task_id}
```

---

**# API Change Rules**

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