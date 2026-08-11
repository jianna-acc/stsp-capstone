# STS Capstone — STUDY AI Architecture

This document describes the current architecture of STUDY AI.

The system currently includes:

- Next.js frontend
- Mantine UI
- Supabase Authentication
- Hosted Supabase PostgreSQL
- Private Supabase Storage
- Student learning-profile onboarding
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
- Student-owned academic task CRUD
- Academic output confidence by skill type
- Deterministic academic-task priority scoring
- Explainable seven-factor priority breakdowns
- Protected Academic Tasks frontend
- Live priority recalculation after task changes

The application includes protected Reviewer, Academic Tasks, and Study Plan frontends.

Future phases may add flashcards, quizzes, analytics, and deployment improvements.

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
| Phase 7A–7E | Academic task persistence, output confidence, CRUD, deterministic priority, frontend, live integration | Implemented |
| Track D | Study-plan persistence, deterministic scheduling, Academic Task integration, calendar workspace, manual sessions, and regeneration | Implemented |
| Later phases | Flashcards, quizzes, analytics, deployment | Planned |

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

        TASK_API["Academic Task API"]
        TASK_SERVICE["Academic Task Service"]
        TASK_PRIORITY["Academic Task Priority Service"]
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

    API --> TASK_API
    TASK_API --> TASK_SERVICE
    TASK_API --> TASK_PRIORITY
    TASK_SERVICE --> DATABASE
    TASK_PRIORITY --> TASK_ENGINE
    TASK_PRIORITY --> DATABASE
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

The implemented output-confidence categories are:

```text
writing
computation
research
presentation
creative
reading_analysis
memorization
```

These values are stored in:

```text
public.learning_output_confidences
```

Academic-task priority uses output confidence based on the task's `output_type`.

The legacy subject-level `confidence_level` is not used by the Academic Task priority engine.

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

Gemini credentials remain inside `backend/.env`.

Normal automated tests use fake providers and do not call live Gemini services.

---

# AI Preparation and Vector Indexing

```mermaid
flowchart LR
    DOCUMENT["Extracted Text"]
    PREPARER["StudyMaterialPreparer"]
    CHUNKER["TextChunker"]
    BATCHER["EmbeddingBatchPreparer"]

    INDEXER["StudyMaterialVectorIndexer"]
    EMBEDDER["StudyMaterialEmbedder"]
    GEMINI["Gemini Embedding API"]

    VALIDATION["Vector Validation"]
    RPC["replace_study_file_ai_chunks"]
    VECTOR_TABLE[("study_file_ai_chunks")]

    DOCUMENT --> PREPARER
    PREPARER --> CHUNKER
    CHUNKER --> BATCHER

    BATCHER --> INDEXER
    INDEXER --> EMBEDDER
    EMBEDDER --> GEMINI

    GEMINI --> VALIDATION
    VALIDATION --> INDEXER

    INDEXER --> RPC
    RPC --> VECTOR_TABLE
```

Current vector configuration uses:

```text
Embedding dimensions: 768
Distance strategy: cosine
Index strategy: HNSW
```

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

---

# Protected RAG API

Main endpoint:

```text
POST /api/rag/answer
```

Authentication:

```text
Authorization: Bearer <Supabase access token>
```

The request may contain:

- `question`
- `conversation_id`
- `subject_id`
- `study_file_id`
- Retrieval tuning values

It must not contain a trusted `user_id`.

---

# Study Assistant Frontend

```mermaid
flowchart LR
    PAGE["/study-assistant"]
    WORKSPACE["StudyAssistantWorkspace"]

    HISTORY["ConversationHistoryPanel"]
    PANEL["StudyAssistantPanel"]

    CONVERSATION_CLIENT["Conversation API Client"]
    RAG_CLIENT["RAG API Client"]

    CONVERSATION_API["/api/study-conversations"]
    RAG_API["/api/rag/answer"]

    PAGE --> WORKSPACE

    WORKSPACE --> HISTORY
    WORKSPACE --> PANEL

    WORKSPACE --> CONVERSATION_CLIENT
    CONVERSATION_CLIENT --> CONVERSATION_API

    PANEL --> RAG_CLIENT
    RAG_CLIENT --> RAG_API
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

---

# Reviewer Frontend

The protected Reviewer workspace is available at:

```text
/reviewers
```

The frontend follows the same authenticated FastAPI-client pattern used by the Study Assistant.

```mermaid
flowchart LR
    PAGE["/reviewers"]
    WORKSPACE["ReviewerWorkspace"]

    FORM["ReviewerGenerationForm"]
    RESULT["ReviewerResult"]

    OPTIONS["Reviewer Filter Options"]
    API_CLIENT["Reviewer API Client"]

    SUPABASE["Supabase"]
    REVIEWER_API["POST /api/reviewers/generate"]

    PAGE --> WORKSPACE

    WORKSPACE --> FORM
    WORKSPACE --> RESULT

    PAGE --> OPTIONS
    OPTIONS --> SUPABASE

    FORM --> API_CLIENT
    API_CLIENT --> REVIEWER_API

    REVIEWER_API --> RESULT
