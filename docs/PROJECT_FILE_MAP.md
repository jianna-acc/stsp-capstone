<!-- File: /docs/PROJECT_FILE_MAP.md -->
<!-- Purpose: Master map of important project files, purposes, owners, statuses, and system connections. -->

# STS Capstone — STUDY AI Project File Map

This document is the central reference for important project files.

Update it whenever files, APIs, migrations, owners, or major system connections change.

---

# Status Definitions

| Status | Meaning |
|---|---|
| Planned | Future work |
| Created | Exists but not fully validated |
| Ready | Independently validated |
| Integrated | Connected and validated with the application |
| Generated | Tool-generated |
| Local Only | Must not be committed |
| Deprecated | Replaced or removed |

---

# Phase Status

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | Foundation and authentication | Integrated |
| Phase 2 | Learning-profile onboarding | Integrated |
| Phase 3 | Subjects and study-material processing | Integrated |
| Phase 4 | AI provider, preparation, embeddings, vectors, retrieval | Integrated |
| Phase 5A–5F | RAG and Study Assistant | Integrated |
| Phase 5G | Saved conversations, memory, summaries, history UI | Integrated |
| Phase 6A | Reviewer backend foundation | Integrated |
| Later | Reviewer frontend/regeneration, flashcards, quizzes, planning, analytics | Planned |

---

# Team Ownership

| Member | Main Responsibility |
|---|---|
| Member 1 | Technical lead, repository, authentication, integration |
| Member 2 | Design system and frontend UI |
| Member 3 | FastAPI, file processing, retrieval, AI |
| Member 4 | Supabase database and security |
| Member 5 | Testing and documentation |

---

# Root

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/.gitignore` | Integrated | Member 1 | Ignores secrets and generated files | Entire repository |
| `/README.md` | Integrated | Member 1 | Project overview | `/docs` |
| `/package.json` | Ready | Member 1 | Root tooling | Supabase CLI |
| `/package-lock.json` | Ready | Member 1 | Root dependency lock | npm |
| `/frontend` | Integrated | Members 1–2 | Next.js application | Supabase, FastAPI |
| `/backend` | Integrated | Member 3 | FastAPI and AI | Supabase, Gemini |
| `/supabase` | Integrated | Member 4 | Migrations and CLI | Hosted Supabase |
| `/docs` | Integrated | Members 1–5 | Technical documentation | Entire project |

---

# Documentation

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/docs/ARCHITECTURE.md` | Integrated | Member 1 | System architecture | Entire project |
| `/docs/PROJECT_FILE_MAP.md` | Integrated | Member 1 | Master file map | Entire project |
| `/docs/api-contracts.md` | Integrated | Member 3 | API/RPC contracts | Frontend, backend, Supabase |
| `/docs/authentication.md` | Integrated | Member 5 | Authentication architecture | Supabase Auth |
| `/docs/database.md` | Integrated | Member 4 | Database architecture | Supabase |
| `/docs/setup-guide.md` | Integrated | Member 5 | Development setup | Entire project |
| `/docs/testing-checklist.md` | Integrated | Member 5 | Validation status | Entire project |
| `/docs/AI_PROVIDER.md` | Integrated | Member 3 | AI provider design | Gemini |
| `/docs/AI_PREPARATION_PIPELINE.md` | Integrated | Member 3 | AI chunk preparation | File processing |
| `/docs/AI_VECTOR_PIPELINE.md` | Integrated | Members 3,5 | Vector indexing | Gemini, pgvector |
| `/docs/AI_RETRIEVAL_DESIGN.md` | Integrated | Members 3–5 | Retrieval design | Vector search |
| `/docs/AI_QUERY_EMBEDDING.md` | Integrated | Member 3 | Query embedding | Retrieval |
| `/docs/AI_RAG_API_ENDPOINT.md` | Integrated | Member 3 | RAG endpoint | FastAPI, frontend |

---

