<!-- File: /docs/PROJECT_FILE_MAP.md -->
<!-- Purpose: Provides the master list of important project files, owners, purposes, statuses, and system connections. -->

# STS Capstone Project File Map

This document is the central reference for the files and folders used in the STS Capstone Project.

Update this document whenever:

1. A new important file is created.
2. A file is renamed, moved, or removed.
3. A file begins using another service or module.
4. File ownership changes.
5. An API, database table, shared type, or environment variable changes.
6. A planned file becomes implemented.
7. A new migration or database function is introduced.
8. A new background worker or processing service is introduced.

---

# File Status

| Status | Meaning |
|---|---|
| Planned | Expected in a future phase but not created |
| Created | Exists but may not be independently tested |
| In Progress | Currently being developed |
| Ready | Works independently and passed direct checks |
| Integrated | Works with the rest of the application |
| Generated | Automatically created by a framework or tool |
| Local Only | Exists only on the developer's computer and must not be committed |
| Deprecated | Removed, replaced, or no longer used |

---

# Phase Status

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | Project foundation, Next.js, Mantine, FastAPI health API, Supabase foundation, and authentication foundation | Integrated |
| Phase 2 | Registration, login, protected routes, profile, learning-profile onboarding, and availability | Integrated |
| Phase 3 | Subjects, private file uploads, processing queue, document extraction, automatic worker, live status refresh, and recovery | Integrated |
| Phase 4 | Embeddings, retrieval, RAG, AI questions, and generated study materials | Planned |
| Later phases | Reviewers, flashcards, quizzes, study plans, analytics, and deployment | Planned |

---

# Team Ownership

| Member | Main Responsibility |
|---|---|
| Member 1 | Technical lead, repository, authentication, integration, and deployment |
| Member 2 | Design system, application shell, dashboard, and shared UI |
| Member 3 | FastAPI backend, file processing, retrieval, and AI services |
| Member 4 | Supabase database, security, reviewers, and quizzes |
| Member 5 | Testing, documentation, tasks, study plans, and calendar |

Ownership identifies the primary maintainer. Shared files may require review from multiple members.

---

# Root Files and Folders

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/.gitignore` | Integrated | Member 1 | Excludes secrets, dependencies, build output, caches, virtual environments, and Supabase temporary files | Entire repository |
| `/README.md` | Integrated | Member 1 | Provides the project overview and documentation links | `/docs/`, `/frontend/`, `/backend/`, `/supabase/` |
| `/package.json` | Ready | Member 1 | Defines repository-level tools such as the Supabase CLI | Root npm tooling |
| `/package-lock.json` | Ready | Member 1 | Locks repository-level npm dependencies | Root `package.json` |
| `/node_modules/` | Local Only | Each member | Stores root development dependencies | Recreated with `npm install` |
| `/frontend/` | Integrated | Members 1 and 2 | Contains the Next.js and Mantine frontend | Browser, Supabase, FastAPI |
| `/backend/` | Integrated | Member 3 | Contains FastAPI, extraction services, and processing worker | Supabase, Storage, future Gemini |
| `/supabase/` | Integrated | Member 4 | Contains CLI configuration and database migrations | Hosted Supabase project |
| `/docs/` | Integrated | Members 1 and 5 | Contains shared technical documentation | Entire repository |

---

# Documentation Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/docs/PROJECT_FILE_MAP.md` | Integrated | Member 1 | Master reference for files, owners, purposes, statuses, and connections | Entire repository |
| `/docs/ARCHITECTURE.md` | Integrated | Member 1 | Documents implemented and planned system architecture using Mermaid | Frontend, backend, Supabase, worker, future AI |
| `/docs/setup-guide.md` | Integrated | Member 5 | Explains installation, environment setup, validation, API startup, and worker startup | Entire development workflow |
| `/docs/api-contracts.md` | Integrated | Member 3 | Documents health, internal processing, worker, and database RPC contracts | FastAPI, Supabase, frontend |
| `/docs/database.md` | Integrated | Member 4 | Documents implemented tables, Storage, RLS, triggers, statuses, and RPCs | Supabase and processing services |
| `/docs/authentication.md` | Integrated | Member 5 | Documents registration, login, sessions, protected routes, and authentication security | Supabase Auth and frontend |
| `/docs/git-workflow.md` | Integrated | Member 1 | Documents branches, commits, pull requests, merges, and reviews | GitHub repository |
| `/docs/testing-checklist.md` | Integrated | Member 5 | Tracks automated, manual, security, and regression tests | Entire application |

