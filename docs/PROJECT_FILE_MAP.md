<!-- File: /docs/PROJECT_FILE_MAP.md -->
<!-- Purpose: Master map of important project files, purposes, owners, statuses, and system connections. -->

**# STS Capstone — STUDY AI Project File Map**

This document is the central reference for important project files.

Update it whenever files, APIs, migrations, owners, or major system connections change.

---

**# Status Definitions**

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

**# Phase Status**

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | Foundation and authentication | Integrated |
| Phase 2 | Learning-profile onboarding | Integrated |
| Phase 3 | Subjects and study-material processing | Integrated |
| Phase 4 | AI provider, preparation, embeddings, vectors, retrieval | Integrated |
| Phase 5A–5F | RAG and Study Assistant | Integrated |
| Phase 5G | Saved conversations, memory, summaries, history UI | Integrated |
| Phase 6A | Reviewer backend foundation | Integrated |
| Phase 6B | Reviewer generation frontend and result display | Integrated |
| Phase 6C | Saved reviewer management and regeneration | Integrated |
| Phase 6D | Large-material multi-pass reviewer generation | Integrated |
| Track A | Flashcard backend, large-material generation, frontend study UI, and saved-deck management | Integrated |
| Track B | Quiz generation, attempts, history, review, and deletion | Integrated |
| Track E | Analytics and Flashcard self-assessment evidence | Ready; shared migration pending coordination |
| Phase 7A–7E | Academic Tasks, output confidence, deterministic priority, frontend, live integration | Integrated |
| Track D | Study plans, scheduling, calendar workspace, Academic Task integration, and regeneration | Integrated |
| Later | Additional Analytics, deployment, and monitoring | Planned |
---

**# Team Ownership**

| Member | Main Responsibility |
|---|---|
| Member 1 | Technical lead, repository, authentication, integration |
| Member 2 | Design system and frontend UI |
| Member 3 | FastAPI, file processing, retrieval, AI |
| Member 4 | Supabase database and security |
| Member 5 | Testing and documentation |

---

**# Root**

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

**# Documentation**

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
| `/docs/AI_REVIEWER_GENERATION.md` | Integrated | Member 3 | Reviewer generation and large-material batching design | Gemini, reviewer services |
| `/docs/AI_QUIZ_GENERATION.md` | Integrated | Member 3 | Quiz generation, answer-key security, attempts, scoring, history, and review | Gemini, Quiz services |
| `/docs/ANALYTICS_DESIGN.md` | Ready | Track E — Analytics | Analytics metrics, canonical sources, Flashcard review evidence, and security | Track E backend, Track A, Track B |
| `/docs/ACADEMIC_TASK_PRIORITY.md` | Integrated | Backend/Documentation | Academic Task deterministic priority design, weights, fallbacks, and API behavior | Academic Task backend and frontend |

---

**# Frontend Foundation**

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

**# Supabase Frontend Clients**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/lib/supabase/config.ts` | Integrated | Member 1 | Safe Supabase config | Browser/server clients |
| `/frontend/lib/supabase/client.ts` | Integrated | Member 1 | Browser client | Client Components |
| `/frontend/lib/supabase/server.ts` | Integrated | Member 1 | Server client | Server Components |
| `/frontend/lib/supabase/proxy.ts` | Integrated | Member 1 | Session refresh and protected-route handling | Protected routes |
| `/frontend/proxy.ts` | Integrated | Member 1 | Root session proxy | Supabase Auth |
| `/frontend/types/database.ts` | Generated | Supabase CLI | Generated schema types | Frontend |

---

**# Authentication**

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

**# Learning Profile**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/features/learning-profile/types.ts` | Integrated | Frontend | Learning-profile and output-confidence types | Onboarding |
| `/frontend/features/learning-profile/validation.ts` | Integrated | Frontend | Learning-profile validation | Mutations |
| `/frontend/features/learning-profile/constants.ts` | Integrated | Frontend | Learning-profile and output-confidence options | Onboarding |
| `/frontend/features/learning-profile/progress.ts` | Integrated | Frontend | Onboarding progress | Protected onboarding |
| `/frontend/features/learning-profile/routing.ts` | Integrated | Frontend | Onboarding routing | Protected pages |
| `/frontend/features/learning-profile/server/queries.ts` | Integrated | Frontend | Load profile and output confidence | Supabase |
| `/frontend/features/learning-profile/server/mutations.ts` | Integrated | Frontend | Save profile and output confidence | Supabase/RPC |
| `/frontend/features/learning-profile/actions/save-subjects.ts` | Integrated | Frontend | Save onboarding subject/profile state | Learning profile |
| `/frontend/features/learning-profile/components/SubjectsForm.tsx` | Integrated | Frontend | Subject and output-confidence controls | Onboarding |
| `/frontend/app/(protected)/onboarding/subjects/page.tsx` | Integrated | Frontend | Subject/confidence onboarding | Learning profile |
| `/frontend/app/(protected)/onboarding/review/page.tsx` | Integrated | Frontend | Onboarding review | Learning profile |
| `/frontend/app/(protected)/profile/page.tsx` | Integrated | Frontend | Profile display | Learning profile |

