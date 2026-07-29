<!-- File: /docs/PROJECT_FILE_MAP.md -->

# STS Capstone Project File Map

This document is the central reference for the files and folders used in the STS Capstone Project.

Update this document whenever:

1. A new important file is created.
2. A file is renamed, moved, or removed.
3. A file begins using another service or module.
4. File ownership changes.
5. An API, database table, shared type, or environment variable changes.
6. A planned file becomes implemented.

# File Status

| Status | Meaning |
|---|---|
| Planned | Expected in a future phase but not created |
| Created | Exists but may not be independently tested |
| In Progress | Currently being developed |
| Ready | Works independently and has passed its direct checks |
| Integrated | Works with the rest of the application |
| Generated | Automatically created by a framework or tool |
| Local Only | Exists on each developer's computer and must not be committed |
| Deprecated | Removed or no longer used |

# Team Ownership

| Member | Main Responsibility |
|---|---|
| Member 1 | Technical lead, repository, authentication, integration, and deployment |
| Member 2 | Design system, application shell, dashboard, and shared UI |
| Member 3 | FastAPI backend, files, retrieval, and AI assistant |
| Member 4 | Supabase, database, reviewers, and quizzes |
| Member 5 | Testing, tasks, prioritization, study plans, and calendar |

# Root Files and Folders

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/.gitignore` | Integrated | Member 1 | Excludes secrets, dependencies, build output, caches, and local files | Entire repository |
| `/README.md` | Integrated | Member 1 | Provides the project overview and links to technical documentation | `/docs/`, `/frontend/`, `/backend/`, `/supabase/` |
| `/frontend/` | Integrated | Member 1 and Member 2 | Contains the Next.js and Mantine frontend | Browser and future backend/Supabase connections |
| `/backend/` | In Progress | Member 3 | Contains the FastAPI backend foundation | Future frontend, Supabase, and Gemini connections |
| `/supabase/` | Created | Member 4 | Contains Supabase documentation and future migrations | Future frontend and backend integration |
| `/docs/` | Integrated | Member 1 and Member 5 | Contains shared technical documentation | Entire repository |

# Documentation Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/docs/PROJECT_FILE_MAP.md` | Integrated | Member 1 | Master list of files, owners, purposes, statuses, and connections | Entire repository |
| `/docs/ARCHITECTURE.md` | Integrated | Member 1 | Shows current and planned system connections using Mermaid | Frontend, backend, Supabase, and Gemini |
| `/docs/setup-guide.md` | Integrated | Member 5 | Explains installation, configuration, testing, and startup steps | Frontend and backend |
| `/docs/api-contracts.md` | Created | Member 3 | Documents planned and implemented API request/response formats | Frontend services and FastAPI routes |
| `/docs/database.md` | Created | Member 4 | Documents planned database relationships, storage, and security | Supabase and FastAPI |
| `/docs/git-workflow.md` | Created | Member 1 | Explains branches, commits, pull requests, and reviews | GitHub repository |
| `/docs/testing-checklist.md` | Integrated | Member 5 | Tracks completed and pending tests | Entire application |

# Frontend Foundation Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/package.json` | Integrated | Member 1 | Defines frontend scripts and direct dependencies | npm and Next.js |
| `/frontend/package-lock.json` | Integrated | Member 1 | Locks exact frontend dependency versions | `package.json` and npm |
| `/frontend/tsconfig.json` | Integrated | Member 1 | Configures TypeScript and the `@/*` alias | All TypeScript and TSX files |
| `/frontend/eslint.config.mjs` | Integrated | Member 1 | Configures ESLint for Next.js and TypeScript | `npm run lint` |
| `/frontend/next-env.d.ts` | Generated | Next.js | Provides Next.js TypeScript declarations | TypeScript compiler |
| `/frontend/next.config.ts` | Integrated | Member 1 | Configures Next.js and the Turbopack project root | Development server and production build |
| `/frontend/postcss.config.cjs` | Integrated | Member 2 | Enables Mantine-compatible PostCSS processing | CSS and CSS Modules |
| `/frontend/app/favicon.ico` | Generated | Next.js | Provides the browser-tab icon | Root application metadata |
| `/frontend/public/` | Created | Member 2 | Stores public static assets | Frontend pages and components |
| `/frontend/README.md` | Generated | Next.js | Contains the original Next.js reference | Frontend developers |
| `/frontend/.gitignore` | Generated | Next.js | Adds frontend-specific ignore rules | Frontend generated files |
| `/frontend/node_modules/` | Local Only | Each member | Stores locally installed npm packages | Recreated using `npm install` |
| `/frontend/.next/` | Local Only | Next.js | Stores generated development and build output | Recreated by `npm run dev` and `npm run build` |

