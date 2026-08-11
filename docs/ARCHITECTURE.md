<!-- File: /docs/ARCHITECTURE.md -->
<!-- Purpose: Documents the implemented and planned architecture of the STS Capstone STUDY AI project. -->

# STS Capstone — STUDY AI Architecture

This document describes the current architecture of STUDY AI.

The system currently includes:

- Next.js frontend
- Mantine UI
- Supabase Authentication
- Hosted Supabase PostgreSQL
- Private Supabase Storage
- Student learning-profile onboarding
- Academic output-confidence onboarding
- Subject management
- Study-material uploads
- Automatic file processing
- Document text extraction
- AI-oriented chunking
- Gemini embeddings
- Supabase pgvector storage
- Semantic retrieval
- Grounded RAG answering
- Protected FastAPI RAG API
- Student-facing Study Assistant
- Saved Study Assistant conversations
- Bounded conversation memory
- Deterministic conversation summaries
- Reviewer generation from a subject or study file
- Structured reviewer content with topics, key points, and definitions
- Reviewer source tracking
- Saved reviewer persistence
- Protected FastAPI reviewer API
- Saved reviewer management and regeneration
- Large-material multi-pass reviewer generation
- Deterministic reviewer source batching
- Partial-reviewer synthesis into one final structured reviewer
- Flashcard generation from one ready study file or a whole subject
- Structured question-and-answer Flashcard generation
- Complete Flashcard source tracking
- Saved Flashcard deck persistence
- Individual ordered Flashcard persistence
- Atomic Flashcard deck-and-card creation
- Protected FastAPI Flashcard API
- Saved Flashcard listing, retrieval, and deletion
- Deterministic large-material Flashcard source batching
- Multi-pass Flashcard candidate generation and final synthesis
- Protected student-facing Flashcard workspace
- Interactive question-and-answer Flashcard study viewer
- Saved Flashcard reopening and deletion UI
- AI Quiz generation from a subject or ready study file
- Multiple-choice, true/false, identification, and mixed Quiz modes
- Easy, medium, and hard Quiz difficulty
- Atomic Quiz and private answer-key persistence
- One-question-at-a-time Quiz attempts with immediate grading feedback
- Final Quiz scoring with strong/weak topic analysis
- Saved Quiz history, completed-attempt review, retaking, and deletion
- Student-owned Academic Task CRUD
- Academic output confidence by skill type
- Deterministic Academic Task priority scoring
- Explainable seven-factor priority breakdowns
- Protected Academic Tasks frontend
- Live priority recalculation after task changes

The application now includes protected Reviewer, Flashcard, Quiz, Academic Tasks, and Study Plan frontends.

Future phases may add analytics, deployment, and monitoring improvements.

---

# Phase Status

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | Project foundation, frontend, backend, Supabase, authentication | Implemented |
| Phase 2 | Learning-profile onboarding and profile data | Implemented |
| Phase 3 | Subjects, uploads, extraction, processing worker | Implemented |
| Phase 4 | AI provider, chunking, embeddings, vector persistence, retrieval | Implemented |
| Phase 5A–5F | Retrieval orchestration, grounded RAG API, Study Assistant | Implemented |
| Phase 5G | Saved conversations, memory, summaries, conversation history UI | Implemented |
| Phase 6A | Reviewer backend foundation, persistence, generation, sources, protected API | Implemented |
| Phase 6B | Reviewer frontend, authenticated generation UI, structured result display | Implemented |
| Phase 6C | Saved reviewer management and regeneration | Implemented |
| Phase 6D | Large-material multi-pass reviewer generation | Implemented |
| Track A | Flashcard backend, large-material generation, protected frontend, saved-deck access, and interactive study UI | Implemented |
| Track B | Quiz generation, attempts, scoring, history, review, retake, deletion | Implemented |
| Phase 7A–7E | Academic Task persistence, output confidence, CRUD, deterministic priority, frontend, and live integration | Implemented |
| Track D | Study-plan persistence, deterministic scheduling, Academic Task integration, calendar workspace, manual sessions, and regeneration | Implemented |
| Later phases | Analytics, deployment, and monitoring | Planned |

---

# High-Level Architecture