---

**# Subjects and Files**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/features/subjects/types.ts` | Integrated | Frontend | Subject types | Subject feature |
| `/frontend/features/subjects/queries.ts` | Integrated | Frontend | Load subjects | Supabase |
| `/frontend/features/subjects/actions.ts` | Integrated | Frontend | Subject CRUD | Supabase |
| `/frontend/app/(protected)/subjects/page.tsx` | Integrated | Frontend | Subject management | Subject feature |
| `/frontend/app/(protected)/subjects/[subjectId]/page.tsx` | Integrated | Frontend | Subject workspace | Files |
| `/frontend/features/files/types.ts` | Integrated | Frontend | File types | File feature |
| `/frontend/features/files/constants.ts` | Integrated | Frontend | File limits/statuses | Upload UI |
| `/frontend/features/files/queries.ts` | Integrated | Frontend | Load files | Supabase |
| `/frontend/features/files/actions.ts` | Integrated | Frontend | File operations | Database, Storage |
| `/frontend/features/files/upload.ts` | Integrated | Frontend | TUS upload | Supabase Storage |
| `/frontend/features/files/components/FileUploadManager.tsx` | Integrated | Frontend | File management UI | File actions |
| `/frontend/features/files/components/FilePreviewModal.tsx` | Integrated | Frontend | File preview | Signed URLs |

---

**# Study Assistant Frontend**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/app/(protected)/study-assistant/page.tsx` | Integrated | Frontend | Protected Study Assistant page | Workspace |
| `/frontend/features/study-assistant/api.ts` | Integrated | Frontend | Authenticated RAG client | `/api/rag/answer` |
| `/frontend/features/study-assistant/conversations-api.ts` | Integrated | Frontend | Conversation API client | `/api/study-conversations` |
| `/frontend/features/study-assistant/server/options.ts` | Integrated | Frontend | Subject/ready-file options | Supabase |
| `/frontend/features/study-assistant/components/StudyAssistantPanel.tsx` | Integrated | Frontend | Question/answer UI | RAG |
| `/frontend/features/study-assistant/components/ConversationHistoryPanel.tsx` | Integrated | Frontend | Saved conversation UI | Conversation API |
| `/frontend/features/study-assistant/components/StudyAssistantWorkspace.tsx` | Integrated | Frontend | Assistant/history orchestration | API clients |
| `/frontend/types/rag.ts` | Integrated | Frontend | RAG contracts | API/UI |
| `/frontend/types/study-conversation.ts` | Integrated | Frontend | Conversation contracts | Conversation API |

---

**# Backend Foundation**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/main.py` | Integrated | Backend | FastAPI application | Router/config |
| `/backend/app/api/router.py` | Integrated | Backend | Registers RAG, Reviewer, Flashcard, Quiz, Quiz Attempt, and Academic Task routes | FastAPI |
| `/backend/app/api/health.py` | Integrated | Backend | Health endpoint | FastAPI |
| `/backend/app/core/config.py` | Integrated | Backend | Typed settings | Backend |
| `/backend/app/core/security.py` | Integrated | Backend | Processor security | Internal routes |
| `/backend/app/services/supabase_admin.py` | Integrated | Backend | Trusted Supabase operations | Database/Storage |

---

**# File Processing Backend**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/services/file_extraction.py` | Integrated | Backend | Document extraction | Processor |
| `/backend/app/services/file_processor.py` | Integrated | Backend | Processing orchestration | Extraction, AI, Supabase |
| `/backend/app/workers/file_processing_worker.py` | Integrated | Backend | Background processing | Queue, processor |
| `/backend/app/api/routes/file_processing.py` | Integrated | Backend | Internal processing API | Processor |

---