# Frontend Application and Mantine Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/app/layout.tsx` | Integrated | Member 1 | Loads metadata, Inter, Mantine styles, color-scheme support, and providers | `providers.tsx`, `globals.css`, and all routes |
| `/frontend/app/providers.tsx` | Integrated | Member 2 | Provides Mantine theme, modal management, and notifications | Root layout and all frontend pages |
| `/frontend/app/globals.css` | Integrated | Member 2 | Defines global variables, background, typography, and browser defaults | Root layout and all pages |
| `/frontend/app/page.tsx` | Integrated | Member 2 | Displays the interactive Mantine foundation check | `MantineFoundationCheck.tsx` |
| `/frontend/app/page.module.css` | Deprecated | Member 2 | Old temporary page stylesheet removed after the Mantine component was created | Replaced by `MantineFoundationCheck.module.css` |
| `/frontend/components/foundation/MantineFoundationCheck.tsx` | Integrated | Member 2 | Displays design-system checks and hosts the frontend-to-backend health-check interface | Mantine providers, `BackendHealthCheck.tsx`, Tabler Icons, and CSS Modules |
| `/frontend/components/foundation/MantineFoundationCheck.module.css` | Integrated | Member 2 | Styles the Mantine system-check component | `MantineFoundationCheck.tsx` |
| `/frontend/theme/colors.ts` | Integrated | Member 2 | Stores the purple palette and application color tokens | `theme.ts`, components, and charts |
| `/frontend/theme/components.ts` | Integrated | Member 2 | Defines shared Mantine component defaults | `theme.ts` |
| `/frontend/theme/theme.ts` | Integrated | Member 2 | Combines colors, typography, radius, shadows, and defaults | `providers.tsx` |

# Frontend API Integration Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/.gitignore` | Integrated | Member 1 | Ignores local frontend environment files while allowing `.env.example` | Frontend environment configuration |
| `/frontend/.env.example` | Ready | Member 1 | Documents the public backend base URL needed by the frontend | `.env.local` and `services/api.ts` |
| `/frontend/.env.local` | Local Only | Each member | Stores the developer's local backend URL | `services/api.ts`; excluded by `.gitignore` |
| `/frontend/types/api.ts` | Integrated | Member 1 | Defines the typed FastAPI health-response structure | `services/api.ts` and `BackendHealthCheck.tsx` |
| `/frontend/services/api.ts` | Integrated | Member 1 | Builds API URLs, validates configuration and responses, applies a timeout, and handles backend request errors | `.env.local`, `types/api.ts`, and `GET /api/health` |
| `/frontend/components/foundation/BackendHealthCheck.tsx` | Integrated | Member 1 | Displays idle, loading, success, error, check-again, and retry states for the FastAPI health endpoint | `services/api.ts`, `types/api.ts`, and `MantineFoundationCheck.tsx` |
| `/frontend/components/foundation/BackendHealthCheck.module.css` | Integrated | Member 2 | Styles the responsive frontend-to-backend health interface | `BackendHealthCheck.tsx` |

# Supabase Client Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/lib/supabase/config.ts` | Ready | Member 1 | Validates the browser-safe hosted Supabase URL and publishable key | `.env.local`, browser client, and server client |
| `/frontend/lib/supabase/client.ts` | Ready | Member 1 | Creates the Supabase browser client for Client Components | Public Supabase configuration and future authentication forms |
| `/frontend/lib/supabase/server.ts` | Ready | Member 1 | Creates the cookie-aware Supabase client for Server Components, Server Actions, and Route Handlers | Public Supabase configuration, Next.js cookies, and future auth proxy |
| `/backend/app/database/supabase_client.py` | Ready | Member 4 | Creates and caches the trusted server-side Supabase client | `config.py`, backend `.env`, hosted Supabase, and future backend services |

# Backend Dependency and Environment Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/backend/README.md` | Created | Member 3 | Documents the backend folder's planned responsibilities | `/backend/app/` |
| `/backend/requirements.in` | Ready | Member 3 | Lists direct Python packages intentionally selected for the backend | pip, FastAPI, Supabase, Gemini, and tests |
| `/backend/requirements.txt` | Ready | Member 3 | Locks the complete tested Python environment to exact versions | `.venv` and team setup |
| `/backend/.venv/` | Local Only | Each member | Contains the isolated Python environment | Recreated using `requirements.txt` |
| `/backend/.env.example` | Ready | Member 3 | Documents backend environment variables without real secrets | `config.py` and team setup |
| `/backend/.env` | Local Only | Each member | Stores private local backend settings and credentials | `config.py` |
| `/backend/app/core/config.py` | Ready | Member 3 | Loads typed settings from environment variables and `.env` | Future FastAPI app, CORS, Supabase, and Gemini |