---

# Frontend Foundation and Configuration

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/package.json` | Integrated | Member 1 | Defines frontend dependencies and scripts | npm and Next.js |
| `/frontend/package-lock.json` | Integrated | Member 1 | Locks exact frontend dependencies | `package.json` |
| `/frontend/tsconfig.json` | Integrated | Member 1 | Configures TypeScript and the `@/*` alias | All TypeScript files |
| `/frontend/eslint.config.mjs` | Integrated | Member 1 | Configures ESLint | `npm run lint` |
| `/frontend/next-env.d.ts` | Generated | Next.js | Provides Next.js TypeScript declarations | TypeScript compiler |
| `/frontend/next.config.ts` | Integrated | Member 1 | Configures Next.js | Development server and build |
| `/frontend/postcss.config.cjs` | Integrated | Member 2 | Enables Mantine-compatible PostCSS processing | CSS and CSS Modules |
| `/frontend/.env.example` | Ready | Member 1 | Documents browser-safe environment variables | `.env.local`, Supabase, FastAPI |
| `/frontend/.env.local` | Local Only | Each member | Stores local public configuration | Next.js runtime |
| `/frontend/.gitignore` | Integrated | Member 1 | Excludes frontend environment and generated files | Frontend workspace |
| `/frontend/node_modules/` | Local Only | Each member | Stores frontend dependencies | Recreated with `npm install` |
| `/frontend/.next/` | Local Only | Next.js | Stores development and production build output | Recreated automatically |
| `/frontend/tsconfig.tsbuildinfo` | Local Only | TypeScript | Stores incremental compiler data | Recreated automatically |
| `/frontend/public/` | Integrated | Member 2 | Stores public static assets | Frontend pages |
| `/frontend/favicon.ico` | Generated | Next.js | Provides the browser icon when present | Application metadata |

---

# Frontend Application and Design-System Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/app/layout.tsx` | Integrated | Member 1 | Loads global styles, metadata, fonts, color scheme, and providers | All frontend routes |
| `/frontend/app/providers.tsx` | Integrated | Member 2 | Provides Mantine theme, modals, and notifications | Root layout |
| `/frontend/app/globals.css` | Integrated | Member 2 | Defines global variables and browser defaults | Root layout |
| `/frontend/app/page.tsx` | Integrated | Member 2 | Provides the application entry or foundation page | Shared UI components |
| `/frontend/theme/colors.ts` | Integrated | Member 2 | Defines application color tokens | Mantine theme |
| `/frontend/theme/components.ts` | Integrated | Member 2 | Defines shared Mantine component defaults | Mantine theme |
| `/frontend/theme/theme.ts` | Integrated | Member 2 | Combines colors, typography, spacing, radii, and component defaults | `providers.tsx` |
| `/frontend/components/foundation/MantineFoundationCheck.tsx` | Integrated | Member 2 | Provides design-system validation controls | Mantine, health check |
| `/frontend/components/foundation/MantineFoundationCheck.module.css` | Integrated | Member 2 | Styles the foundation component | `MantineFoundationCheck.tsx` |
| `/frontend/components/foundation/BackendHealthCheck.tsx` | Integrated | Member 1 | Displays health connection, loading, error, and retry states | Frontend API service |
| `/frontend/components/foundation/BackendHealthCheck.module.css` | Integrated | Member 2 | Styles the backend-health interface | `BackendHealthCheck.tsx` |

---

# Frontend FastAPI Integration Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/types/api.ts` | Integrated | Member 1 | Defines typed FastAPI health responses | API service and health component |
| `/frontend/services/api.ts` | Integrated | Member 1 | Builds URLs, validates health responses, applies timeouts, and handles request failures | FastAPI `/api/health` |
| `/frontend/components/foundation/BackendHealthCheck.tsx` | Integrated | Member 1 | Consumes the health API service | `services/api.ts` |

---

# Supabase Frontend Client Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/lib/supabase/config.ts` | Integrated | Member 1 | Validates browser-safe Supabase configuration | Browser and server clients |
| `/frontend/lib/supabase/client.ts` | Integrated | Member 1 | Creates the browser Supabase client | Client Components |
| `/frontend/lib/supabase/server.ts` | Integrated | Member 1 | Creates the cookie-aware server Supabase client | Server Components and Actions |
| `/frontend/lib/supabase/proxy.ts` | Integrated | Member 1 | Refreshes authentication sessions and synchronizes cookies | Root proxy and Supabase Auth |
| `/frontend/proxy.ts` | Integrated | Member 1 | Runs session refresh for matched requests | `lib/supabase/proxy.ts` |
| `/frontend/types/database.ts` | Generated | Supabase CLI | Contains generated TypeScript definitions for the hosted public schema | All typed Supabase clients and features |

`frontend/types/database.ts` must be regenerated after approved schema changes and must not be edited manually.

---

# Authentication Feature Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/features/auth/types.ts` | Integrated | Member 1 | Defines authentication action and form types | Auth validation and components |
| `/frontend/features/auth/validation.ts` | Integrated | Member 1 | Validates registration and login inputs | Auth Server Actions |
| `/frontend/features/auth/actions/register.ts` | Integrated | Member 1 | Creates Supabase Auth users and redirects to confirmation flow | Supabase Auth |
| `/frontend/features/auth/components/RegisterForm.tsx` | Integrated | Member 1 | Displays and submits the registration form | Registration action |
| `/frontend/features/auth/components/LoginForm.tsx` | Integrated | Member 1 | Displays and submits the login form | Supabase Auth |
| `/frontend/app/(auth)/layout.tsx` | Integrated | Member 2 | Provides the public authentication layout | Registration and login pages |
| `/frontend/app/(auth)/register/page.tsx` | Integrated | Member 1 | Displays student registration | Register form |
| `/frontend/app/(auth)/register/check-email/page.tsx` | Integrated | Member 1 | Displays registration confirmation instructions | Supabase email confirmation |
| `/frontend/app/(auth)/login/page.tsx` | Integrated | Member 1 | Displays student login | Login form |
| `/frontend/app/auth/confirm/route.ts` | Integrated | Member 1 | Exchanges the email-confirmation code and creates a session | Supabase Auth |
| `/frontend/app/(protected)/dashboard/page.tsx` | Integrated | Members 1 and 2 | Provides the protected dashboard | Auth guards and onboarding state |

Authentication filenames may differ slightly when actions are split into separate modules. The feature directory remains the source of truth.

---

# Phase 2 Learning-Profile Feature Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/features/learning-profile/constants.ts` | Integrated | Member 2 | Defines questionnaire options and onboarding steps | Validation and forms |
| `/frontend/features/learning-profile/types.ts` | Integrated | Member 2 | Defines learning-profile inputs and snapshots | Queries, mutations, forms |
| `/frontend/features/learning-profile/validation.ts` | Integrated | Member 2 | Validates profile, preference, subject, and availability inputs | Server mutations |
| `/frontend/features/learning-profile/progress.ts` | Integrated | Member 2 | Calculates onboarding progress | Onboarding shell |
| `/frontend/features/learning-profile/routing.ts` | Integrated | Member 2 | Maps onboarding steps to routes | Onboarding entry |
| `/frontend/features/learning-profile/display.ts` | Integrated | Member 2 | Formats stored learning-profile values | Dashboard and profile |
| `/frontend/features/learning-profile/server/auth.ts` | Integrated | Member 2 | Retrieves the authenticated user ID | Queries and mutations |
| `/frontend/features/learning-profile/server/queries.ts` | Integrated | Member 2 | Loads the complete onboarding snapshot | Onboarding, dashboard, profile |
| `/frontend/features/learning-profile/server/mutations.ts` | Integrated | Member 2 | Saves profile sections and calls onboarding RPCs | Supabase |
| `/frontend/features/learning-profile/server/guards.ts` | Integrated | Member 2 | Protects pages requiring completed onboarding | Dashboard and profile |
| `/frontend/app/(protected)/onboarding/` | Integrated | Member 2 | Contains the six-step onboarding flow | Learning-profile feature |
| `/frontend/app/(protected)/profile/page.tsx` | Integrated | Member 2 | Displays the completed learning profile | Queries and onboarding routes |

---

# Phase 3 Subject Feature Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/features/subjects/types.ts` | Integrated | Members 1 and 2 | Defines subject summaries and input types | Queries, actions, components |
| `/frontend/features/subjects/queries.ts` | Integrated | Members 1 and 2 | Loads authenticated student subjects | Supabase `subjects` table |
| `/frontend/features/subjects/actions.ts` | Integrated | Members 1 and 2 | Creates, updates, and deletes owned subjects | Supabase and RLS |
| `/frontend/features/subjects/components/SubjectTabs.tsx` | Integrated | Member 2 | Displays navigation tabs for student subjects | Subject workspace routes |
| `/frontend/features/subjects/components/` | Integrated | Member 2 | Contains subject forms, cards, dialogs, and shared UI | Subject actions and queries |
| `/frontend/app/(protected)/subjects/page.tsx` | Integrated | Members 1 and 2 | Displays subject management and empty states | Subject actions and queries |
| `/frontend/app/(protected)/subjects/[subjectId]/page.tsx` | Integrated | Members 1 and 2 | Displays one subject workspace and its uploaded materials | Subject and file queries |
| `/frontend/app/(protected)/files/page.tsx` | Integrated | Member 1 | Redirects legacy file navigation to the subject workspace | `/subjects` |
| `/frontend/components/` | Integrated | Member 2 | Contains the protected application shell and shared navigation when present | Dashboard and subjects |

---

# Phase 3 File Feature Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/features/files/types.ts` | Integrated | Members 1 and 3 | Defines study-file summaries and action results | File actions and UI |
| `/frontend/features/files/constants.ts` | Integrated | Members 1 and 3 | Defines MIME types, upload limits, and processing-status metadata | Dropzone and status badges |
| `/frontend/features/files/queries.ts` | Integrated | Members 1 and 3 | Loads authenticated study-file records | Supabase `study_files` |
| `/frontend/features/files/actions.ts` | Integrated | Members 1 and 3 | Reserves, completes, fails, retries, signs, and deletes files | Supabase database and Storage |
| `/frontend/features/files/upload.ts` | Integrated | Member 3 | Uploads private files through Supabase TUS | Private `study-materials` bucket |
| `/frontend/features/files/components/FileUploadManager.tsx` | Integrated | Members 2 and 3 | Provides upload, progress, retry, preview, download, delete, status display, and polling | File actions, queries, Storage |
| `/frontend/features/files/components/FileUploadManager.module.css` | Integrated | Member 2 | Styles the file-management interface | `FileUploadManager.tsx` |
| `/frontend/features/files/components/FilePreviewModal.tsx` | Integrated | Member 2 | Displays supported file previews through signed URLs | File access action |
| `/frontend/features/files/components/` | Integrated | Members 2 and 3 | Contains file-management UI components | File actions and types |

`FileUploadManager.tsx` currently owns active local polling for its live file state. The separate `FileStatusAutoRefresh.tsx` component may remain available for other pages but is not required on the subject workspace when manager-level polling is active.

---

# Backend Dependency and Environment Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/backend/README.md` | Ready | Member 3 | Documents backend responsibilities | Backend source |
| `/backend/requirements.in` | Integrated | Member 3 | Lists intentional direct Python dependencies | FastAPI, extraction, tests |
| `/backend/requirements.txt` | Integrated | Member 3 | Locks the tested Python environment | `.venv` |
| `/backend/.venv/` | Local Only | Each member | Contains the local Python environment | Recreated using `requirements.txt` |
| `/backend/.env.example` | Integrated | Member 3 | Documents safe backend environment-variable names | `config.py` |
| `/backend/.env` | Local Only | Each member | Stores private credentials and configuration | Backend runtime |
| `/backend/app/core/config.py` | Integrated | Member 3 | Loads typed backend settings | FastAPI, Supabase admin, worker |
| `/backend/app/core/security.py` | Integrated | Member 3 | Validates the internal processor key using secure comparison | Internal processing endpoints |

Private values stored in `backend/.env` include the Supabase secret and processor internal key. They must not be committed or exposed to the frontend.

---

# Backend Application Package Structure

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/backend/app/__init__.py` | Ready | Member 3 | Marks the backend application as a Python package | Backend imports |
| `/backend/app/main.py` | Integrated | Member 3 | Creates FastAPI, CORS, and the main router | Config and API router |
| `/backend/app/api/__init__.py` | Ready | Member 3 | Marks the API folder as a Python package | API imports |
| `/backend/app/api/router.py` | Integrated | Member 3 | Combines health and processing routers | FastAPI application |
| `/backend/app/api/health.py` | Integrated | Member 3 | Provides `GET /api/health` | Health schema and config |
| `/backend/app/api/routes/__init__.py` | Ready | Member 3 | Marks route modules as a package | API router |
| `/backend/app/api/routes/file_processing.py` | Integrated | Member 3 | Provides protected source-validation and processing endpoints | Security and processor service |
| `/backend/app/core/__init__.py` | Ready | Member 3 | Marks core utilities as a package | Config and security |
| `/backend/app/schemas/__init__.py` | Ready | Member 3 | Marks schemas as a package | Pydantic models |
| `/backend/app/schemas/health.py` | Integrated | Member 3 | Defines the health response schema | Health endpoint |
| `/backend/app/schemas/file_processing.py` | Integrated | Member 3 | Defines source-validation and processing response schemas | Processing endpoints |
| `/backend/app/services/__init__.py` | Ready | Member 3 | Marks services as a package | Processor services |
| `/backend/app/workers/__init__.py` | Ready | Member 3 | Marks workers as a package | Worker module |
| `/backend/tests/__init__.py` | Ready | Member 5 | Marks backend tests as a package | pytest |

---

# Backend File-Processing Services

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/backend/app/services/supabase_admin.py` | Integrated | Member 3 | Provides trusted PostgREST, RPC, and private Storage access | Supabase database and Storage |
| `/backend/app/services/file_extraction.py` | Integrated | Member 3 | Extracts text and source metadata from PDF, TXT, PPTX, XLSX, and XLS | File processor |
| `/backend/app/services/file_processor.py` | Integrated | Member 3 | Validates, downloads, extracts, chunks, persists, and finalizes study files | Supabase admin and extraction |
| `/backend/app/workers/file_processing_worker.py` | Integrated | Member 3 | Recovers stale jobs, atomically claims queued work, and processes files continuously | Supabase admin and file processor |
| `/backend/app/services/gemini.py` | Planned | Member 3 | Will provide the AI-provider wrapper | Future retrieval and generation modules |

---

# Backend Tests

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/backend/tests/test_health.py` | Ready | Member 5 | Tests the health response and CORS | FastAPI application |
| `/backend/tests/test_file_processor.py` | Ready | Members 3 and 5 | Tests queued and claimed processing, validation, extraction, persistence, and failure behavior | File processor |
| `/backend/tests/test_file_processing_worker.py` | Ready | Members 3 and 5 | Tests empty queues, success, failure, recovery, and worker configuration | Worker and fake admin service |
| `/backend/tests/` | Integrated | Members 3 and 5 | Contains all backend automated tests | pytest |

---

# Hosted Supabase Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/supabase/README.md` | Ready | Member 4 | Documents the hosted Supabase workflow | CLI and migrations |
| `/supabase/config.toml` | Integrated | Member 4 | Stores repository Supabase CLI configuration | Hosted project |
| `/supabase/migrations/` | Integrated | Member 4 | Stores timestamped database, Storage, RLS, trigger, and RPC changes | Hosted Supabase database |
| `/supabase/.temp/` | Local Only | Supabase CLI | Stores local linked-project metadata | Supabase CLI |
| `/supabase/seed.sql` | Planned | Member 4 | May contain safe development seed data later | Future test workflow |
| `/supabase/policies/` | Planned | Member 4 | May contain supporting policy documentation later | Database and Storage policies |

The current workflow uses hosted Supabase. Docker-based local Supabase services are not required.

---

# Known Phase 1 and Phase 2 Migrations

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/supabase/migrations/*_create_profiles*.sql` | Integrated | Member 4 | Creates profiles, ownership policies, timestamps, and new-user trigger | Supabase Auth |
| `/supabase/migrations/20260728070745_create_learning_profile_foundation.sql` | Integrated | Member 4 | Creates learning-profile tables and completion validation | Phase 2 onboarding |
| `/supabase/migrations/20260728074910_create_learning_profile_data_functions.sql` | Integrated | Member 4 | Creates replacement functions and onboarding-reset triggers | Learning-profile mutations |
| `/supabase/migrations/*_fix_replace_study_availability.sql` | Integrated | Member 4 | Corrects recurring availability JSON parsing | Study-availability RPC |

Wildcard entries are used when the exact timestamp varies between repository copies. The committed migration filename is the source of truth.

---

# Phase 3 Subject and File Migrations

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/supabase/migrations/20260729053314_create_subject_file_foundation.sql` | Integrated | Member 4 | Creates subjects, study-file metadata, private Storage bucket, RLS, policies, and initial statuses | Frontend subject and file features |
| `/supabase/migrations/*_add_powerpoint_file_support.sql` | Integrated | Member 4 | Adds PowerPoint MIME support where required | File upload validation |
| `/supabase/migrations/*_add_excel_file_support.sql` | Integrated | Member 4 | Adds Excel MIME support where required | File upload validation |
| `/supabase/migrations/20260731055238_create_file_processing_foundation.sql` | Integrated | Member 4 | Creates jobs, extracted contents, chunks, processing statuses, and persistence functions | Backend processor |
| `/supabase/migrations/*_queue_study_file_processing*.sql` | Integrated | Member 4 | Creates or updates the queue RPC | Upload completion action |
| `/supabase/migrations/*_claim_next_file_processing_job*.sql` | Integrated | Member 4 | Creates the atomic worker claim RPC using locking and `SKIP LOCKED` | Processing worker |
| `/supabase/migrations/*_recover_stale_file_processing_jobs.sql` | Integrated | Member 4 | Creates stale-job recovery and retry-limit behavior | Processing worker recovery |

Previously applied migrations must never be edited. Corrections require a new timestamped migration.

---

# Implemented Supabase Database Resources

| Resource | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `auth.users` | Integrated | Supabase | Stores authenticated student accounts | Profiles and sessions |
| `public.profiles` | Integrated | Member 4 | Stores student profile and onboarding state | Auth and onboarding |
| `public.learning_profiles` | Integrated | Member 4 | Stores general learning preferences | Phase 2 |
| `public.learning_profile_subjects` | Integrated | Member 4 | Stores strong and weak subjects with confidence | Phase 2 |
| `public.study_availability` | Integrated | Member 4 | Stores recurring weekly study periods | Phase 2 |
| `public.subjects` | Integrated | Member 4 | Stores academic subject workspaces | Phase 3 |
| `public.study_files` | Integrated | Member 4 | Stores upload metadata and file processing state | File manager and worker |
| `public.file_processing_jobs` | Integrated | Member 4 | Stores queue and worker processing state | Worker |
| `public.study_file_contents` | Integrated | Member 4 | Stores complete extracted text and metadata | File processor |
| `public.study_file_chunks` | Integrated | Member 4 | Stores ordered source-aware chunks | Future retrieval |
| `storage.objects` | Integrated | Supabase | Stores private uploaded objects | `study-materials` bucket |
| `study-materials` bucket | Integrated | Member 4 | Stores private student study files | Upload, preview, download, processor |

---

# Implemented Processing RPCs

| Function | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `queue_study_file_processing` | Integrated | Member 4 | Queues an uploaded file and creates or resets its job | Upload completion |
| `claim_next_file_processing_job` | Integrated | Member 4 | Atomically claims the next queued job | Worker |
| `start_study_file_processing` | Integrated | Member 4 | Starts processing for a queued file | Reusable processor |
| `mark_study_file_indexing` | Integrated | Member 4 | Changes an active file to indexing | File processor |
| `complete_study_file_processing` | Integrated | Member 4 | Stores full content and chunks and marks the file ready | File processor |
| `fail_study_file_processing` | Integrated | Member 4 | Saves synchronized failure state | Processor and worker |
| `recover_stale_file_processing_jobs` | Integrated | Member 4 | Requeues abandoned work or permanently fails exhausted jobs | Worker recovery |
| `complete_learning_profile_onboarding` | Integrated | Member 4 | Validates required onboarding data before completion | Phase 2 |

---

# Environment Variables

## Frontend Browser-Safe Variables

| Variable | File | Purpose |
|---|---|---|
| `NEXT_PUBLIC_SITE_URL` | `frontend/.env.local` | Builds local application and confirmation URLs |
| `NEXT_PUBLIC_API_BASE_URL` | `frontend/.env.local` | Connects the frontend to FastAPI |
| `NEXT_PUBLIC_SUPABASE_URL` | `frontend/.env.local` | Connects browser-safe Supabase clients |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | `frontend/.env.local` | Provides the public Supabase credential |

Only browser-safe values may use `NEXT_PUBLIC_`.

## Backend Private Variables

| Variable | File | Purpose |
|---|---|---|
| `APP_NAME` | `backend/.env` | FastAPI application name |
| `APP_VERSION` | `backend/.env` | Backend version |
| `ENVIRONMENT` | `backend/.env` | Runtime environment |
| `API_PREFIX` | `backend/.env` | API route prefix |
| `FRONTEND_URL` | `backend/.env` | Allowed CORS origin |
| `SUPABASE_URL` | `backend/.env` | Hosted Supabase project URL |
| `SUPABASE_SECRET_KEY` | `backend/.env` | Trusted backend-only Supabase credential |
| `PROCESSOR_INTERNAL_KEY` | `backend/.env` | Protects internal processing endpoints |
| `STUDY_MATERIALS_BUCKET` | `backend/.env` | Selects the private Storage bucket |
| `REQUEST_TIMEOUT_SECONDS` | `backend/.env` | Controls outbound-request timeout |
| `MAX_PROCESSING_FILE_BYTES` | `backend/.env` | Controls backend processing-size limit |
| `GEMINI_API_KEY` | `backend/.env` | Reserved for later AI integration |

Real values must never appear in Git, documentation, screenshots, frontend code, or logs.

---

# Generated and Local-Only Files

| Path | Status | Purpose |
|---|---|---|
| `/frontend/.next/` | Local Only | Next.js generated output |
| `/frontend/node_modules/` | Local Only | Frontend npm dependencies |
| `/frontend/tsconfig.tsbuildinfo` | Local Only | TypeScript build cache |
| `/backend/.venv/` | Local Only | Python virtual environment |
| `/backend/.env` | Local Only | Private backend configuration |
| `/frontend/.env.local` | Local Only | Local public frontend configuration |
| `/backend/**/__pycache__/` | Local Only | Python bytecode cache |
| `/backend/.pytest_cache/` | Local Only | pytest cache |
| `/node_modules/` | Local Only | Root npm tooling |
| `/supabase/.temp/` | Local Only | Supabase linked-project metadata |
| `/frontend/types/database.ts` | Generated | Supabase public-schema TypeScript definitions |
| `/frontend/next-env.d.ts` | Generated | Next.js TypeScript declarations |

---

# Planned Phase 4 Files

The exact Phase 4 structure must be finalized before implementation.

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/backend/app/services/embeddings.py` | Planned | Member 3 | Generates document embeddings | Gemini or approved embedding provider |
| `/backend/app/services/retrieval.py` | Planned | Member 3 | Retrieves relevant study-file chunks | `study_file_chunks` |
| `/backend/app/services/gemini.py` | Planned | Member 3 | Provides AI model access | Gemini API |
| `/backend/app/api/routes/retrieval.py` | Planned | Member 3 | Provides retrieval or source-grounded AI endpoints | Retrieval service |
| `/frontend/features/chat/` | Planned | Members 2 and 3 | Provides the student AI assistant | Retrieval API |
| `/frontend/features/reviewers/` | Planned | Members 2 and 4 | Provides reviewer generation and display | AI services |
| `/frontend/features/flashcards/` | Planned | Members 2 and 4 | Provides flashcard generation and practice | AI services |
| `/supabase/migrations/*_create_embeddings*.sql` | Planned | Member 4 | Adds vector storage and retrieval support | Future RAG pipeline |