```mermaid
flowchart LR
    STUDENT["Student"]

    subgraph FRONTEND["Next.js Frontend"]
        AUTH_UI["Authentication"]
        ONBOARDING["Learning Profile"]
        SUBJECT_UI["Subjects"]
        FILE_UI["Study Materials"]
        ASSISTANT["Study Assistant"]
        HISTORY["Saved Conversations"]
        REVIEWERS_UI["Reviewer Workspace"]
        FLASHCARDS_UI["Flashcard Workspace"]
        QUIZZES_UI["Quiz Workspace"]
        TASKS_UI["Academic Tasks Workspace"]

        SUPABASE_CLIENT["Supabase Clients"]
        API_CLIENT["FastAPI Clients"]
    end

    subgraph BACKEND["FastAPI Backend"]
        API["FastAPI Routes"]
        AUTH_DEP["Authenticated User Dependency"]

        PROCESSOR["File Processor"]
        WORKER["Processing Worker"]
        EXTRACTION["Document Extraction"]

        PREPARATION["AI Preparation"]
        VECTOR_INDEXER["Vector Indexer"]

        RETRIEVAL["Retrieval Service"]
        RAG["RAG Orchestration"]

        CONVERSATION["Conversation Service"]
        MEMORY["Bounded Memory"]
        SUMMARY["Deterministic Summary"]

        REVIEWER_API["Reviewer API"]
        REVIEWER_ORCHESTRATION["Reviewer Orchestration"]
        REVIEWER_SOURCE["Reviewer Source Loader"]
        REVIEWER_GENERATION["Reviewer Generation"]
        REVIEWER_BATCHER["Reviewer Source Batcher"]
        REVIEWER_SERVICE["Reviewer Persistence Service"]

        FLASHCARD_API["Flashcard API"]
        FLASHCARD_ORCHESTRATION["Flashcard Orchestration"]
        FLASHCARD_SOURCE["Flashcard Source Loader"]
        FLASHCARD_GENERATION["Flashcard Generation"]
        FLASHCARD_SERVICE["Flashcard Persistence Service"]

        QUIZ_API["Quiz API"]
        QUIZ_ORCHESTRATION["Quiz Orchestration"]
        QUIZ_SOURCE["Quiz Source Loader"]
        QUIZ_GENERATION["Quiz Generation"]
        QUIZ_SERVICE["Quiz Persistence Service"]
        QUIZ_ATTEMPTS["Quiz Attempt Service"]

        TASK_API["Academic Task API"]
        TASK_SERVICE["Academic Task Service"]
        TASK_PRIORITY["Academic Task Priority Service"]
        TASK_CONTEXT["Priority Context Resolver"]
        TASK_ENGINE["Deterministic Priority Engine"]
    end

    subgraph SUPABASE["Supabase"]
        AUTH["Authentication"]
        DATABASE[("PostgreSQL")]
        STORAGE[("Private Storage")]
        VECTOR[("pgvector")]
        RPC["Trusted RPC Functions"]
    end

    GEMINI["Gemini API"]

    STUDENT --> AUTH_UI
    STUDENT --> ONBOARDING
    STUDENT --> SUBJECT_UI
    STUDENT --> FILE_UI
    STUDENT --> ASSISTANT
    STUDENT --> REVIEWERS_UI
    STUDENT --> FLASHCARDS_UI
    STUDENT --> QUIZZES_UI
    STUDENT --> TASKS_UI

    AUTH_UI --> SUPABASE_CLIENT
    ONBOARDING --> SUPABASE_CLIENT
    SUBJECT_UI --> SUPABASE_CLIENT
    FILE_UI --> SUPABASE_CLIENT

    SUPABASE_CLIENT --> AUTH
    SUPABASE_CLIENT --> DATABASE
    SUPABASE_CLIENT --> STORAGE

    ASSISTANT --> HISTORY
    ASSISTANT --> API_CLIENT
    REVIEWERS_UI --> API_CLIENT
    FLASHCARDS_UI --> API_CLIENT
    QUIZZES_UI --> API_CLIENT
    TASKS_UI --> API_CLIENT

    API_CLIENT --> API
    API --> AUTH_DEP
    AUTH_DEP --> AUTH

    WORKER --> PROCESSOR
    PROCESSOR --> STORAGE
    PROCESSOR --> EXTRACTION
    EXTRACTION --> PREPARATION
    PREPARATION --> VECTOR_INDEXER

    VECTOR_INDEXER --> GEMINI
    VECTOR_INDEXER --> VECTOR

    API --> CONVERSATION
    CONVERSATION --> MEMORY
    CONVERSATION --> SUMMARY
    CONVERSATION --> RAG

    RAG --> RETRIEVAL
    RETRIEVAL --> VECTOR
    RAG --> GEMINI
    CONVERSATION --> DATABASE

    API --> REVIEWER_API
    REVIEWER_API --> REVIEWER_ORCHESTRATION
    REVIEWER_ORCHESTRATION --> REVIEWER_SOURCE
    REVIEWER_ORCHESTRATION --> REVIEWER_GENERATION
    REVIEWER_ORCHESTRATION --> REVIEWER_SERVICE
    REVIEWER_SOURCE --> DATABASE
    REVIEWER_GENERATION --> REVIEWER_BATCHER
    REVIEWER_GENERATION --> GEMINI
    REVIEWER_SERVICE --> DATABASE

    API --> FLASHCARD_API
    FLASHCARD_API --> FLASHCARD_ORCHESTRATION
    FLASHCARD_ORCHESTRATION --> FLASHCARD_SOURCE
    FLASHCARD_ORCHESTRATION --> FLASHCARD_GENERATION
    FLASHCARD_ORCHESTRATION --> FLASHCARD_SERVICE
    FLASHCARD_SOURCE --> DATABASE
    FLASHCARD_GENERATION --> GEMINI
    FLASHCARD_SERVICE --> RPC
    FLASHCARD_SERVICE --> DATABASE

    API --> QUIZ_API
    QUIZ_API --> QUIZ_ORCHESTRATION
    QUIZ_ORCHESTRATION --> QUIZ_SOURCE
    QUIZ_ORCHESTRATION --> QUIZ_GENERATION
    QUIZ_ORCHESTRATION --> QUIZ_SERVICE
    QUIZ_API --> QUIZ_ATTEMPTS
    QUIZ_SOURCE --> DATABASE
    QUIZ_GENERATION --> GEMINI
    QUIZ_SERVICE --> RPC
    QUIZ_SERVICE --> DATABASE
    QUIZ_ATTEMPTS --> RPC
    QUIZ_ATTEMPTS --> DATABASE

    API --> TASK_API
    TASK_API --> TASK_SERVICE
    TASK_API --> TASK_PRIORITY
    TASK_SERVICE --> DATABASE
    TASK_PRIORITY --> TASK_CONTEXT
    TASK_CONTEXT --> DATABASE
    TASK_PRIORITY --> TASK_ENGINE
```