```

The Reviewer frontend supports:

- Whole-subject reviewer generation
- Single-study-material reviewer generation
- `short`, `medium`, and `long` reviewer lengths
- Authenticated subject loading
- Ready study-material filtering
- Loading and safe error states
- Structured overview display
- Topic summaries
- Key points
- Important definitions
- Grounded source references
- Saved reviewer persistence
- Saved reviewer management
- Reviewer regeneration

Only study files that have completed processing and are in the `ready` state are available for file-scope generation.

Generated reviewers are persisted by the backend before being returned to the frontend.

Large-material reviewer generation is handled through deterministic source batching and final synthesis.

---

# Phase 5G Conversation Persistence

Implemented tables:

```text
study_conversations
study_messages
```

```mermaid
erDiagram
    AUTH_USERS ||--o{ STUDY_CONVERSATIONS : owns
    SUBJECTS ||--o{ STUDY_CONVERSATIONS : filters
    STUDY_FILES ||--o{ STUDY_CONVERSATIONS : filters
    STUDY_CONVERSATIONS ||--o{ STUDY_MESSAGES : contains
```

A conversation stores:

- Owner
- Title
- Optional subject
- Optional study file
- Summary state
- Creation time
- Update time
- Last message time

A saved message stores:

- Role
- Content
- Assistant outcome
- Safe citation metadata
- Creation time

---

# Conversation-Aware RAG

```mermaid
sequenceDiagram
    actor Student
    participant Frontend as Study Assistant
    participant API as RAG API
    participant Service as Conversation RAG Service
    participant Repository as Repository
    participant RAG as RAG Service

    Student->>Frontend: Ask first question
    Frontend->>API: Question

    API->>Service: Authenticated request
    Service->>Repository: Create conversation
    Service->>Repository: Save user message
    Service->>RAG: Generate grounded answer
    RAG-->>Service: Answer
    Service->>Repository: Save assistant message

    Service-->>Frontend: Answer + conversation_id

    Student->>Frontend: Ask follow-up
    Frontend->>API: Question + conversation_id

    API->>Service: Continue conversation
    Service->>Repository: Verify ownership
    Service->>Repository: Load memory
    Service->>RAG: Generate grounded answer
    Service->>Repository: Save new messages

    Service-->>Frontend: Updated answer
```

---

# Bounded Conversation Memory

Current limits:

| Limit | Value |
|---|---:|
| Maximum memory items | 10 |
| Maximum memory characters | 8,000 |
| Recent messages without summary | 10 |
| Recent messages with summary | 9 |
| Maximum summary size | 4,000 characters |
| Summary version | 1 |

When a summary exists:

```text
1 summary
+
9 recent messages
=
10 maximum memory items
```

---

# Deterministic Conversation Summary

Older messages may be compressed into a deterministic backend summary.

The summary builder:

- Does not call Gemini
- Does not use another AI provider
- Produces deterministic output
- Removes citation markers
- Has a 4,000-character limit
- Keeps the newest relevant summary entries

Internal summary fields:

```text
summary_text
summarized_message_count
summary_updated_at
summary_version
```

These fields must not be consumed or modified by the frontend.

---

# Evidence Boundary

Conversation memory helps interpret follow-up questions.

It does not become factual evidence.

Correct factual evidence flow:

```text
Question
→ Query Embedding
→ Owned Vector Retrieval
→ Retrieved Study Material
→ Grounded Prompt
→ Gemini Answer
→ Citations
```

Conversation history is context only.

---

# Academic Tasks and Deterministic Priority

The protected Academic Tasks workspace is available at:

```text
/academic-tasks
```

Academic tasks are student-owned records containing:

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

## Academic Task Architecture

```mermaid
flowchart LR
    STUDENT["Authenticated Student"]
    WORKSPACE["Academic Tasks Workspace"]
    CLIENT["Authenticated Academic Task API Client"]

    API["Academic Task FastAPI Routes"]
    CRUD["Academic Task Service"]
    REPOSITORY["Academic Task Repository"]

    PRIORITY_SERVICE["Academic Task Priority Service"]
    CONTEXT_REPOSITORY["Priority Context Repository"]
    CONTEXT["Priority Context Resolver"]
    ENGINE["Deterministic Priority Engine"]

    TASKS[("academic_tasks")]
    PROFILE[("profiles")]
    CONFIDENCE[("learning_output_confidences")]
    AVAILABILITY[("study_availability")]

    STUDENT --> WORKSPACE
    WORKSPACE --> CLIENT
    CLIENT --> API

    API --> CRUD
    CRUD --> REPOSITORY
    REPOSITORY --> TASKS

    API --> PRIORITY_SERVICE
    PRIORITY_SERVICE --> CONTEXT_REPOSITORY

    CONTEXT_REPOSITORY --> PROFILE
    CONTEXT_REPOSITORY --> CONFIDENCE
    CONTEXT_REPOSITORY --> AVAILABILITY

    PRIORITY_SERVICE --> CONTEXT
    CONTEXT --> PRIORITY_SERVICE
    PRIORITY_SERVICE --> ENGINE
```

Priority calculation is performed by deterministic backend code.

It does not use Gemini or another generative AI provider.

## Priority Factors

The engine combines seven factors:

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

Higher factor scores mean the factor increases task urgency.

Completed and cancelled tasks receive:

```text
total priority = 0
```

Previous performance currently uses a neutral fallback because a production quiz/performance data source is not yet connected.

Missing confidence or unavailable context uses controlled neutral behavior rather than inventing student information.

## Priority API

The frontend receives authoritative ordering from:

```text
GET /api/academic-tasks/prioritized
```

The response contains the task and its complete seven-factor priority breakdown.

The backend sorts by:

```text
1. Total priority score descending
2. Deadline ascending
3. Creation time ascending
4. Task ID
```

The frontend does not duplicate the priority formula.

## Academic Tasks Frontend

The workspace supports:

- Create task
- Edit task
- Change task status
- Delete task
- Display deterministic priority
- Display urgency category
- Expand `Why this priority?`
- Display all seven factor scores
- Refresh priority after successful create, edit, status change, and deletion
- Responsive independent task columns

The independent-column layout allows one task's priority explanation to expand without stretching or displacing task cards in the opposite column.

After a successful mutation, the frontend requests the prioritized endpoint again so the backend remains the source of truth for score and ordering.

## Live Integration

Phase 7E live integration verified:

```text
Next.js frontend
→ authenticated FastAPI request
→ Supabase persistence and priority context
→ deterministic priority engine
→ prioritized API response
→ Academic Tasks workspace
```

Live validation covered:

```text
create
read
edit
status change
priority recalculation
priority explanation
completed-task zero priority
delete
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
7. FastAPI derives identity from bearer authentication.
8. RAG requests cannot override `user_id`.
9. Clients cannot submit arbitrary conversation memory.
10. Clients cannot submit summary state.
11. Conversation summaries are backend-managed.
12. Raw embeddings are not returned to the browser.
13. Raw retrieved chunks are not persisted as conversation source metadata.
14. Public errors must not expose tokens or credentials.
15. Academic tasks are owner-scoped through authenticated backend operations and database RLS.
16. Academic Task requests cannot provide or override a trusted `user_id`.
17. Priority context is loaded by the backend for the authenticated student.
18. Clients cannot provide trusted priority scores or priority context.
19. Study plans and study sessions are owner-scoped to the authenticated student.
20. Study Plan requests cannot provide or override a trusted `user_id`.
21. Scheduling availability, timezone, and preferred duration are loaded by trusted backend services.
22. Regeneration preserves manual sessions and replaces only generated sessions.
23. The generated-session replacement RPC is restricted to trusted backend execution.
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

The reviewer foundation migration creates the owned `reviewers` table, reviewer scope and length constraints, ownership validation, timestamps, indexes, and Row Level Security policies.

---

# Phase 7 Academic Task Migrations

```text
20260809054523_create_academic_tasks.sql
20260809153000_add_output_confidence_and_task_output_type.sql
```

The first migration creates the student-owned `academic_tasks` table, subject-ownership validation, indexes, triggers, grants, and Row Level Security.

The second migration introduces academic output-confidence storage and adds `output_type` to academic tasks so deterministic priority can use confidence for the skill required by the task.

---

# Track D Study Plan Migrations

```text
20260810002500_create_study_plans_foundation.sql
20260811002500_add_study_plan_regeneration_rpc.sql
```

The foundation migration creates the student-owned `study_plans` and `study_sessions` tables, validation constraints, ownership relationships, indexes, timestamps, privileges, and Row Level Security.

The regeneration migration adds the trusted transactional `replace_generated_study_plan_sessions` RPC and aligns generated-session titles with the 200-character Academic Task title limit.

These migration files are implemented in Track D. Application to the shared linked Supabase database must be coordinated during integration.

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

Quiz generation remains deferred to a later phase.

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

- Flashcards
- Quizzes
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