# Frontend Foundation

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/package.json` | Integrated | Member 1 | Frontend dependencies/scripts | Next.js |
| `/frontend/package-lock.json` | Integrated | Member 1 | Dependency lock | npm |
| `/frontend/tsconfig.json` | Integrated | Member 1 | TypeScript configuration | Frontend |
| `/frontend/eslint.config.mjs` | Integrated | Member 1 | ESLint configuration | Frontend |
| `/frontend/app/layout.tsx` | Integrated | Member 1 | Root layout | Providers |
| `/frontend/app/providers.tsx` | Integrated | Member 2 | Mantine providers | Entire UI |
| `/frontend/app/globals.css` | Integrated | Member 2 | Global styles | Entire UI |
| `/frontend/theme/theme.ts` | Integrated | Member 2 | Mantine theme | Providers |
| `/frontend/theme/colors.ts` | Integrated | Member 2 | Color tokens | Theme |
| `/frontend/theme/components.ts` | Integrated | Member 2 | Component defaults | Theme |

---

# Supabase Frontend Clients

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/lib/supabase/config.ts` | Integrated | Member 1 | Safe Supabase config | Browser/server clients |
| `/frontend/lib/supabase/client.ts` | Integrated | Member 1 | Browser client | Client Components |
| `/frontend/lib/supabase/server.ts` | Integrated | Member 1 | Server client | Server Components |
| `/frontend/lib/supabase/proxy.ts` | Integrated | Member 1 | Session refresh | Proxy |
| `/frontend/proxy.ts` | Integrated | Member 1 | Root session proxy | Supabase Auth |
| `/frontend/types/database.ts` | Generated | Supabase CLI | Schema types | Frontend Supabase clients |

---

# Authentication

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/features/auth/types.ts` | Integrated | Member 1 | Auth types | Forms/actions |
| `/frontend/features/auth/validation.ts` | Integrated | Member 1 | Auth validation | Server Actions |
| `/frontend/features/auth/actions/register.ts` | Integrated | Member 1 | Registration | Supabase Auth |
| `/frontend/features/auth/components/RegisterForm.tsx` | Integrated | Member 1 | Registration form | Register action |
| `/frontend/features/auth/components/LoginForm.tsx` | Integrated | Member 1 | Login form | Supabase Auth |
| `/frontend/app/(auth)/register/page.tsx` | Integrated | Member 1 | Registration page | Auth |
| `/frontend/app/(auth)/login/page.tsx` | Integrated | Member 1 | Login page | Auth |
| `/frontend/app/auth/confirm/route.ts` | Integrated | Member 1 | Confirmation callback | Supabase Auth |

---

# Learning Profile

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/features/learning-profile/types.ts` | Integrated | Member 2 | Profile types | Onboarding |
| `/frontend/features/learning-profile/validation.ts` | Integrated | Member 2 | Input validation | Mutations |
| `/frontend/features/learning-profile/server/queries.ts` | Integrated | Member 2 | Load profile | Supabase |
| `/frontend/features/learning-profile/server/mutations.ts` | Integrated | Member 2 | Save profile | Supabase RPC |
| `/frontend/features/learning-profile/server/guards.ts` | Integrated | Member 2 | Onboarding guards | Protected routes |
| `/frontend/app/(protected)/onboarding` | Integrated | Member 2 | Onboarding flow | Learning-profile feature |
| `/frontend/app/(protected)/profile/page.tsx` | Integrated | Member 2 | Profile display | Learning profile |

---