---

# Frontend Architecture

The frontend uses:

- Next.js
- TypeScript
- Mantine UI
- CSS Modules
- Tabler Icons
- Supabase browser/server clients
- Typed FastAPI clients
- Vitest
- React Testing Library

The frontend does not contain backend secrets.

---

# Authentication Flow

Supabase Authentication is the identity provider.

```mermaid
sequenceDiagram
    actor Student
    participant Frontend as Next.js
    participant Supabase as Supabase Auth
    participant Proxy as Session Proxy
    participant Protected as Protected Route

    Student->>Frontend: Register or sign in
    Frontend->>Supabase: Authenticate
    Supabase-->>Frontend: Session

    Frontend->>Proxy: Request protected page
    Proxy->>Supabase: Validate or refresh session
    Supabase-->>Proxy: Authenticated state

    alt Authenticated
        Proxy-->>Protected: Allow
    else Unauthenticated
        Proxy-->>Student: Redirect to login
    end
```

Student identity used by protected FastAPI requests comes from the validated Supabase bearer access token.

The browser must not provide a trusted `user_id`.

---

# Learning Profile Architecture

```mermaid
flowchart TD
    STUDENT["Student"]
    ONBOARDING["Onboarding"]

    PROFILE["Profile"]
    LEARNING["Learning Preferences"]
    STRENGTHS["Subject Strengths"]
    CONFIDENCE["Academic Output Confidence"]
    AVAILABILITY["Study Availability"]

    PROFILES[("profiles")]
    LEARNING_TABLE[("learning_profiles")]
    SUBJECT_TABLE[("learning_profile_subjects")]
    CONFIDENCE_TABLE[("learning_output_confidences")]
    AVAILABILITY_TABLE[("study_availability")]

    STUDENT --> ONBOARDING

    ONBOARDING --> PROFILE
    ONBOARDING --> LEARNING
    ONBOARDING --> STRENGTHS
    ONBOARDING --> CONFIDENCE
    ONBOARDING --> AVAILABILITY

    PROFILE --> PROFILES
    LEARNING --> LEARNING_TABLE
    STRENGTHS --> SUBJECT_TABLE
    CONFIDENCE --> CONFIDENCE_TABLE
    AVAILABILITY --> AVAILABILITY_TABLE
```

Academic output confidence is stored separately from subject strength.

Implemented output-confidence categories:

```text
writing
computation
research
presentation
creative
reading_analysis
memorization
```

Academic Task priority uses output confidence according to the task's `output_type`.

The legacy subject-level confidence value is not used by the Academic Task priority engine.

---

# Subject and Study-Material Architecture

```mermaid
flowchart LR
    STUDENT["Student"]

    SUBJECTS["Subject Workspace"]
    FILE_MANAGER["FileUploadManager"]

    SUBJECT_TABLE[("subjects")]
    FILE_TABLE[("study_files")]
    STORAGE[("Private study-materials Bucket")]
    JOBS[("file_processing_jobs")]

    STUDENT --> SUBJECTS
    SUBJECTS --> SUBJECT_TABLE

    SUBJECTS --> FILE_MANAGER
    FILE_MANAGER --> FILE_TABLE
    FILE_MANAGER --> STORAGE
    FILE_MANAGER --> JOBS
```

Uploaded study files belong to an authenticated student and subject.

---

# File Processing Lifecycle

```mermaid
stateDiagram-v2
    [*] --> uploading

    uploading --> queued: upload complete
    uploading --> failed: upload failure

    queued --> reading: worker claims
    reading --> indexing: extraction complete
    indexing --> ready: persistence complete

    reading --> failed
    indexing --> failed

    reading --> queued: stale recovery
    indexing --> queued: stale recovery

    failed --> uploading: retry

    ready --> [*]
```

Study-file statuses:

```text
uploading
queued
reading
indexing
ready
failed
```

---

# File Processing Worker