**# AI Provider, Retrieval, and RAG**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/ai/contracts.py` | Integrated | Backend | AI provider contracts | AI services |
| `/backend/app/ai/errors.py` | Integrated | Backend | AI errors | Providers/services |
| `/backend/app/ai/providers/gemini.py` | Integrated | Backend | Gemini provider | Gemini API |
| `/backend/app/ai/text_chunker.py` | Integrated | Backend | Deterministic text chunking | Preparation |
| `/backend/app/services/study_material_preparer.py` | Integrated | Backend | AI preparation | Chunking |
| `/backend/app/services/study_material_embedder.py` | Integrated | Backend | Embedding execution | Gemini |
| `/backend/app/services/study_material_vector_indexer.py` | Integrated | Backend | Vector persistence | Supabase |
| `/backend/app/services/query_embedding.py` | Integrated | Backend | Query embeddings | Retrieval |
| `/backend/app/services/retrieval_orchestration.py` | Integrated | Backend | Query-to-results flow | Vector search |
| `/backend/app/services/rag_orchestration.py` | Integrated | Backend | Grounded answer flow | Retrieval/Gemini |
| `/backend/app/api/routes/rag.py` | Integrated | Backend | `POST /api/rag/answer` | RAG |

---

**# Reviewer Backend**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/ai/reviewer_prompt.py` | Integrated | Backend | Reviewer prompts | Gemini |
| `/backend/app/schemas/reviewer.py` | Integrated | Backend | Reviewer contracts | Routes/services |
| `/backend/app/repositories/reviewer_repository.py` | Integrated | Backend | Reviewer persistence | Supabase |
| `/backend/app/services/reviewer_source_loader.py` | Integrated | Backend | Ordered source loading | Study files/chunks |
| `/backend/app/services/reviewer_batching.py` | Integrated | Backend | Large-material batching | Reviewer generation |
| `/backend/app/services/reviewer_generation.py` | Integrated | Backend | Structured reviewer generation | Gemini |
| `/backend/app/services/reviewer_service.py` | Integrated | Backend | Reviewer persistence operations | Repository |
| `/backend/app/services/reviewer_orchestration.py` | Integrated | Backend | Reviewer generation orchestration | Reviewer services |
| `/backend/app/api/routes/reviewers.py` | Integrated | Backend | Protected Reviewer API | Reviewer services |

---

**# Track A — Flashcards**

**## Backend**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/ai/flashcard_prompt.py` | Integrated | Backend | Grounded Flashcard prompts | Gemini |
| `/backend/app/schemas/flashcard.py` | Integrated | Backend | Flashcard generation/deck contracts | API/services |
| `/backend/app/schemas/flashcard_summary.py` | Integrated | Backend | Saved deck summary contracts | API |
| `/backend/app/repositories/flashcard_repository.py` | Integrated | Backend | Atomic creation and owner-scoped CRUD | Supabase/RPC |
| `/backend/app/services/flashcard_source_loader.py` | Integrated | Backend | Complete owned source loading | Study files/chunks |
| `/backend/app/services/flashcard_batching.py` | Integrated | Backend | Deterministic source batching | Generation |
| `/backend/app/services/flashcard_generation.py` | Integrated | Backend | Structured Flashcard generation | Gemini |
| `/backend/app/services/flashcard_service.py` | Integrated | Backend | Saved deck operations | Repository |
| `/backend/app/services/flashcard_orchestration.py` | Integrated | Backend | Source, generation, persistence orchestration | Flashcard services |
| `/backend/app/api/routes/flashcards.py` | Integrated | Backend | Protected Flashcard API | FastAPI |

**## Frontend**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/app/(protected)/flashcards/page.tsx` | Integrated | Frontend | Protected Flashcard page | Workspace |
| `/frontend/features/flashcards/types.ts` | Integrated | Frontend | Flashcard contracts | API/UI |
| `/frontend/features/flashcards/api.ts` | Integrated | Frontend | Generate/list/get/delete client | FastAPI |
| `/frontend/features/flashcards/server/options.ts` | Integrated | Frontend | Subject/ready-file options | Supabase |
| `/frontend/features/flashcards/components/FlashcardGenerationForm.tsx` | Integrated | Frontend | Generation controls | API |
| `/frontend/features/flashcards/components/FlashcardStudyViewer.tsx` | Integrated | Frontend | Interactive viewer | Deck |
| `/frontend/features/flashcards/components/SavedFlashcardList.tsx` | Integrated | Frontend | Saved deck list | Workspace |
| `/frontend/features/flashcards/components/FlashcardWorkspace.tsx` | Integrated | Frontend | Flashcard orchestration | API/components |

---

**# Track B — Quizzes**