# Backend Package Structure

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/backend/app/` | In Progress | Member 3 | Contains the FastAPI source code | FastAPI runtime and feature modules |
| `/backend/app/__init__.py` | Created | Member 3 | Marks the main application folder as a Python package | All backend imports |
| `/backend/app/api/` | Created | Member 3 | Contains API routers and endpoint registration | Future `main.py` and feature routes |
| `/backend/app/api/__init__.py` | Created | Member 3 | Marks the API folder as a Python package | API imports |
| `/backend/app/core/` | Created | Member 3 | Contains settings, exceptions, and logging | Entire backend |
| `/backend/app/core/__init__.py` | Created | Member 3 | Marks the core folder as a Python package | Core imports |
| `/backend/app/database/` | Created | Member 4 | Contains future Supabase and database utilities | Supabase database and storage |
| `/backend/app/database/__init__.py` | Created | Member 4 | Marks the database folder as a Python package | Database imports |
| `/backend/app/modules/` | Created | Member 3 | Contains future feature-specific modules | Routes, schemas, and services |
| `/backend/app/modules/__init__.py` | Created | Member 3 | Marks the modules folder as a Python package | Module imports |
| `/backend/app/schemas/` | Created | Member 3 | Contains future Pydantic request and response models | Routes and services |
| `/backend/app/schemas/__init__.py` | Created | Member 3 | Marks the schemas folder as a Python package | Schema imports |
| `/backend/app/services/` | Created | Member 3 | Contains future shared services such as Gemini and file processing | Modules and external APIs |
| `/backend/app/services/__init__.py` | Created | Member 3 | Marks the services folder as a Python package | Service imports |
| `/backend/tests/` | Created | Member 5 | Contains backend automated tests | FastAPI application and services |
| `/backend/tests/__init__.py` | Created | Member 5 | Marks the test folder as a Python package | pytest |

# Backend Application and Planned API Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/backend/app/main.py` | Integrated | Member 3 | Creates FastAPI, configures CORS, and registers the main API router | `config.py`, `router.py`, and `CORSMiddleware` |
| `/backend/app/api/router.py` | Integrated | Member 3 | Combines all backend feature routers | `main.py` and `health.py` |
| `/backend/app/api/health.py` | Integrated | Member 3 | Provides `GET /api/health` | Health schema, settings, router, and frontend connection test |
| `/backend/app/schemas/health.py` | Integrated | Member 3 | Defines the typed health response | Health route and Swagger documentation |
| `/backend/tests/test_health.py` | Ready | Member 5 | Tests the health response and frontend CORS origin | FastAPI application and health route |
| `/backend/app/database/supabase_client.py` | Planned | Member 4 | Creates the trusted server-side Supabase client | Supabase database and storage |
| `/backend/app/services/gemini.py` | Planned | Member 3 | Creates the Gemini service wrapper | Google Gen AI SDK and feature modules |

# Repository Tooling Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/package.json` | Ready | Member 1 | Defines repository-level development tools and Supabase CLI scripts | npm, Supabase CLI, and the root `package-lock.json` |
| `/package-lock.json` | Ready | Member 1 | Locks the exact dependency tree for repository-level tooling | Root `package.json` and team setup |
| `/node_modules/` | Local Only | Each member | Stores locally installed repository tools | Recreated using `npm install`; excluded by `.gitignore` |

# Supabase Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/supabase/README.md` | Created | Member 4 | Documents the Supabase folder and hosted-development workflow | Supabase configuration, migrations, policies, and team setup |
| `/supabase/config.toml` | Ready | Member 4 | Stores repository-level Supabase CLI configuration | Supabase CLI, future hosted-project link, migrations, Auth, Storage, and API settings |
| `/supabase/migrations/` | Planned | Member 4 | Stores versioned PostgreSQL schema and policy changes | Hosted Supabase database and `supabase db push` |
| `/supabase/policies/` | Planned | Member 4 | Stores supporting row-level security documentation when required | Supabase tables and Storage |
| `/supabase/seed.sql` | Planned | Member 4 | Stores safe non-production development seed data | Future development database workflow |
| `/supabase/.temp/` | Local Only | Supabase CLI | Stores local metadata such as the linked project reference | Generated by Supabase CLI and excluded from Git |