```mermaid
flowchart TD
    START["Worker"]
    RECOVER["Recover Stale Jobs"]
    CLAIM["Claim Next Job"]
    FOUND{"Job?"}

    DOWNLOAD["Download Private File"]
    EXTRACT["Extract Text"]
    PREPARE["Prepare AI Chunks"]
    INDEX["Generate and Persist Embeddings"]
    COMPLETE["Persist Extracted Content"]
    READY["Mark Ready"]
    FAIL["Record Failure"]
    WAIT["Wait"]

    START --> RECOVER
    RECOVER --> CLAIM
    CLAIM --> FOUND

    FOUND -->|No| WAIT
    WAIT --> RECOVER

    FOUND -->|Yes| DOWNLOAD
    DOWNLOAD --> EXTRACT
    EXTRACT --> PREPARE
    PREPARE --> INDEX
    INDEX --> COMPLETE
    COMPLETE --> READY

    DOWNLOAD -->|Error| FAIL
    EXTRACT -->|Error| FAIL
    PREPARE -->|Error| FAIL
    INDEX -->|Error| FAIL
    COMPLETE -->|Error| FAIL
```

Atomic job claiming uses database locking and `SKIP LOCKED`.

---

# Document Extraction

Implemented extraction:

| Format | Implementation |
|---|---|
| PDF | `pypdf` |
| TXT | UTF-8 decoding |
| PPTX | `python-pptx` |
| XLSX | `openpyxl` |
| XLS | `xlrd` |

Source-aware locators include:

- Page
- Slide
- Worksheet
- Document

JPEG, PNG, and WebP may be stored, but OCR is not currently part of the implemented extraction pipeline.

---

# AI Provider Architecture

Backend AI services depend on provider-independent contracts.

```mermaid
flowchart TD
    SERVICES["Backend AI Services"]
    CONTRACTS["AI Contracts"]
    GENERATION["GenerationProvider"]
    EMBEDDING["EmbeddingProvider"]

    GEMINI_PROVIDER["GeminiProvider"]
    GEMINI["Gemini API"]

    SERVICES --> CONTRACTS
    CONTRACTS --> GENERATION
    CONTRACTS --> EMBEDDING

    GENERATION --> GEMINI_PROVIDER
    EMBEDDING --> GEMINI_PROVIDER

    GEMINI_PROVIDER --> GEMINI
```

Gemini credentials remain backend-only.

Normal automated tests use fake providers and do not call live Gemini services.

---

# Retrieval Architecture

```mermaid
flowchart LR
    QUESTION["Student Question"]
    QUERY["Query Embedding"]
    GEMINI["Gemini Embedding API"]

    RETRIEVER["Retrieval Orchestration"]
    SEARCH["Vector Search RPC"]
    VECTORS[("study_file_ai_chunks")]

    RESULTS["Ranked Study Chunks"]

    QUESTION --> QUERY
    QUERY --> GEMINI
    GEMINI --> RETRIEVER

    RETRIEVER --> SEARCH
    SEARCH --> VECTORS
    VECTORS --> RESULTS
```

Retrieval supports:

- Student-owned materials only
- Optional subject filtering
- Optional study-file filtering
- Similarity threshold
- Maximum match count
- Safe source metadata

---

# Grounded RAG Architecture

```mermaid
flowchart TD
    QUESTION["Question"]
    RETRIEVAL["Owned Retrieval"]
    CONTEXT{"Relevant Context?"}
    NO_CONTEXT["No-Context Result"]
    PROMPT["Grounded Prompt"]
    GEMINI["Gemini Generation"]
    ANSWER["Answer + Sources"]

    QUESTION --> RETRIEVAL
    RETRIEVAL --> CONTEXT
    CONTEXT -->|No| NO_CONTEXT
    CONTEXT -->|Yes| PROMPT
    PROMPT --> GEMINI
    GEMINI --> ANSWER
```

Factual claims must be supported by retrieved study-material content.

Conversation history is context only and does not become factual evidence.

---

# Study Assistant

The protected Study Assistant route is:

```text
/study-assistant
```

The Study Assistant supports:

- Subject filtering
- Study-file filtering
- Grounded answers
- Source cards
- No-context responses
- Saved conversation history
- Conversation switching
- New conversations
- Follow-up questions

Implemented persistence:

```text
study_conversations
study_messages
```

Conversation memory is bounded.

Older messages may be compressed into a deterministic backend summary without calling Gemini.

---

# Reviewer Architecture

A reviewer can be generated from:

- One ready study file
- All ready study files within one subject

Reviewer generation loads processed source-aware chunks in deterministic file and chunk order rather than similarity-based RAG retrieval.

Generated reviewer content is structured as:

```text
overview
topics
  title
  summary
  key_points
  definitions
```

Reviewer sources preserve the originating study file, chunk index, and available locator metadata.

Protected endpoints include:

```text
POST   /api/reviewers/generate
GET    /api/reviewers
GET    /api/reviewers/{reviewer_id}
DELETE /api/reviewers/{reviewer_id}
POST   /api/reviewers/{reviewer_id}/regenerate
```

Large-material generation uses deterministic source batching and final synthesis.

---

# Track A — Flashcards

Track A implements the complete Flashcard workflow from authenticated study-material selection through AI generation, persistence, interactive studying, and saved-deck management.

Supported generation scopes:

```text
file
subject
```

Supported deck sizes:

```text
Minimum cards: 5
Default cards: 20
Maximum cards: 50
```