**## Backend**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/ai/quiz_prompt.py` | Integrated | Backend | Grounded Quiz prompts | Gemini |
| `/backend/app/schemas/quiz.py` | Integrated | Backend | Quiz/attempt/history/review contracts | API/services |
| `/backend/app/repositories/quiz_repository.py` | Integrated | Backend | Quiz persistence and safe reads | Supabase |
| `/backend/app/repositories/quiz_attempt_repository.py` | Integrated | Backend | Attempts, grading, history, review | Supabase/RPC |
| `/backend/app/services/quiz_source_loader.py` | Integrated | Backend | Owned ready source loading | Study files/chunks |
| `/backend/app/services/quiz_generation.py` | Integrated | Backend | Structured Quiz generation | Gemini |
| `/backend/app/services/quiz_service.py` | Integrated | Backend | Quiz CRUD operations | Repository |
| `/backend/app/services/quiz_orchestration.py` | Integrated | Backend | Generation orchestration | Quiz services |
| `/backend/app/services/quiz_attempt_service.py` | Integrated | Backend | Attempts, results, topic analysis, review | Attempt repository |
| `/backend/app/api/routes/quizzes.py` | Integrated | Backend | Generate/list/get/delete Quiz routes | FastAPI |
| `/backend/app/api/routes/quiz_attempts.py` | Integrated | Backend | Attempt/history/submit/result/review routes | FastAPI |

**## Frontend**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/app/(protected)/quizzes/page.tsx` | Integrated | Frontend | Protected Quiz page | Workspace |
| `/frontend/features/quizzes/types.ts` | Integrated | Frontend | Quiz/attempt/history/review contracts | API/UI |
| `/frontend/features/quizzes/api.ts` | Integrated | Frontend | Quiz generation client | FastAPI |
| `/frontend/features/quizzes/attempts-api.ts` | Integrated | Frontend | Quiz attempt client | FastAPI |
| `/frontend/features/quizzes/history-api.ts` | Integrated | Frontend | History/review/delete client | FastAPI |
| `/frontend/features/quizzes/server/options.ts` | Integrated | Frontend | Subject/ready-file options | Supabase |
| `/frontend/features/quizzes/components/QuizGenerationForm.tsx` | Integrated | Frontend | Generation controls | API |
| `/frontend/features/quizzes/components/QuizPlayer.tsx` | Integrated | Frontend | Quiz-taking flow | Attempt API |
| `/frontend/features/quizzes/components/QuizQuestionView.tsx` | Integrated | Frontend | Question/feedback UI | Quiz player |
| `/frontend/features/quizzes/components/QuizResult.tsx` | Integrated | Frontend | Final score/topics | Attempt result |
| `/frontend/features/quizzes/components/QuizHistoryPanel.tsx` | Integrated | Frontend | History/retake/review/delete | History API |
| `/frontend/features/quizzes/components/QuizAttemptReview.tsx` | Integrated | Frontend | Completed-attempt review | Review API |
| `/frontend/features/quizzes/components/QuizWorkspace.tsx` | Integrated | Frontend | Quiz orchestration | Quiz feature |

---

**# Phase 7 — Academic Tasks**

**## Database and Migrations**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/supabase/migrations/20260809054523_create_academic_tasks.sql` | Integrated | Database | Creates student-owned Academic Tasks, constraints, ownership validation, triggers, indexes, privileges, and RLS | Academic Task backend |
| `/supabase/migrations/20260809153000_add_output_confidence_and_task_output_type.sql` | Integrated | Database | Adds academic output-confidence storage and Academic Task `output_type` | Learning profile, priority engine |
| `/frontend/types/database.ts` | Generated | Supabase CLI | Generated database contracts including Track C changes | Frontend |

**## Backend**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/schemas/academic_task.py` | Integrated | Backend | Academic Task CRUD contracts | API/service |
| `/backend/app/schemas/academic_task_priority.py` | Integrated | Backend | Explainable priority response contracts | Priority API |
| `/backend/app/repositories/academic_task_repository.py` | Integrated | Backend | Owner-scoped task persistence | Supabase |
| `/backend/app/repositories/academic_task_priority_context_repository.py` | Integrated | Backend | Loads timezone, output confidence, and study availability | Priority service |
| `/backend/app/services/academic_task_errors.py` | Integrated | Backend | Controlled Academic Task errors | Services/API |
| `/backend/app/services/academic_task_service.py` | Integrated | Backend | Academic Task CRUD orchestration | Repository |
| `/backend/app/services/academic_task_priority.py` | Integrated | Backend | Pure deterministic seven-factor priority engine | Priority service |
| `/backend/app/services/academic_task_priority_context.py` | Integrated | Backend | Resolves output confidence and available study time | Priority service |
| `/backend/app/services/academic_task_priority_service.py` | Integrated | Backend | Combines task and student context into priority evaluations | Priority engine |
| `/backend/app/api/academic_task_dependency.py` | Integrated | Backend | CRUD dependency assembly | FastAPI |
| `/backend/app/api/academic_task_priority_dependency.py` | Integrated | Backend | Priority dependency assembly | FastAPI |
| `/backend/app/api/routes/academic_tasks.py` | Integrated | Backend | Protected CRUD, status, and prioritized routes | Academic Task services |