Do not create these files until the Phase 4 architecture and database contracts are approved.

---

# New File Entry Template

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/path/to/file` | Created | Member # | Explain what the file does | List modules, services, tables, or endpoints |

---

# File Header Rules

Every manually created source file must begin with its filepath when the format supports comments.

## TypeScript and TSX

```typescript
// File: /frontend/path/to/file.ts
// Purpose: Explain the file's responsibility.
```

## JavaScript

```javascript
// File: /frontend/path/to/file.js
// Purpose: Explain the file's responsibility.
```

## Python

```python
# File: /backend/path/to/file.py
# Purpose: Explain the file's responsibility.
```

## CSS

```css
/* File: /frontend/path/to/file.css */
/* Purpose: Explain the file's responsibility. */
```

## Markdown

```markdown
<!-- File: /docs/path/to/file.md -->
<!-- Purpose: Explain the file's responsibility. -->
```

## SQL

```sql
-- File: /supabase/migrations/timestamp_description.sql
-- Purpose: Explain the migration.
```

## Environment Examples

```env
# File: /backend/.env.example
# Purpose: Documents safe environment-variable names.
```

## JSON Exception

Strict JSON files do not support comments.

Do not add filepath comments to:

- `package.json`
- `package-lock.json`
- `tsconfig.json`

Document those files in this master map instead.

---

# Connection Documentation Rules

For every important file, record:

- What imports or uses it
- What it imports or calls
- Which API endpoint it provides or consumes
- Which database table or Storage bucket it accesses
- Which environment variables it requires
- Which team member owns it
- Whether it is implemented, generated, local only, or planned

---

# Shared File Change Rules

Coordinate with the team before making major changes to:

```text
/.gitignore
/frontend/package.json
/frontend/package-lock.json
/frontend/app/layout.tsx
/frontend/app/providers.tsx
/frontend/theme/theme.ts
/frontend/types/database.ts
/backend/app/main.py
/backend/app/core/config.py
/backend/requirements.in
/backend/requirements.txt
/supabase/migrations/
/docs/PROJECT_FILE_MAP.md
/docs/ARCHITECTURE.md
/docs/database.md
/docs/api-contracts.md
```

Generated database types should be regenerated rather than manually edited.

Previously pushed migrations must never be edited.

---

# File-Map Verification Commands

List frontend file-management files:

```bash
cd ~/stsp-capstone