# Subjects and Files

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/features/subjects/types.ts` | Integrated | Members 1,2 | Subject types | Subject feature |
| `/frontend/features/subjects/queries.ts` | Integrated | Members 1,2 | Load subjects | Supabase |
| `/frontend/features/subjects/actions.ts` | Integrated | Members 1,2 | Subject CRUD | Supabase |
| `/frontend/app/(protected)/subjects/page.tsx` | Integrated | Members 1,2 | Subject management | Subject feature |
| `/frontend/app/(protected)/subjects/[subjectId]/page.tsx` | Integrated | Members 1,2 | Subject workspace | Files |
| `/frontend/features/files/types.ts` | Integrated | Members 1,3 | File types | File feature |
| `/frontend/features/files/constants.ts` | Integrated | Members 1,3 | File limits/statuses | Upload UI |
| `/frontend/features/files/queries.ts` | Integrated | Members 1,3 | Load files | Supabase |
| `/frontend/features/files/actions.ts` | Integrated | Members 1,3 | File operations | Database, Storage |
| `/frontend/features/files/upload.ts` | Integrated | Member 3 | TUS upload | Supabase Storage |
| `/frontend/features/files/components/FileUploadManager.tsx` | Integrated | Members 2,3 | File management UI | File actions |
| `/frontend/features/files/components/FilePreviewModal.tsx` | Integrated | Member 2 | File preview | Signed URLs |

---

# Study Assistant Frontend

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/app/(protected)/study-assistant/page.tsx` | Integrated | Frontend | Protected Study Assistant page | Workspace |
| `/frontend/features/study-assistant/api.ts` | Integrated | Frontend | Authenticated RAG API client | `/api/rag/answer` |
| `/frontend/features/study-assistant/conversations-api.ts` | Integrated | Frontend | Saved conversation API client | `/api/study-conversations` |
| `/frontend/features/study-assistant/server/options.ts` | Integrated | Frontend | Load subjects/ready files | Supabase |
| `/frontend/features/study-assistant/components/StudyAssistantPanel.tsx` | Integrated | Frontend | Question form, answer UI, transcript | RAG client |
| `/frontend/features/study-assistant/components/StudyAssistantPanel.module.css` | Integrated | Frontend | Panel/transcript styling | Study Assistant panel |
| `/frontend/features/study-assistant/components/ConversationHistoryPanel.tsx` | Integrated | Frontend | Saved history UI | Workspace |
| `/frontend/features/study-assistant/components/ConversationHistoryPanel.module.css` | Integrated | Frontend | History styling | History panel |
| `/frontend/features/study-assistant/components/StudyAssistantWorkspace.tsx` | Integrated | Frontend | History/detail orchestration | Both API clients |
| `/frontend/features/study-assistant/components/StudyAssistantWorkspace.module.css` | Integrated | Frontend | Two-column responsive layout | Workspace |
| `/frontend/types/rag.ts` | Integrated | Frontend | RAG contracts | API/client/UI |
| `/frontend/types/study-conversation.ts` | Integrated | Frontend | Conversation contracts | Conversation API |

---

# Study Assistant Frontend Tests

| Path | Status | Purpose |
|---|---|---|
| `/frontend/features/study-assistant/api.test.ts` | Ready | RAG API tests |
| `/frontend/features/study-assistant/conversations-api.test.ts` | Ready | Conversation API tests |
| `/frontend/features/study-assistant/server/options.test.ts` | Ready | Filter loader tests |
| `/frontend/features/study-assistant/components/StudyAssistantPanel.test.tsx` | Ready | Panel and continuation tests |
| `/frontend/features/study-assistant/components/ConversationHistoryPanel.test.tsx` | Ready | History-state tests |
| `/frontend/features/study-assistant/components/StudyAssistantWorkspace.test.tsx` | Ready | Switching/refresh tests |

---

# Backend Foundation

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/main.py` | Integrated | Member 3 | FastAPI app | Router/config |
| `/backend/app/api/router.py` | Integrated | Member 3 | Main API router | Routes |
| `/backend/app/api/health.py` | Integrated | Member 3 | Health endpoint | FastAPI |
| `/backend/app/core/config.py` | Integrated | Member 3 | Typed settings | Backend |
| `/backend/app/core/security.py` | Integrated | Member 3 | Processor security | Internal endpoints |
| `/backend/app/services/supabase_admin.py` | Integrated | Member 3 | Trusted Supabase operations | Database/Storage |

---

# File Processing Backend

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/services/file_extraction.py` | Integrated | Member 3 | Document extraction | Processor |
| `/backend/app/services/file_processor.py` | Integrated | Member 3 | Processing orchestration | Extraction, AI, Supabase |
| `/backend/app/workers/file_processing_worker.py` | Integrated | Member 3 | Background processing | Queue, processor |
| `/backend/app/api/routes/file_processing.py` | Integrated | Member 3 | Internal processing API | Processor |

---