Flashcard generation uses complete processed source-aware chunks rather than similarity-based RAG retrieval.

For source material within the single-pass limit:

```text
Complete source bundle
→ Flashcard prompt
→ Gemini
→ Validated Flashcards
→ Persistence
```

For oversized material:

```text
Complete source bundle
→ Deterministic source batches
→ Candidate Flashcard generation
→ Final synthesis
→ Validated final deck
→ Persistence
```

Flashcards use:

```text
flashcard_decks
flashcards
```

Trusted persistence uses:

```text
create_flashcard_deck_with_cards(...)
```

Protected endpoints:

```text
POST   /api/flashcards/generate
GET    /api/flashcards
GET    /api/flashcards/{deck_id}
DELETE /api/flashcards/{deck_id}
```

The protected Flashcard workspace is:

```text
/flashcards
```

The frontend supports:

- Whole-subject generation
- Single-ready-study-material generation
- Configurable card count
- Question-first presentation
- Question/answer flipping
- Previous/next navigation
- Saved deck reopening
- Saved deck deletion

---

# Track B — Quiz Generation and Attempts

Track B implements end-to-end Quiz generation and Quiz-taking from processed study material.

Supported scopes:

```text
file
subject
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

Private answer-key fields:

```text
correct_answer
accepted_answers
explanation
```

are not returned through normal Quiz reads.

Quiz resources:

```text
quizzes
quiz_questions
quiz_attempts
quiz_attempt_answers
```

Trusted RPCs:

```text
create_quiz_with_questions
start_quiz_attempt
submit_quiz_attempt_answer
```

Strong topics use:

```text
accuracy >= 70%
```

Weak topics use:

```text
accuracy < 70%
```

The protected Quiz workspace is:

```text
/quizzes
```

The frontend supports:

- Quiz generation
- One-question-at-a-time attempts
- Immediate grading feedback
- Final score
- Strong/weak topic analysis
- Saved Quiz history
- Completed-attempt review
- Retakes
- Deletion

---

# Phase 7 — Academic Tasks and Deterministic Priority

Phase 7 implements student-owned Academic Task management and deterministic priority scoring.

The protected Academic Tasks workspace is:

```text
/academic-tasks
```

Academic Tasks contain:

```text
subject
title
description
deadline
estimated duration
difficulty
task type
academic output type
workflow status
```

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

## Academic Task Priority Architecture

```mermaid
flowchart LR
    STUDENT["Authenticated Student"]
    WORKSPACE["Academic Tasks Workspace"]
    API["Academic Task FastAPI Routes"]

    CRUD["Academic Task Service"]
    REPOSITORY["Academic Task Repository"]

    PRIORITY["Academic Task Priority Service"]
    CONTEXT_REPO["Priority Context Repository"]
    CONTEXT["Priority Context Resolver"]
    ENGINE["Deterministic Priority Engine"]

    TASKS[("academic_tasks")]
    PROFILE[("profiles")]
    CONFIDENCE[("learning_output_confidences")]
    AVAILABILITY[("study_availability")]

    STUDENT --> WORKSPACE
    WORKSPACE --> API

    API --> CRUD
    CRUD --> REPOSITORY
    REPOSITORY --> TASKS

    API --> PRIORITY
    PRIORITY --> CONTEXT_REPO

    CONTEXT_REPO --> PROFILE
    CONTEXT_REPO --> CONFIDENCE
    CONTEXT_REPO --> AVAILABILITY

    PRIORITY --> CONTEXT
    CONTEXT --> PRIORITY
    PRIORITY --> ENGINE
