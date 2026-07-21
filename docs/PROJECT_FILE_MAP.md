<!-- File: /docs/PROJECT_FILE_MAP.md -->

# STS Capstone Project File Map

This document is the central reference for the files and folders used in the STS Capstone Project.

Every team member must update this document when:

1. A new important file is created.
2. A file is renamed or moved.
3. A file begins using another service or module.
4. File ownership changes.
5. A file becomes obsolete or is removed.
6. An API, database table, or shared type changes.

## File Status

| Status | Meaning |
|---|---|
| Planned | The file or folder is expected but has not been created |
| Created | The file exists but may not be complete |
| In Progress | The owner is currently working on it |
| Ready | The file works independently |
| Integrated | The file works with the rest of the application |
| Deprecated | The file should no longer be used |

## Team Ownership

| Member | Main Responsibility |
|---|---|
| Member 1 | Technical lead, repository, authentication, integration, and deployment |
| Member 2 | Design system, application shell, dashboard, and shared UI |
| Member 3 | FastAPI backend, files, retrieval, and AI assistant |
| Member 4 | Supabase, database, reviewers, and quizzes |
| Member 5 | Testing, tasks, prioritization, study plans, and calendar |

## Root Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/.gitignore` | Created | Member 1 | Prevents secrets, dependencies, build outputs, and temporary files from being committed | Entire repository |
| `/README.md` | Planned | Member 1 | Gives the project overview, setup summary, and documentation links | `/docs/`, `/frontend/`, `/backend/`, `/supabase/` |
| `/frontend/` | Planned | Member 1 | Contains the Next.js frontend application | FastAPI API, Supabase Auth, Supabase Storage |
| `/backend/` | Created | Member 3 | Contains the FastAPI backend application | Frontend, Supabase, Gemini API |
| `/supabase/` | Created | Member 4 | Contains database migrations, policies, and Supabase setup files | FastAPI backend and Next.js frontend |
| `/docs/` | Created | Member 1 | Contains shared technical and project documentation | Entire repository |

## Documentation Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/docs/PROJECT_FILE_MAP.md` | Created | Member 1 | Master list of project files, owners, purposes, and connections | Entire repository |
| `/docs/ARCHITECTURE.md` | Created | Member 1 | Contains Mermaid diagrams showing system connections | Frontend, backend, Supabase, and Gemini |
| `/docs/setup-guide.md` | Created | Member 5 | Explains how to install and run the project | Frontend and backend setup |
| `/docs/api-contracts.md` | Created | Member 3 | Documents frontend and backend request and response formats | Frontend services and FastAPI routes |
| `/docs/database.md` | Created | Member 4 | Documents database tables, relationships, storage, and security | Supabase and FastAPI |
| `/docs/git-workflow.md` | Created | Member 1 | Explains branches, commits, pull requests, and code reviews | GitHub repository |
| `/docs/testing-checklist.md` | Created | Member 5 | Records required manual and automated tests | Entire application |

## Backend Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/backend/README.md` | Created | Member 3 | Placeholder documentation for the FastAPI backend | `/backend/app/` |
| `/backend/app/main.py` | Planned | Member 3 | Creates and configures the FastAPI application | API router, CORS, configuration |
| `/backend/app/api/router.py` | Planned | Member 3 | Combines the backend API routes | Health, authentication, files, AI, quizzes, tasks |
| `/backend/app/api/health.py` | Planned | Member 3 | Provides a health-check endpoint | Frontend connection test |
| `/backend/app/core/config.py` | Planned | Member 3 | Loads backend settings and environment variables | FastAPI, Supabase, Gemini |
| `/backend/requirements.txt` | Planned | Member 3 | Lists the backend Python dependencies | Python virtual environment |
| `/backend/.env.example` | Planned | Member 3 | Shows the backend environment variables without real secrets | Backend configuration |

## Supabase Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/supabase/README.md` | Created | Member 4 | Placeholder documentation for database and storage setup | Supabase migrations and policies |
| `/supabase/migrations/` | Planned | Member 4 | Stores versioned database changes | Supabase PostgreSQL database |
| `/supabase/policies/` | Planned | Member 4 | Stores row-level security documentation or scripts | Supabase database tables |
| `/supabase/seed.sql` | Planned | Member 4 | Adds safe sample data for development | Development database |

## Next.js Frontend Foundation Files

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/frontend/` | Created | Member 1 | Contains the Next.js frontend application | Browser, future FastAPI API, and Supabase |
| `/frontend/package.json` | Created | Member 1 | Defines frontend scripts and dependencies | npm and Next.js |
| `/frontend/package-lock.json` | Created | Member 1 | Locks the exact frontend dependency versions | `package.json` and npm |
| `/frontend/tsconfig.json` | Created | Member 1 | Configures TypeScript and the `@/*` import alias | All TypeScript and TSX files |
| `/frontend/eslint.config.mjs` | Created | Member 1 | Configures ESLint for Next.js and TypeScript | `npm run lint` |
| `/frontend/next-env.d.ts` | Generated | Next.js | Provides Next.js TypeScript declarations | TypeScript compiler |
| `/frontend/next.config.ts` | Integrated | Member 1 | Configures Next.js and the Turbopack project root | Next.js development server and production build |
| `/frontend/app/layout.tsx` | Integrated | Member 1 | Defines the root HTML layout and metadata | `globals.css` and all application pages |
| `/frontend/app/globals.css` | Integrated | Member 2 | Defines global colors and base browser styles | Root layout and all frontend pages |
| `/frontend/app/page.tsx` | Integrated | Member 1 | Displays the temporary frontend foundation page | `page.module.css` |
| `/frontend/app/page.module.css` | Integrated | Member 2 | Styles the temporary frontend foundation page | `page.tsx` |
| `/frontend/app/favicon.ico` | Generated | Next.js | Provides the browser-tab icon | Root application metadata |
| `/frontend/public/` | Created | Member 2 | Stores public static assets | Frontend pages and components |
| `/frontend/README.md` | Generated | Next.js | Contains the original Next.js setup reference | Frontend developers |
| `/frontend/.gitignore` | Generated | Next.js | Ignores frontend-specific generated files | Frontend repository files |

## New File Entry Template

Copy this row when adding a new file:

| Path | Status | Owner | Purpose | Connected To |
|---|---|---|---|---|
| `/path/to/file` | Created | Member # | Explain what the file does | List modules, services, or files it uses |

## File Header Rules

Whenever supported, every manually created source file must begin with its filepath.

### TypeScript and TSX

```typescript
// File: /frontend/path/to/file.ts