# AI Provider and Preparation

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/ai/contracts.py` | Integrated | Member 3 | AI provider contracts | AI services |
| `/backend/app/ai/errors.py` | Integrated | Member 3 | AI exceptions | Provider/services |
| `/backend/app/ai/providers/gemini.py` | Integrated | Member 3 | Gemini implementation | Gemini API |
| `/backend/app/ai/chunking.py` | Integrated | Member 3 | Chunk contracts | Chunker |
| `/backend/app/ai/text_chunker.py` | Integrated | Member 3 | Deterministic chunking | Preparer |
| `/backend/app/ai/embedding_batcher.py` | Integrated | Member 3 | Embedding batches | Preparer |
| `/backend/app/ai/preparation.py` | Integrated | Member 3 | Preparation result | File processor |
| `/backend/app/services/study_material_preparer.py` | Integrated | Member 3 | AI preparation | Chunking |
| `/backend/app/services/study_material_embedder.py` | Integrated | Member 3 | Embedding execution | Gemini |
| `/backend/app/services/study_material_vector_indexer.py` | Integrated | Member 3 | Vector persistence orchestration | Supabase |
| `/backend/app/ai/vector_persistence.py` | Integrated | Member 3 | Vector payload validation | Vector indexer |

---

# Retrieval and RAG

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/services/query_embedding.py` | Integrated | Member 3 | Query vectors | Gemini |
| `/backend/app/ai/retrieval_contracts.py` | Integrated | Member 3 | Retrieval contracts | Retrieval |
| `/backend/app/ai/retrieval_persistence.py` | Integrated | Member 3 | Vector RPC access | Supabase |
| `/backend/app/services/retrieval_orchestration.py` | Integrated | Member 3 | Query-to-results flow | Query embedding |
| `/backend/app/services/rag_orchestration.py` | Integrated | Member 3 | Retrieval + answer flow | Grounded generation |
| `/backend/app/api/routes/rag.py` | Integrated | Member 3 | `POST /api/rag/answer` | RAG service |
| `/backend/app/schemas/rag.py` | Integrated | Member 3 | Public RAG contracts | API/frontend |

---

# Phase 5G Backend

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/repositories/study_conversation_repository.py` | Integrated | Member 3 | Conversation persistence | Supabase |
| `/backend/app/schemas/study_conversation.py` | Integrated | Member 3 | Conversation/message contracts | Routes/services |
| `/backend/app/services/study_conversation_errors.py` | Integrated | Member 3 | Controlled errors | Conversation services |
| `/backend/app/services/study_conversation_service.py` | Integrated | Member 3 | Conversation CRUD | Repository |
| `/backend/app/services/study_conversation_memory.py` | Integrated | Member 3 | Bounded memory | Conversation RAG |
| `/backend/app/services/study_conversation_summary.py` | Integrated | Member 3 | Deterministic summaries | Conversation RAG |
| `/backend/app/services/study_conversation_rag.py` | Integrated | Member 3 | Persisted RAG flow | RAG/repository |
| `/backend/app/api/routes/study_conversations.py` | Integrated | Member 3 | Conversation endpoints | Conversation service |
| `/backend/app/api/study_conversation_dependency.py` | Integrated | Member 3 | CRUD dependencies | Repository |
| `/backend/app/api/study_conversation_rag_dependency.py` | Integrated | Member 3 | Conversation RAG dependency | RAG services |

---

# Phase 6A Reviewer Backend

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/ai/reviewer_prompt.py` | Integrated | Member 3 | Builds bounded reviewer-generation prompts | Reviewer generation, Gemini |
| `/backend/app/schemas/reviewer.py` | Integrated | Member 3 | Reviewer API and persistence contracts | Routes, services, repository |
| `/backend/app/repositories/reviewer_repository.py` | Integrated | Member 3 | Reviewer persistence and ownership filtering | Supabase |
| `/backend/app/services/reviewer_errors.py` | Integrated | Member 3 | Controlled reviewer-domain errors | Reviewer services, API |
| `/backend/app/services/reviewer_source_loader.py` | Integrated | Member 3 | Loads ordered source-aware chunks for file/subject scope | Study files, chunks |
| `/backend/app/services/reviewer_generation.py` | Integrated | Member 3 | Structured Gemini reviewer generation and repair | Gemini provider |
| `/backend/app/services/reviewer_service.py` | Integrated | Member 3 | Reviewer save/list/get/delete operations | Reviewer repository |
| `/backend/app/services/reviewer_orchestration.py` | Integrated | Member 3 | Coordinates source loading, generation, and persistence | Reviewer services |
| `/backend/app/api/reviewer_dependency.py` | Integrated | Member 3 | Reviewer persistence dependency | Repository, Supabase client |
| `/backend/app/api/reviewer_orchestration_dependency.py` | Integrated | Member 3 | Reviewer generation dependency assembly | Gemini, source loader, service |
| `/backend/app/api/routes/reviewers.py` | Integrated | Member 3 | Protected reviewer API endpoints | Reviewer orchestration/service |
| `/backend/app/services/supabase_admin.py` | Integrated | Member 3 | Trusted ready-file and source-chunk reads | Reviewer source loader |