# New File Entry Template

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/path/to/file` | Created | Member # | Explain what the file does | List modules, services, or files it uses |

# File Header Rules

Every manually created source file must begin with its filepath when the file format supports comments.

## TypeScript and TSX

```typescript
// File: /frontend/path/to/file.ts
```

## JavaScript

```javascript
// File: /frontend/path/to/file.js
```

## Python

```python
# File: /backend/path/to/file.py
```

## CSS

```css
/* File: /frontend/path/to/file.css */
```

## Markdown

```markdown
<!-- File: /docs/path/to/file.md -->
```

## SQL

```sql
-- File: /supabase/path/to/file.sql
```

## Environment Examples

```env
# File: /backend/.env.example
```

## JSON Exception

Strict JSON files do not support comments. Do not add filepath comments to:

- `package.json`
- `package-lock.json`
- `tsconfig.json`

Document those files in this masterfile instead.

# Connection Documentation Rules

For each important file, record:

- What imports or uses it
- What it imports or calls
- Which API endpoint it provides or consumes
- Which database table or storage bucket it accesses
- Which environment variables it requires
- Which team member owns it
- Whether it is implemented or planned

# Shared File Change Rules

Coordinate with the team before making major changes to:

- `/.gitignore`
- `/frontend/package.json`
- `/frontend/package-lock.json`
- `/frontend/app/layout.tsx`
- `/frontend/app/providers.tsx`
- `/frontend/theme/theme.ts`
- `/backend/app/main.py`
- `/backend/app/core/config.py`
- `/backend/requirements.in`
- `/backend/requirements.txt`
- `/supabase/migrations/`
- `/docs/PROJECT_FILE_MAP.md`
- `/docs/ARCHITECTURE.md`

# Authentication Foundation Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/docs/authentication.md` | Ready | Member 5 | Documents authentication routes, flows, security rules, and implementation phases | Supabase Auth, profiles table, frontend routes, and project architecture |
| `/frontend/proxy.ts` | Ready | Member 1 | Runs the authentication session-refresh process for matched Next.js requests | `lib/supabase/proxy.ts` and Next.js request lifecycle |
| `/frontend/lib/supabase/proxy.ts` | Ready | Member 1 | Validates authentication claims and synchronizes refreshed cookies between requests and responses | Supabase Auth, public configuration, generated database types, and root Proxy |

# Phase 2 Files (Onboarding and Learning Profile)
| Path | Status | Owner | Purpose | Connections |
|---|---|---|---|---|
| `/frontend/features/learning-profile/constants.ts` | Integrated | Member 2 | Defines questionnaire options and onboarding steps | Validation, actions, forms, routing |
| `/frontend/features/learning-profile/types.ts` | Integrated | Member 2 | Defines learning-profile input and snapshot types | Generated database types, queries, mutations |
| `/frontend/features/learning-profile/validation.ts` | Integrated | Member 2 | Validates student-profile and questionnaire values | Server mutations and Server Actions |
| `/frontend/features/learning-profile/progress.ts` | Integrated | Member 2 | Calculates onboarding progress from saved records | Onboarding shell and resume routing |
| `/frontend/features/learning-profile/routing.ts` | Integrated | Member 2 | Maps onboarding steps to application routes | Onboarding entry route |
| `/frontend/features/learning-profile/display.ts` | Integrated | Member 2 | Formats stored profile values for display | Review, dashboard, profile page |
| `/frontend/features/learning-profile/server/auth.ts` | Integrated | Member 2 | Retrieves the verified authenticated user ID | Queries and mutations |
| `/frontend/features/learning-profile/server/queries.ts` | Integrated | Member 2 | Loads the complete onboarding snapshot | Onboarding pages, dashboard, profile |
| `/frontend/features/learning-profile/server/mutations.ts` | Integrated | Member 2 | Saves learning-profile sections and completes onboarding | Server Actions and Supabase RPCs |
| `/frontend/features/learning-profile/server/guards.ts` | Integrated | Member 2 | Protects pages requiring completed onboarding | Dashboard and profile |
| `/frontend/app/(protected)/onboarding/` | Integrated | Member 2 | Contains the six-step learning-profile onboarding flow | Supabase profile tables and Server Actions |
| `/frontend/app/(protected)/profile/page.tsx` | Integrated | Member 2 | Displays and manages the completed learning profile | Dashboard and onboarding edit routes |
| `/supabase/migrations/20260728070745_create_learning_profile_foundation.sql` | Integrated | Member 4 | Creates learning-profile tables and completion function | Supabase Auth and frontend database types |
| `/supabase/migrations/20260728074910_create_learning_profile_data_functions.sql` | Integrated | Member 4 | Creates atomic replacement functions and reset triggers | Subject and availability mutations |
| `/supabase/migrations/<actual_timestamp>_fix_replace_study_availability.sql` | Integrated | Member 4 | Corrects recurring availability JSON parsing | Availability RPC |