```

Priority calculation is deterministic backend logic.

It does not use Gemini or another generative AI provider.

## Priority Factors

| Factor | Weight |
|---|---:|
| Deadline proximity | 30% |
| Difficulty | 20% |
| Estimated completion time | 15% |
| Academic output confidence | 15% |
| Previous performance | 10% |
| Available study time | 5% |
| Task status | 5% |

Total configured weight:

```text
100%
```

Higher factor scores increase task urgency.

Completed and cancelled tasks receive:

```text
total priority = 0
```

Previous performance currently uses a neutral fallback until a production performance source is connected to the priority engine.

Missing confidence or unavailable context uses deterministic fallback behavior rather than invented student data.

## Priority API and Ordering

The authoritative prioritized endpoint is:

```text
GET /api/academic-tasks/prioritized
```

The backend sorts by:

```text
1. total priority score descending
2. deadline ascending
3. creation time ascending
4. task ID
```

The frontend does not duplicate the priority formula.

After successful:

```text
create
edit
status change
delete
```

the frontend reloads the prioritized endpoint so ordering and scores remain backend-controlled.

The frontend provides:

```text
Why this priority?
```

which displays the seven factor scores.

## Academic Output Confidence

Academic output confidence is stored in:

```text
public.learning_output_confidences
```

Implemented skill categories:

```text
writing
computation
research
presentation
creative
reading_analysis
memorization
```

For a direct output type, the corresponding confidence value is used.

For `mixed`, the backend may use an aggregate when complete output-confidence data exists.

For unavailable confidence data, deterministic neutral fallback behavior is used.

## Phase 7 Live Integration

Live validation covered:

```text
create task
load task
edit task
change status
priority calculation
priority explanation
priority recalculation
completed-task zero priority
delete task
page refresh persistence
```

See:

```text
docs/ACADEMIC_TASK_PRIORITY.md
```

---

# Study Plans and Scheduling

Track D implements persistent study plans, study sessions, deterministic scheduling, Academic Task integration, manual scheduling, and generated-plan regeneration.

The protected frontend route is:

```text
/study-plan
```

The feature supports two plan modes:

```text
manual
generated
```

Manual plans allow students to create their own plans and sessions.

Generated plans use prioritized Academic Tasks together with the authenticated student's scheduling preferences.

## Scheduling Context

The backend loads trusted scheduling context from existing onboarding data:

```text
profiles.timezone
learning_profiles.preferred_study_duration_minutes
study_availability
```

The browser does not provide trusted availability or timezone values.

Academic Tasks are converted into scheduler inputs containing:

```text
task_id
subject_id
title
deadline
estimated_minutes
priority_weight
```

The Academic Task deterministic priority score is converted into a bounded scheduler priority weight from `1` to `5`.

Completed and cancelled Academic Tasks are excluded from scheduling.

## Generation Flow

```mermaid
flowchart LR
    TASKS["Prioritized Academic Tasks"]
    ADAPTER["Academic Task Adapter"]
    CONTEXT["Scheduling Context"]
    SCHEDULER["Deterministic Study Scheduler"]
    PERSIST["Study Plan Persistence"]
    CALENDAR["Study Plan Calendar"]

    TASKS --> ADAPTER
    ADAPTER --> SCHEDULER
    CONTEXT --> SCHEDULER
    SCHEDULER --> PERSIST
    PERSIST --> CALENDAR
```

Generated schedules:

- use the selected plan date range
- use the student's weekly study availability
- respect preferred study-session duration
- schedule higher-priority work deterministically
- stop scheduling work after its deadline
- return remaining work as `unscheduled_tasks`
- persist the generated plan and sessions

## Manual Sessions

Students may add manual sessions to a study plan.

Manual sessions are stored with:

```text
origin = manual
```

Generated sessions are stored with:

```text
origin = generated
```

This distinction is important during regeneration.

## Generated Plan Regeneration

Generated plans can be refreshed using the latest Academic Tasks and the latest scheduling preferences.

Regeneration:

1. Keeps the existing `study_plan.id`.
2. Loads the plan's manual sessions.
3. Treats manual sessions as blocked scheduling windows.
4. Prevents newly generated sessions from being scheduled in the past.
5. Generates a new schedule from the latest eligible Academic Tasks.
6. Replaces only sessions whose origin is `generated`.
7. Preserves all manual sessions.
8. Returns remaining unscheduled work to the frontend.

The final replacement operation uses a trusted PostgreSQL RPC so deletion of the old generated sessions, insertion of the new generated sessions, and plan refresh occur transactionally.

## Study Plan API Integration

The main FastAPI router exposes:

```text
/api/study-plans
/api/study-plans/{study_plan_id}
/api/study-plans/{study_plan_id}/sessions
/api/study-plans/{study_plan_id}/sessions/{study_session_id}

/api/study-plan-generation
/api/study-plan-generation/{study_plan_id}/regenerate
```

The Study Plan workspace is also available from the authenticated application navigation.

---

# Implemented Database Resources

```text
auth.users

public.profiles
public.learning_profiles
public.learning_profile_subjects
public.learning_output_confidences
public.study_availability

public.subjects
public.study_files
public.file_processing_jobs
public.study_file_contents
public.study_file_chunks
public.study_file_ai_chunks

public.study_conversations
public.study_messages
public.reviewers

public.flashcard_decks
public.flashcards

public.quizzes
public.quiz_questions
public.quiz_attempts
public.quiz_attempt_answers