---

# Phase 5G Migrations

| Path | Status | Purpose |
|---|---|---|
| `/supabase/migrations/20260806192800_create_study_conversations_and_messages.sql` | Integrated | Conversations/messages |
| `/supabase/migrations/20260806200500_fix_study_message_outcome_constraint.sql` | Integrated | Assistant outcome constraint |
| `/supabase/migrations/20260806223000_add_study_conversation_summary_state.sql` | Integrated | Summary state |
| `/supabase/migrations/20260806234000_restrict_study_conversation_summary_updates.sql` | Integrated | Summary security |

---

# Phase 6A Migration

| Path | Status | Purpose |
|---|---|---|
| `/supabase/migrations/20260807230500_create_reviewers.sql` | Integrated | Retained no-op migration entry matching remote migration history |
| `/supabase/migrations/20260808053929_create_reviewers_foundation.sql` | Integrated | Reviewer table, ownership/scope validation, indexes, triggers, privileges, and RLS |

---

# Phase 6A Reviewer Tests

| Path | Status | Purpose |
|---|---|---|
| `/backend/tests/test_reviewer_migration.py` | Ready | Reviewer migration contract |
| `/backend/tests/test_reviewer_schemas.py` | Ready | Reviewer schema validation |
| `/backend/tests/test_reviewer_repository.py` | Ready | Reviewer persistence behavior |
| `/backend/tests/test_reviewer_service.py` | Ready | Reviewer service behavior |
| `/backend/tests/test_reviewer_source_loader.py` | Ready | File/subject source loading |
| `/backend/tests/test_reviewer_source_admin.py` | Ready | Trusted Supabase source queries |
| `/backend/tests/test_reviewer_prompt.py` | Ready | Prompt construction and limits |
| `/backend/tests/test_reviewer_generation.py` | Ready | Structured AI generation and repair |
| `/backend/tests/test_reviewer_orchestration.py` | Ready | End-to-end reviewer service orchestration |
| `/backend/tests/test_reviewer_api_endpoint.py` | Ready | Authenticated reviewer API contract |

---



# Important Supabase Resources

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

storage bucket: study-materials
```

---

# Environment Variables

## Frontend

```text
NEXT_PUBLIC_SITE_URL
NEXT_PUBLIC_API_BASE_URL
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
```

## Backend

Important private values include:

```text
SUPABASE_URL
SUPABASE_SECRET_KEY
PROCESSOR_INTERNAL_KEY
GEMINI_API_KEY
```

Real private values must never be committed.

---

# Local-Only Files

```text
frontend/.env.local
frontend/.next
frontend/node_modules

backend/.env
backend/.venv
backend/**/__pycache__
backend/.pytest_cache

node_modules
supabase/.temp
```

---

# File Header Rule

Manually created source files must include their filepath when the format supports comments.

TypeScript:

```typescript
// File: /frontend/path/file.ts
```

Python:

```python
# File: /backend/path/file.py
```

CSS:

```css
/* File: /frontend/path/file.css */
```

Markdown:

```markdown
<!-- File: /docs/file.md -->
```

SQL:

```sql
-- File: /supabase/migrations/timestamp_name.sql
```

Strict JSON files are exempt because JSON does not support comments.

---

# Update Rule

Update this map whenever:

- A file is created
- A file is deleted
- A file is renamed
- Ownership changes
- An API changes
- A database migration is added
- A system connection changes
- A development phase becomes implemented