find frontend/features/files \
  -type f \
  | sort
```

List subject files:

```bash
find frontend/features/subjects \
  -type f \
  | sort
```

List backend processing files:

```bash
find backend/app/services \
  backend/app/workers \
  backend/app/api/routes \
  backend/tests \
  -type f \
  | sort
```

List migrations:

```bash
ls -1 supabase/migrations
```

Validate documentation formatting:

```bash
git diff --check
```

Confirm that all paths in this document are updated whenever files are renamed, added, or removed.
---

## Phase 4B — AI Provider Foundation

| File | Purpose | Owner | System connections |
|---|---|---|---|
| `backend/.env.example` | Documents safe AI provider environment-variable names and defaults without storing credentials. | Backend / AI | `Settings`, local `.env`, Gemini provider |
| `backend/app/core/config.py` | Loads and validates AI provider, model, dimension, timeout, generation, and live-test settings. | Backend / AI | `.env`, `GeminiProvider`, smoke-test scripts |
| `backend/app/ai/__init__.py` | Exposes shared AI contracts and controlled exception types. | Backend / AI | Backend services, providers, tests |
| `backend/app/ai/contracts.py` | Defines generation and embedding requests, results, task types, and asynchronous provider protocols. | Backend / AI | Future RAG services, `GeminiProvider`, tests |
| `backend/app/ai/errors.py` | Defines controlled configuration, request, and response exceptions for AI providers. | Backend / AI | `GeminiProvider`, future API error handling |
| `backend/app/ai/providers/__init__.py` | Exposes concrete AI provider implementations. | Backend / AI | Provider imports, backend services |
| `backend/app/ai/providers/gemini.py` | Implements asynchronous Gemini generation and embedding operations behind shared interfaces. | Backend / AI | Google Gen AI SDK, `Settings`, AI contracts |
| `backend/app/ai/smoke/__init__.py` | Marks the package containing explicitly controlled live AI smoke tests. | Backend / AI | Embedding and generation smoke scripts |
| `backend/app/ai/smoke/embedding.py` | Runs guarded live document and query embedding connectivity tests without printing vectors or credentials. | Backend / AI | `GeminiProvider`, Gemini Embedding 2, private `.env` |
| `backend/app/ai/smoke/generation.py` | Runs a guarded live generation connectivity test using a fixed non-sensitive marker. | Backend / AI | `GeminiProvider`, Gemini 3.6 Flash, private `.env` |
| `backend/tests/test_ai_config.py` | Tests AI settings, safe defaults, normalization, and validation without external requests. | Backend / QA | `Settings` |
| `backend/tests/test_ai_contracts.py` | Tests provider-independent AI contracts, validation, protocols, and exception hierarchy. | Backend / QA | `app.ai.contracts`, `app.ai.errors` |
| `backend/tests/test_gemini_provider.py` | Tests Gemini request construction, response parsing, errors, timeout handling, and cleanup using fake clients. | Backend / QA | `GeminiProvider`, Google Gen AI SDK types |
| `docs/AI_PROVIDER.md` | Documents the AI provider architecture, configuration, safety controls, and smoke-test workflow. | Documentation / AI | All Phase 4B AI files |
| `docs/PROJECT_FILE_MAP.md` | Maintains the master inventory of project files, purposes, owners, and connections. | Documentation | Entire repository |
| `docs/ARCHITECTURE.md` | Shows how the AI provider layer connects to backend services, configuration, Gemini models, and tests. | Documentation / Architecture | Backend, AI provider, Gemini API |

### Phase 4B System Connections

- Backend services depend on the provider-independent interfaces in `contracts.py`.
- `GeminiProvider` implements both `GenerationProvider` and `EmbeddingProvider`.
- `GeminiProvider` reads model and request settings through `Settings`.
- The Google Gen AI SDK is isolated inside the concrete Gemini provider.
- Offline tests inject fake clients and never contact Gemini.
- Live smoke tests require an API key, an enabled environment flag, and explicit command-line confirmation.
- Future chunking, retrieval, RAG, citation, and assistant services will call the shared provider interfaces rather than the SDK directly.