public.academic_tasks
public.study_plans
public.study_sessions
```

Private Storage:

```text
study-materials
```

---

# Security Boundaries

1. Supabase backend credentials remain backend-only.
2. Gemini credentials remain backend-only.
3. Processor credentials remain backend-only.
4. Browser code uses only publishable Supabase credentials.
5. Student database access is protected by RLS.
6. Study files remain private.
7. FastAPI derives student identity from bearer authentication.
8. RAG requests cannot override `user_id`.
9. Clients cannot submit arbitrary conversation memory.
10. Clients cannot submit summary state.
11. Conversation summary state is backend-managed.
12. Raw embeddings are not returned to the browser.
13. Raw retrieved chunks are not persisted as conversation source metadata.
14. Public errors must not expose tokens, credentials, SQL details, or provider tracebacks.
15. Flashcard requests cannot choose a trusted `user_id`.
16. Flashcard source loading verifies authenticated ownership and readiness.
17. Browser roles cannot directly call trusted Flashcard persistence RPCs.
18. Normal Quiz responses do not expose private answer-key fields.
19. Quiz grading uses trusted backend operations and RPCs.
20. Completed-attempt review requires authenticated ownership and completed state.
21. Academic Tasks are owner-scoped through authenticated backend operations and database RLS.
22. Academic Task requests cannot provide or override a trusted `user_id`.
23. Priority context is loaded by the backend for the authenticated student.
24. Clients cannot provide trusted priority scores, availability, or output-confidence context.
25. Study plans and study sessions are owner-scoped to the authenticated student.
26. Study Plan requests cannot provide or override a trusted `user_id`.
27. Scheduling availability, timezone, and preferred duration are loaded by trusted backend services.
28. Regeneration preserves manual sessions and replaces only generated sessions.
29. The generated-session replacement RPC is restricted to trusted backend execution.

---

# Migration Workflow

```mermaid
flowchart LR
    CREATE["Create Migration"]
    WRITE["Write SQL"]
    DIFF["git diff --check"]
    DRY["Linked Dry Run"]
    PUSH["db push"]
    VERIFY["Migration List"]
    TYPES["Generate database.ts"]
    TEST["Run Tests"]

    CREATE --> WRITE
    WRITE --> DIFF
    DIFF --> DRY
    DRY --> PUSH
    PUSH --> VERIFY
    VERIFY --> TYPES
    TYPES --> TEST
```

Applied migrations must never be edited.

Corrections require a new timestamped migration.

---

# Phase 5G Migrations

```text
20260806192800_create_study_conversations_and_messages.sql
20260806200500_fix_study_message_outcome_constraint.sql
20260806223000_add_study_conversation_summary_state.sql
20260806234000_restrict_study_conversation_summary_updates.sql
```

---

# Phase 6A Migrations

```text
20260807230500_create_reviewers.sql
20260808053929_create_reviewers_foundation.sql
```

---

# Track A Flashcard Migrations

```text
20260809142000_create_flashcard_foundation.sql
20260809145600_create_flashcard_persistence_rpc.sql
```

---

# Track B Quiz Migrations

```text
20260809204500_create_quizzes_foundation.sql
20260809211600_create_quiz_persistence_rpc.sql
20260809223500_create_quiz_attempt_foundation.sql
20260809225500_create_quiz_attempt_rpcs.sql
```

---

# Phase 7 Academic Task Migrations

```text
20260809054523_create_academic_tasks.sql
20260809153000_add_output_confidence_and_task_output_type.sql
```

The first Phase 7 migration creates the student-owned `academic_tasks` table, validation, triggers, indexes, grants, and Row Level Security.

The second migration introduces academic output-confidence storage and adds `output_type` to academic tasks so deterministic priority can use confidence for the skill required by the task.

---

# Track D Study Plan Migrations

```text
20260810002500_create_study_plans_foundation.sql
20260811002500_add_study_plan_regeneration_rpc.sql
```

The foundation migration creates the student-owned `study_plans` and `study_sessions` tables, validation constraints, ownership relationships, indexes, timestamps, privileges, and Row Level Security.

The regeneration migration adds the trusted transactional `replace_generated_study_plan_sessions` RPC and aligns generated-session titles with the 200-character Academic Task title limit.

These Track D migration files have been applied to the shared linked Supabase database during coordinated integration.

---

# Phase 6A Reviewer Backend

Phase 6A introduces the backend foundation for generated study reviewers.

A reviewer can be generated from:

- One ready study file
- All ready study files within one subject

Reviewer generation does not use similarity-based RAG retrieval.

It loads processed source-aware chunks in deterministic file and chunk order so the reviewer can represent the selected material broadly rather than only answering a similarity-based question.

```mermaid
flowchart LR
    REQUEST["Authenticated Reviewer Request"]

    API["Reviewer API"]
    ORCHESTRATION["Reviewer Orchestration"]

    SOURCE["Reviewer Source Loader"]
    GENERATION["Reviewer Generation"]
    PERSISTENCE["Reviewer Service"]

    FILES[("study_files")]
    CHUNKS[("study_file_chunks")]
    REVIEWERS[("reviewers")]

    GEMINI["Gemini Generation Provider"]

    REQUEST --> API
    API --> ORCHESTRATION

    ORCHESTRATION --> SOURCE
    SOURCE --> FILES
    SOURCE --> CHUNKS

    ORCHESTRATION --> GENERATION
    GENERATION --> GEMINI

    ORCHESTRATION --> PERSISTENCE
    PERSISTENCE --> REVIEWERS
```

Generated reviewer content is structured as:

```text
overview
topics
  title
  summary
  key_points
  definitions
```

Saved reviewer metadata includes:

```text
scope_type
subject_id
study_file_id
reviewer_length
sources
generation_model
generation_count
generated_at
```

Reviewer sources preserve the originating study file, chunk index, and available locator metadata.

Current protected endpoints include:

```text
POST   /api/reviewers/generate
GET    /api/reviewers
GET    /api/reviewers/{reviewer_id}
DELETE /api/reviewers/{reviewer_id}
POST   /api/reviewers/{reviewer_id}/regenerate
```

The authenticated user's identity comes from the validated bearer token.

Reviewer requests cannot choose a trusted `user_id`.

Reviewer insert and generation operations are performed through the trusted backend.

Browser clients do not receive direct insert or update access to reviewer records.

Saved reviewer management and regeneration were implemented in Phase 6C.

Large-material multi-pass reviewer generation was implemented in Phase 6D.

---

# Phase 6B Reviewer Frontend

Phase 6B connects the Reviewer backend to the protected Next.js application.

Implemented frontend route:

```text
/reviewers
```

The Reviewer workspace provides generation controls and structured reviewer display.

Generation options include:

```text
Scope:
- Whole subject
- Single study material

