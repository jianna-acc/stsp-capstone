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

The application now also includes a protected Reviewer frontend for generating structured reviewers from a whole subject or one ready study material.

Future phases may add reviewer regeneration, scalable multi-pass generation for very large materials, flashcards, quizzes, study planning, scheduling, analytics, and deployment improvements.
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
| Later phases | Reviewer history/regeneration, scalable multi-pass generation, flashcards, quizzes, study plans, analytics, deployment | Planned |

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
        REVIEWER_SERVICE["Reviewer Persistence Service"]
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
    REVIEWER_GENERATION --> GEMINI
    REVIEWER_SERVICE --> DATABASE
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
    AVAILABILITY["Study Availability"]

    PROFILES[("profiles")]
    LEARNING_TABLE[("learning_profiles")]
    SUBJECT_TABLE[("learning_profile_subjects")]
    AVAILABILITY_TABLE[("study_availability")]

    STUDENT --> ONBOARDING

    ONBOARDING --> PROFILE
    ONBOARDING --> LEARNING
    ONBOARDING --> STRENGTHS
    ONBOARDING --> AVAILABILITY

    PROFILE --> PROFILES
    LEARNING --> LEARNING_TABLE
    STRENGTHS --> SUBJECT_TABLE
    AVAILABILITY --> AVAILABILITY_TABLE
```

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

Only study files that have completed processing and are in the `ready` state are available for file-scope generation.

Generated reviewers are persisted by the backend before being returned to the frontend.

Saved-reviewer history, reopening, deletion controls, and regeneration remain deferred to the next Reviewer phase.

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

# Implemented Database Resources

```text
auth.users

public.profiles
public.learning_profiles
public.learning_profile_subjects
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

````
# Phase 6A Migrations

```text
20260807230500_create_reviewers.sql
20260808053929_create_reviewers_foundation.sql
```

This migration creates the owned `reviewers` table, reviewer scope and length constraints, ownership validation, timestamps, indexes, and Row Level Security policies.

---

# Phase 6A Reviewer Backend

Phase 6A introduces the backend foundation for generated study reviewers.

A reviewer can currently be generated from:

- One ready study file
- All ready study files within one subject

Reviewer generation does not use similarity-based RAG retrieval. It loads the processed source-aware chunks in deterministic file and chunk order so that the reviewer can represent the selected material broadly rather than only answering a similarity-based question.

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

Current protected endpoints are:

```text
POST   /api/reviewers/generate
GET    /api/reviewers
GET    /api/reviewers/{reviewer_id}
DELETE /api/reviewers/{reviewer_id}
```

The authenticated user's identity comes from the validated bearer token. Reviewer requests cannot choose a trusted `user_id`.

Reviewer insert and generation operations are performed through the trusted backend. Browser clients do not receive direct insert or update access to reviewer records.

Phase 6A did not include a student-facing reviewer workspace. That workspace is now implemented in Phase 6B.

The following capabilities remain deferred:

- Saved reviewer history and reopening
- Reviewer deletion controls in the frontend
- Reviewer regeneration
- Multi-pass generation for source collections that exceed the current bounded prompt size
- Quiz generation

# Phase 6B Reviewer Frontend

Phase 6B connects the Phase 6A Reviewer backend to the protected Next.js application.

Implemented frontend route:

```text
/reviewers
```

The Reviewer workspace provides:

```text
ReviewerWorkspace
├── ReviewerGenerationForm
└── ReviewerResult
```

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

Live integration verified:

- Single study material + Medium reviewer
- Whole subject + Medium reviewer
- Whole subject + Short reviewer
- Multi-file subject generation
- Reviewer persistence
- Structured overview rendering
- Topic/key-point rendering
- Important-term rendering
- Source-location rendering

During live integration, short whole-subject generation exposed an output truncation issue. The Short generation output budget was increased from 2,048 to 4,096 tokens so the provider has enough room to complete valid structured JSON while the prompt still requests concise content.

Reviewer response validation still remains strict, and malformed provider output continues to receive only one controlled repair attempt.

Phase 6B intentionally does not yet include:

- Saved reviewer history UI
- Opening previously saved reviewers
- Reviewer deletion controls in the frontend
- Reviewer regeneration
- Multi-pass generation for very large materials
- Quiz generation

---

# Planned Future Features

Future phases may introduce:

- Saved reviewer history and reopening
- Reviewer regeneration
- Scalable multi-pass reviewer generation for very large materials
- Flashcards
- Quizzes
- Academic tasks
- Study-plan generation
- Calendar scheduling
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