**## Frontend**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/app/(protected)/academic-tasks/page.tsx` | Integrated | Frontend | Protected Academic Tasks page | Workspace |
| `/frontend/features/academic-tasks/types.ts` | Integrated | Frontend | CRUD and priority contracts | API/UI |
| `/frontend/features/academic-tasks/api.ts` | Integrated | Frontend | Authenticated CRUD and prioritized API client | FastAPI |
| `/frontend/features/academic-tasks/validation.ts` | Integrated | Frontend | Create/edit form validation | Workspace |
| `/frontend/features/academic-tasks/form.ts` | Integrated | Frontend | Persisted task to form mapping | Workspace |
| `/frontend/features/academic-tasks/priority-presentation.ts` | Integrated | Frontend | Score and urgency presentation | Workspace |
| `/frontend/features/academic-tasks/components/AcademicTaskPriorityBreakdown.tsx` | Integrated | Frontend | Expandable seven-factor `Why this priority?` explanation | Priority response |
| `/frontend/features/academic-tasks/components/AcademicTasksWorkspace.tsx` | Integrated | Frontend | CRUD, status, priority display, refresh, and independent-column layout | Academic Task API |
| `/frontend/features/academic-tasks/components/AcademicTasksWorkspace.module.css` | Integrated | Frontend | Responsive independent-column task-card layout | Workspace |
| `/frontend/features/navigation/components/ProtectedAppShell.tsx` | Integrated | Frontend | Protected navigation including Flashcards, Quizzes, and Academic Tasks | Protected pages |

**## Backend Tests**

| Path | Status | Purpose |
|---|---|---|
| `/backend/tests/test_academic_task_api_endpoint.py` | Ready | Academic Task API |
| `/backend/tests/test_academic_task_priority.py` | Ready | Deterministic priority engine |
| `/backend/tests/test_academic_task_priority_context.py` | Ready | Output confidence and availability |
| `/backend/tests/test_academic_task_priority_context_repository.py` | Ready | Priority context persistence |
| `/backend/tests/test_academic_task_priority_schemas.py` | Ready | Priority contracts |
| `/backend/tests/test_academic_task_priority_service.py` | Ready | Priority orchestration |
| `/backend/tests/test_academic_task_repository.py` | Ready | Task persistence |
| `/backend/tests/test_academic_task_schemas.py` | Ready | Task CRUD schemas |
| `/backend/tests/test_academic_task_service.py` | Ready | Task CRUD service |

**## Frontend Tests**

| Path | Status | Purpose |
|---|---|---|
| `/frontend/features/academic-tasks/api.test.ts` | Ready | Academic Task API client |
| `/frontend/features/academic-tasks/validation.test.ts` | Ready | Task-form validation |
| `/frontend/features/academic-tasks/form.test.ts` | Ready | Persisted-task form mapping |
| `/frontend/features/academic-tasks/priority-presentation.test.ts` | Ready | Priority presentation |
| `/frontend/features/academic-tasks/components/AcademicTaskPriorityBreakdown.test.tsx` | Ready | Priority explanation |
| `/frontend/features/academic-tasks/components/AcademicTasksWorkspace.test.tsx` | Ready | Workspace loading, creation, priority display |
| `/frontend/features/academic-tasks/components/AcademicTasksWorkspace.mutations.test.tsx` | Ready | Edit, status, delete, priority refresh |

---
**# Track D — Study Plans and Scheduling**

**## Database and Migrations**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/supabase/migrations/20260810002500_create_study_plans_foundation.sql` | Ready | Database | Creates owned study plans and study sessions with validation and RLS | Study Plan backend |
| `/supabase/migrations/20260811002500_add_study_plan_regeneration_rpc.sql` | Ready | Database | Adds transactional generated-session replacement | Regeneration backend |

The Track D migration files are committed but shared database application is coordinated separately.