Length:
- Short
- Medium
- Long
```

The frontend loads authenticated subjects and only study files with:

```text
processing_status = ready
```

The browser sends reviewer-generation requests through the authenticated Reviewer API client using the student's Supabase access token.

Live integration verified reviewer generation, persistence, structured display, and source rendering.

---

# Phase 6D Large-Material Reviewer Generation

Phase 6D extends reviewer generation so study material exceeding the normal single-pass prompt limit can still be processed without silently truncating source content.

The existing source loader continues to load the complete authenticated source bundle.

Large-material handling begins only inside the reviewer generation layer.

## Generation Strategy

Reviewer generation uses two paths:

```text
Source bundle at or below single-pass limit
→ Complete reviewer prompt
→ Gemini
→ Validated ReviewerContent
```

For oversized source bundles:

```text
Complete source bundle
→ ReviewerSourceBatcher
→ Ordered source batches
→ Partial reviewer generation
→ Final synthesis prompt
→ Gemini
→ Validated ReviewerContent
```

The default limits are:

| Limit | Value |
|---|---:|
| Normal single-pass source limit | 80,000 characters |
| Default large-material batch limit | 60,000 characters |
| Maximum configurable batch limit | 80,000 characters |

The batcher splits only at existing source-chunk boundaries.

It does not truncate a chunk, remove chunks, duplicate chunks, or change their original order.

## Large-Material Flow

```mermaid
flowchart TD
    REQUEST["Reviewer Request"]
    SOURCE["Complete ReviewerSourceBundle"]

    SINGLE{"Fits single-pass limit?"}

    COMPLETE_PROMPT["Complete Reviewer Prompt"]
    BATCHER["ReviewerSourceBatcher"]

    BATCH1["Source Batch 1"]
    BATCH2["Source Batch 2"]
    BATCHN["Source Batch N"]

    PARTIAL1["Partial Reviewer 1"]
    PARTIAL2["Partial Reviewer 2"]
    PARTIALN["Partial Reviewer N"]

    SYNTHESIS["Final Synthesis Prompt"]
    GEMINI["Gemini Generation"]
    CONTENT["Validated ReviewerContent"]
    SAVE["Reviewer Persistence"]

    REQUEST --> SOURCE
    SOURCE --> SINGLE

    SINGLE -->|Yes| COMPLETE_PROMPT
    COMPLETE_PROMPT --> GEMINI

    SINGLE -->|No| BATCHER

    BATCHER --> BATCH1
    BATCHER --> BATCH2
    BATCHER --> BATCHN

    BATCH1 --> PARTIAL1
    BATCH2 --> PARTIAL2
    BATCHN --> PARTIALN

    PARTIAL1 --> SYNTHESIS
    PARTIAL2 --> SYNTHESIS
    PARTIALN --> SYNTHESIS

    SYNTHESIS --> GEMINI
    GEMINI --> CONTENT
    CONTENT --> SAVE
```

Each partial batch prompt identifies itself as one ordered portion of a larger source collection.

The model is instructed to use only concepts supported by that batch and not assume information from unseen batches.

The synthesis prompt receives the ordered validated partial reviewers and combines them into one final reviewer.

## Compatibility With Existing Reviewer Generation

Materials within the normal source limit continue through the original single-pass reviewer flow.

Existing behaviors remain enforced:

- Short, medium, and long reviewer lengths
- Strict JSON response validation
- One controlled repair attempt for malformed output
- Provider identity validation
- Structured overview, topics, key points, and definitions
- File-level and subject-level scopes
- Authenticated ownership validation
- Complete source tracking
- Existing reviewer persistence

## Source Metadata

Even when generation uses multiple batches, final generation metadata reports the complete original source bundle:

```text
source_character_count
source_chunk_count
source_file_count
```

Saved reviewer source metadata continues to reference original source chunks rather than generated partial reviewers.

## Database Impact

Phase 6D introduces no new table, migration, or RLS policy.

It reuses:

```text
study_files
study_file_chunks
reviewers
```

---

# Planned Future Features

Future phases may introduce:

- Study analytics
- Deployment and monitoring improvements

These features must not be documented as implemented until their code, migrations, tests, and security boundaries exist.
- Study analytics
- Deployment and monitoring improvements

These features must not be documented as implemented until their code, migrations, tests, and security boundaries exist.

---

# Architecture Update Rules

Update this document whenever:

1. A major service is introduced.
2. A new API endpoint is added.
3. A database table is created.
4. A new trusted RPC is created.
5. A major data flow changes.
6. A planned feature becomes implemented.
7. A security boundary changes.
8. A development phase is completed.