**## Study Plan Backend**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/backend/app/schemas/study_plan.py` | Integrated | Backend | Study-plan and study-session contracts | Repository, service, API |
| `/backend/app/schemas/study_scheduler.py` | Integrated | Backend | Deterministic scheduler input/output and blocked-window contracts | Scheduler |
| `/backend/app/schemas/study_plan_generation_api.py` | Integrated | Backend | Generation and regeneration API contracts | Generation routes |
| `/backend/app/schemas/generated_study_plan_regeneration.py` | Integrated | Backend | Transactional regeneration persistence contract | Regeneration service |
| `/backend/app/repositories/study_plan_repository.py` | Integrated | Backend | Owned plan/session persistence and manual-session loading | Supabase |
| `/backend/app/repositories/generated_study_plan_regeneration_repository.py` | Integrated | Backend | Calls trusted generated-session replacement RPC | Supabase RPC |
| `/backend/app/services/study_plan_service.py` | Integrated | Backend | Study-plan and manual-session orchestration | Repository, API |
| `/backend/app/services/study_scheduler.py` | Integrated | Backend | Pure deterministic scheduling engine | Generation |
| `/backend/app/services/study_schedule_generation_service.py` | Integrated | Backend | Loads scheduling context and produces schedules | Scheduler |
| `/backend/app/services/generated_study_plan_regeneration_service.py` | Integrated | Backend | Validates and persists regenerated schedules | Regeneration repository |
| `/backend/app/services/study_plan_regeneration_orchestrator.py` | Integrated | Backend | Coordinates latest tasks, blocked manual sessions, scheduling, and replacement | Generation and persistence |
| `/backend/app/api/study_plan_dependency.py` | Integrated | Backend | Study Plan dependency assembly | FastAPI |
| `/backend/app/api/study_plan_generation_dependency.py` | Integrated | Backend | Generation/regeneration dependency assembly | FastAPI |
| `/backend/app/api/routes/study_plans.py` | Integrated | Backend | Protected plan/session CRUD routes | Study Plan services |
| `/backend/app/api/routes/study_plan_generation.py` | Integrated | Backend | Protected generation and regeneration routes | Generation services |
| `/backend/app/api/router.py` | Integrated | Backend | Registers Study Plan routes in the shared API | FastAPI application |

**## Study Plan Frontend**

| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/app/(protected)/study-plan/page.tsx` | Integrated | Frontend | Protected Study Plan route | Study Plans workspace |
| `/frontend/features/study-plans/types.ts` | Integrated | Frontend | Study Plan, session, scheduler, generation, and regeneration contracts | API/UI |
| `/frontend/features/study-plans/api.ts` | Integrated | Frontend | Authenticated Study Plan API client | FastAPI |
| `/frontend/features/study-plans/academic-task-adapter.ts` | Integrated | Frontend | Converts prioritized Academic Tasks into scheduler tasks | Track C Academic Tasks |
| `/frontend/features/study-plans/components/StudyPlansWorkspace.tsx` | Integrated | Frontend | Saved plans, calendar, manual controls, generation, and regeneration | Study Plan APIs |
| `/frontend/features/study-plans/components/GenerateStudyPlanModal.tsx` | Integrated | Frontend | Generated-plan creation workflow | Generation API |
| `/frontend/features/study-plans/components/RegenerateStudyPlanModal.tsx` | Integrated | Frontend | Generated-plan refresh and unscheduled-work feedback | Regeneration API |
| `/frontend/features/navigation/components/ProtectedAppShell.tsx` | Integrated | Frontend | Adds Study Plan to protected navigation | `/study-plan` |

**## Study Plan Tests**

| Path | Status | Purpose |
|---|---|---|
| `/backend/tests/test_study_plan_api_endpoint.py` | Ready | Study Plan CRUD API behavior |
| `/backend/tests/test_study_plan_generation_api_endpoint.py` | Ready | Generation and regeneration API behavior |
| `/backend/tests/test_study_scheduler_blocked_time.py` | Ready | Manual blocked windows and future-only scheduling |
| `/backend/tests/test_study_plan_regeneration_orchestrator.py` | Ready | Generated-plan regeneration orchestration |
| `/backend/tests/test_generated_study_plan_regeneration_repository.py` | Ready | Trusted replacement RPC repository behavior |
| `/backend/tests/test_generated_study_plan_regeneration_service.py` | Ready | Regeneration persistence validation |
| `/backend/tests/test_study_plan_regeneration_migration.py` | Ready | Regeneration migration contract |
| `/frontend/features/study-plans/api.test.ts` | Ready | Authenticated Study Plan API client |
| `/frontend/features/study-plans/academic-task-adapter.test.ts` | Ready | Academic Task scheduling adapter |
| `/frontend/features/study-plans/components/GenerateStudyPlanModal.test.tsx` | Ready | Study-plan generation UI |
| `/frontend/features/study-plans/components/RegenerateStudyPlanModal.test.tsx` | Ready | Regeneration UI |
| `/frontend/features/study-plans/components/StudyPlansWorkspace.test.tsx` | Ready | Calendar, plan switching, generation, and regeneration integration |

---

**# Migrations**

**## Phase 5G**

| Path | Status | Purpose |
|---|---|---|
| `/supabase/migrations/20260806192800_create_study_conversations_and_messages.sql` | Integrated | Conversations/messages |
| `/supabase/migrations/20260806200500_fix_study_message_outcome_constraint.sql` | Integrated | Assistant outcome constraint |
| `/supabase/migrations/20260806223000_add_study_conversation_summary_state.sql` | Integrated | Summary state |
| `/supabase/migrations/20260806234000_restrict_study_conversation_summary_updates.sql` | Integrated | Summary security |

**## Phase 6A**

| Path | Status | Purpose |
|---|---|---|
| `/supabase/migrations/20260807230500_create_reviewers.sql` | Integrated | Retained migration-history entry |
| `/supabase/migrations/20260808053929_create_reviewers_foundation.sql` | Integrated | Reviewer persistence and RLS foundation |

**## Track A**

| Path | Status | Purpose |
|---|---|---|
| `/supabase/migrations/20260809142000_create_flashcard_foundation.sql` | Integrated | Flashcard deck/card foundation |
| `/supabase/migrations/20260809145600_create_flashcard_persistence_rpc.sql` | Integrated | Atomic Flashcard persistence RPC |

**## Track B**

| Path | Status | Purpose |
|---|---|---|
| `/supabase/migrations/20260809204500_create_quizzes_foundation.sql` | Integrated | Quiz metadata and private questions |
| `/supabase/migrations/20260809211600_create_quiz_persistence_rpc.sql` | Integrated | Atomic Quiz persistence |
| `/supabase/migrations/20260809223500_create_quiz_attempt_foundation.sql` | Integrated | Quiz attempts and answer history |
| `/supabase/migrations/20260809225500_create_quiz_attempt_rpcs.sql` | Integrated | Attempt start and answer grading |

**## Phase 7**

| Path | Status | Purpose |
|---|---|---|
| `/supabase/migrations/20260809054523_create_academic_tasks.sql` | Integrated | Academic Task foundation |
| `/supabase/migrations/20260809153000_add_output_confidence_and_task_output_type.sql` | Integrated | Output confidence and task output type |

---

**## Phase 6 Track E — Analytics**

| File | Status | Purpose | Owner | Connections |
|---|---|---|---|---|
| `backend/app/api/analytics_dependency.py` | Ready | Constructs the Analytics service and repository dependency graph. | Track E — Analytics | Supabase client, Analytics repository, Analytics service |
| `backend/app/api/routes/analytics.py` | Ready | Exposes `GET /api/analytics/overview`. | Track E — Analytics | Authentication dependency, Analytics service |
| `backend/app/repositories/analytics_repository.py` | Ready | Reads owner-scoped subject, study-material, completed Quiz, Quiz-answer, and Flashcard-review evidence. | Track E — Analytics | `subjects`, `study_files`, `quiz_attempts`, `quiz_attempt_answers`, `flashcard_review_events` |
| `backend/app/schemas/analytics.py` | Ready | Defines Analytics response contracts, periods, metric availability, and topic-performance records. | Track E — Analytics | Analytics route and service |
| `backend/app/services/analytics_errors.py` | Ready | Defines controlled Analytics feature errors. | Track E — Analytics | Analytics repository and route |
| `backend/app/services/analytics_service.py` | Ready | Aggregates current inventory, weighted Quiz accuracy, Quiz topic performance, and Flashcard self-assessment performance. | Track E — Analytics | Analytics repository, Track A Flashcards, Track B Quiz evidence |
| `backend/app/schemas/flashcard_review.py` | Ready | Defines Flashcard self-assessment review request, outcome, and response contracts. | Track E — Analytics | Flashcard review API and persistence |
| `backend/app/repositories/flashcard_review_repository.py` | Ready | Validates owned Flashcard review targets and persists durable review events. | Track E — Analytics | `flashcard_decks`, `flashcards`, `flashcard_review_events` |
| `backend/app/services/flashcard_review_errors.py` | Ready | Defines controlled Flashcard-review errors. | Track E — Analytics | Flashcard review repository and API |
| `backend/app/services/flashcard_review_service.py` | Ready | Coordinates Flashcard self-assessment persistence. | Track E — Analytics | Flashcard review repository |
| `backend/app/api/flashcard_review_dependency.py` | Ready | Constructs the Flashcard-review repository/service dependency graph. | Track E — Analytics | Supabase client, review repository, review service |
| `backend/app/api/routes/flashcard_reviews.py` | Ready | Exposes the protected Flashcard self-assessment review endpoint. | Track E — Analytics | Authentication, review service |
| `frontend/features/flashcards/types.ts` | Ready | Includes Flashcard review request/response and outcome contracts used by the frontend. | Track A + Track E integration | Flashcard frontend API |
| `frontend/features/flashcards/api.ts` | Ready | Sends authenticated Flashcard review events in addition to existing Flashcard requests. | Track A + Track E integration | Protected Flashcard API |
| `frontend/features/flashcards/components/FlashcardStudyViewer.tsx` | Ready | Lets the student persist `I Know This` or `Review Again` after revealing an answer. | Track A + Track E integration | Flashcard review API |
| `backend/tests/test_analytics_api_endpoint.py` | Ready | Tests Analytics authentication, reporting periods, responses, and controlled failures. | Track E — Analytics | Analytics API |
| `backend/tests/test_analytics_repository.py` | Ready | Tests owner-scoped canonical Analytics reads including Quiz and Flashcard-review evidence. | Track E — Analytics | Analytics repository |
| `backend/tests/test_analytics_router_registration.py` | Ready | Protects Analytics router registration. | Track E — Analytics | FastAPI application router |
| `backend/tests/test_analytics_service.py` | Ready | Tests Quiz/Flashcard aggregation, periods, topic classification, empty evidence, and owner scope. | Track E — Analytics | Analytics service |
| `backend/tests/test_flashcard_review_api_endpoint.py` | Ready | Tests Flashcard-review authentication, valid writes, and request validation. | Track E — Analytics | Flashcard review API |
| `backend/tests/test_flashcard_review_migration.py` | Ready | Protects the Flashcard review-event migration security foundation. | Track E — Analytics | Supabase migration |
| `backend/tests/test_flashcard_review_repository.py` | Ready | Tests owner/card validation and review persistence. | Track E — Analytics | Flashcard review repository |
| `backend/tests/test_flashcard_review_router_registration.py` | Ready | Protects Flashcard-review route registration. | Track E — Analytics | FastAPI application router |
| `backend/tests/test_flashcard_review_service.py` | Ready | Tests Flashcard-review service delegation. | Track E — Analytics | Flashcard review service |
| `frontend/features/flashcards/api.test.ts` | Ready | Tests authenticated Flashcard review requests and response validation alongside existing Flashcard API behavior. | Track A + Track E integration | Frontend Flashcard API |
| `frontend/features/flashcards/components/FlashcardStudyViewer.test.tsx` | Ready | Tests review controls, known/review-again persistence, failures, and navigation behavior. | Track A + Track E integration | Flashcard study viewer |
| `supabase/migrations/20260811162000_create_flashcard_review_events.sql` | Ready; remote pending | Adds durable owner-scoped Flashcard self-assessment evidence for Analytics. | Track E — Analytics | `flashcard_decks`, `flashcards`, RLS |
| `docs/ANALYTICS_DESIGN.md` | Ready | Documents Track E architecture, canonical metrics, security, validation, and remaining unavailable metrics. | Track E — Analytics | Phase 6 implementation |

Track E's currently implemented metrics remain based on canonical Quiz and Flashcard evidence.

The Track E migration remains intentionally unapplied to the shared remote database until linked migration history is re-inspected after this C/D synchronization merge.


**# Important Supabase Resources**

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
public.flashcard_review_events

public.quizzes
public.quiz_questions
public.quiz_attempts
public.quiz_attempt_answers

public.academic_tasks
public.study_plans
public.study_sessions

storage bucket: study-materials
```

---

**# Environment Variables**

**## Frontend**

```text
NEXT_PUBLIC_SITE_URL
NEXT_PUBLIC_API_BASE_URL
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
```

**## Backend**

```text
SUPABASE_URL
SUPABASE_SECRET_KEY
PROCESSOR_INTERNAL_KEY
GEMINI_API_KEY
```

Real private values must never be committed.

---

**# Local-Only Files**

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

**# File Header Rule**

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

Strict JSON files are exempt.

---

**# Update Rule**

Update this map whenever:

- A file is created
- A file is deleted
- A file is renamed
- Ownership changes
- An API changes
- A database migration is added
- A system connection changes
- A development phase becomes implemented