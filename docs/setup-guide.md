<!-- File: /docs/setup-guide.md -->
<!-- Purpose: Explains how to install, configure, validate, and run the STS Capstone Project through Phase 3. -->

# Development Setup Guide

This document explains how to install, configure, validate, and run the STS Capstone Project.

The current application includes:

- Next.js frontend
- Mantine design system
- Supabase Authentication
- Supabase PostgreSQL
- Private Supabase Storage
- Learning-profile onboarding
- Subject management
- Study-file uploads
- Background document processing
- PDF, TXT, PPTX, XLSX, and XLS extraction
- Automatic frontend processing-status updates
- Stale processing-job recovery
- FastAPI health and internal processing endpoints

---

# Supported Development Environment

## Required Software

Install:

- Git
- Visual Studio Code
- Node.js 20.9 or newer
- npm
- Python 3.12 or another version supported by the locked dependencies
- A supported web browser
- A Supabase account
- Access to the team's hosted Supabase development project

Docker is not required for the current hosted Supabase workflow.

## Verified Project Versions

The project has been developed and tested with versions including:

```text
Node.js: v22.15.0
npm: 11.16.0
Next.js: 16.2.10
Python: 3.12
```

Install dependencies from the committed lock files instead of manually selecting package versions.

---

# Repository Setup

## Clone the Repository

```bash
git clone <repository-url>
cd stsp-capstone
```

For an existing local copy:

```bash
cd ~/stsp-capstone

git fetch origin
git status
```

Check the current branch:

```bash
git branch --show-current
```

Feature work should normally be completed on a feature branch rather than directly on `main`.

---

# Root Repository Tools

The repository root contains its own npm package for shared tools such as the Supabase CLI.

This package is separate from the frontend package.

Install root dependencies:

```bash
cd ~/stsp-capstone

npm install
```

This reads:

```text
/package.json
/package-lock.json
```

and creates:

```text
/node_modules/
```

The generated root `node_modules` folder must not be committed.

Verify the locally installed Supabase CLI:

```bash
npx supabase --version
```

Display available commands:

```bash
npx supabase --help
```

Do not install the Supabase CLI globally through npm.

---

# Frontend Setup

## Install Frontend Dependencies

```bash
cd ~/stsp-capstone/frontend

npm install
```

This reads:

```text
frontend/package.json
frontend/package-lock.json
```

and creates:

```text
frontend/node_modules/
```

The `node_modules` folder is local and must not be committed.

---

# Frontend Environment Configuration

Create the frontend local environment file from its safe example:

```bash
cd ~/stsp-capstone/frontend

cp .env.example .env.local
```

The safe file may be committed:

```text
frontend/.env.example
```

The private local file must not be committed:

```text
frontend/.env.local
```

Use the exact variable names already defined in `.env.example`.

The frontend configuration includes values such as:

```env
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
```

Only public browser-safe values may use the `NEXT_PUBLIC_` prefix.

Never store these values in frontend variables:

```text
SUPABASE_SECRET_KEY
PROCESSOR_INTERNAL_KEY
Database password
Gemini secret
```

Restart the Next.js development server whenever `.env.local` changes.

---

# Frontend Technology Stack

The approved frontend stack is:

- Next.js
- TypeScript
- Mantine UI
- CSS Modules
- Global CSS variables
- Tabler Icons
- Motion
- Mantine Charts or Recharts

Tailwind is not the main styling system for this project.

Important Mantine packages include:

```text
@mantine/core
@mantine/hooks
@mantine/form
@mantine/notifications
@mantine/modals
@mantine/dropzone
@mantine/dates
@mantine/charts
@mantine/spotlight
@tabler/icons-react
motion
dayjs
recharts
```

The provider hierarchy is:

```text
app/layout.tsx
    ↓
app/providers.tsx
    ├── MantineProvider
    ├── ModalsProvider
    └── Notifications
```

Only one global `Notifications` component should be rendered.

---

# Run the Frontend

```bash
cd ~/stsp-capstone/frontend

npm run dev
```

Open:

```text
http://localhost:3000
```

Stop the server using:

```text
Ctrl + C
```

---

# Frontend Validation

Run all frontend checks before committing:

```bash
cd ~/stsp-capstone/frontend

rm -rf .next
rm -f tsconfig.tsbuildinfo

npx next typegen
npm run lint
npx tsc --noEmit
npm run build
```

Expected results:

- Route type generation succeeds
- ESLint reports no errors
- TypeScript reports no errors
- The production build succeeds

Do not edit files inside:

```text
frontend/.next/
```

The `.next` folder is generated automatically.

---

# Frontend Cache Troubleshooting

When Next.js reports corrupted generated data, missing generated route types, or errors such as `Unexpected end of JSON input`, stop the development server and run:

```bash
cd ~/stsp-capstone/frontend

rm -rf .next
rm -f tsconfig.tsbuildinfo

npx next typegen
npm run dev
```

Do not delete source-code folders.

---

# Backend Setup

## Create the Python Virtual Environment

### macOS or Linux

```bash
cd ~/stsp-capstone/backend

python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
cd backend

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

After activation, the terminal should begin with:

```text
(.venv)
```

The `.venv` folder is local and must not be committed.

---

# Install Backend Dependencies

With the virtual environment active:

```bash
cd ~/stsp-capstone/backend

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verify the installed dependency graph:

```bash
python -m pip check
```

Expected:

```text
No broken requirements found.
```

## Backend Dependency Files

| File | Purpose |
|---|---|
| `requirements.in` | Lists direct dependencies selected by the team |
| `requirements.txt` | Locks the complete tested dependency environment |
| `.venv/` | Stores local packages and must not be committed |

Phase 3 extraction dependencies include packages for:

- PDF extraction
- PowerPoint extraction
- Modern Excel extraction
- Legacy Excel extraction
- FastAPI
- HTTP requests
- Supabase communication
- Testing

When changing backend dependencies:

```text
Edit requirements.in
        ↓
Install or compile the dependency set
        ↓
Regenerate requirements.txt
        ↓
Run pip check
        ↓
Run all backend tests
```

Do not modify `requirements.txt` without also verifying the complete environment.

---

# Backend Environment Configuration

Create the private environment file:

```bash
cd ~/stsp-capstone/backend

cp .env.example .env
```

The safe template may be committed:

```text
backend/.env.example
```

The real local file must not be committed:

```text
backend/.env
```

Use the variable names provided by `.env.example`.

Current backend configuration includes values such as:

```env
APP_NAME=STS Capstone API
APP_VERSION=0.1.0
ENVIRONMENT=development
API_PREFIX=/api
FRONTEND_URL=http://localhost:3000

SUPABASE_URL=
SUPABASE_SECRET_KEY=
PROCESSOR_INTERNAL_KEY=
STUDY_MATERIALS_BUCKET=study-materials

REQUEST_TIMEOUT_SECONDS=30
MAX_PROCESSING_FILE_BYTES=20971520

GEMINI_API_KEY=
```

The exact values for secrets must be entered privately.

Never:

- Commit `backend/.env`
- Paste a Supabase secret into chat
- Store the secret in frontend code
- Add `NEXT_PUBLIC_` to a private key
- Display the complete `.env` file
- Include private values in screenshots
- Put secrets in documentation

After changing backend environment values, restart FastAPI and the worker.

---

# Verify Backend Configuration

With the virtual environment active:

```bash
cd ~/stsp-capstone/backend

python - <<'PY'
from app.core.config import get_settings

settings = get_settings()

print(
    settings.app_name,
    settings.environment,
    settings.api_prefix,
    settings.frontend_url,
)
PY
```

This command intentionally prints only non-secret settings.

Do not print:

```text
supabase_secret_key
processor_internal_key
gemini_api_key
```

---

# Run the FastAPI Backend

```bash
cd ~/stsp-capstone/backend

source .venv/bin/activate

python -m uvicorn app.main:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000
```

Open the health endpoint:

```text
http://127.0.0.1:8000/api/health
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

Open the OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

Stop FastAPI using:

```text
Ctrl + C
```

---

# Backend Validation

With the virtual environment active:

```bash
cd ~/stsp-capstone/backend

python -m compileall app
python -m pytest
python -m pip check
```

Expected:

- All application modules compile
- All automated tests pass
- No broken dependencies are reported

List registered API routes:

```bash
python - <<'PY'
from app.main import app

for path, operations in app.openapi()["paths"].items():
    methods = [
        method.upper()
        for method in operations
        if method.lower() in {
            "get",
            "post",
            "put",
            "patch",
            "delete",
        }
    ]

    print(methods, path)
PY
```

Expected Phase 3 routes include:

```text
GET  /api/health
POST /api/internal/file-processing/{file_id}/validate-source
POST /api/internal/file-processing/{file_id}/process
```

---

# Supabase Hosted-Project Workflow

The project uses a hosted Supabase development project.

Docker-based local Supabase services are not required.

Do not use these commands for the current workflow:

```text
npx supabase start
npx supabase stop
npx supabase db reset
```

unless the team intentionally changes to a local Docker workflow.

---

# Authenticate the Supabase CLI

From the project root:

```bash
cd ~/stsp-capstone

npx supabase login
```

Follow the browser or token instructions provided by the CLI.

Do not commit the access token.

---

# Link the Repository to Supabase

Link only when the repository is not already linked:

```bash
cd ~/stsp-capstone

npx supabase link \
  --project-ref YOUR_PROJECT_REFERENCE
```

The linked project reference must match the team's development project.

Do not paste the database password into documentation or source code.

---

# Check Migration Status

```bash
cd ~/stsp-capstone

npx supabase migration list --linked
```

Check whether pending migrations exist:

```bash
npx supabase db push \
  --linked \
  --dry-run
```

Expected when synchronized:

```text
Remote database is up to date.
```

---

# Apply New Migrations

Always perform a dry run first:

```bash
cd ~/stsp-capstone

git diff --check

npx supabase db push \
  --linked \
  --dry-run
```

Apply pending migrations:

```bash
npx supabase db push --linked
```

Verify afterward:

```bash
npx supabase migration list --linked

npx supabase db push \
  --linked \
  --dry-run
```

Previously pushed migrations must never be edited.

Use a new corrective migration when changing an applied schema.

---

# Generate Supabase Database Types

After applying a migration:

```bash
cd ~/stsp-capstone

npx supabase gen types typescript \
  --linked \
  --schema public \
  > frontend/types/database.ts
```

Generated file:

```text
frontend/types/database.ts
```

Do not manually edit this file.

Run the frontend checks after regenerating it:

```bash
cd ~/stsp-capstone/frontend

npx next typegen
npm run lint
npx tsc --noEmit
npm run build
```

---

# Implemented Supabase Resources

Phase 3 uses:

## Authentication

```text
auth.users
```

## Application Tables

```text
public.profiles
public.learning_profiles
public.learning_profile_subjects
public.study_availability
public.subjects
public.study_files
public.file_processing_jobs
public.study_file_contents
public.study_file_chunks
```

## Private Storage Bucket

```text
study-materials
```

## Processing Functions

```text
queue_study_file_processing
claim_next_file_processing_job
start_study_file_processing
mark_study_file_indexing
complete_study_file_processing
fail_study_file_processing
recover_stale_file_processing_jobs
```

More details are documented in:

```text
docs/database.md
docs/api-contracts.md
docs/ARCHITECTURE.md
```

---

# Run the Complete Application

The Phase 3 application requires three running processes.

## Terminal 1 — Frontend

```bash
cd ~/stsp-capstone/frontend

npm run dev
```

Open:

```text
http://localhost:3000
```

---

## Terminal 2 — FastAPI Backend

```bash
cd ~/stsp-capstone/backend

source .venv/bin/activate

python -m uvicorn app.main:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000
```

Confirm:

```text
http://127.0.0.1:8000/api/health
```

---

## Terminal 3 — File-Processing Worker

```bash
cd ~/stsp-capstone/backend

source .venv/bin/activate

python -m app.workers.file_processing_worker \
  --poll-seconds 2 \
  --recovery-interval-seconds 30 \
  --stale-after-minutes 30 \
  --max-attempts 3
```

The worker should display a startup message indicating its polling and recovery intervals.

Stop it using:

```text
Ctrl + C
```

---

# Worker Command Options

Display all worker arguments:

```bash
cd ~/stsp-capstone/backend

source .venv/bin/activate

python -m app.workers.file_processing_worker \
  --help
```

Supported options include:

| Option | Purpose |
|---|---|
| `--once` | Recover stale work, process at most one job, and exit |
| `--poll-seconds` | Delay when no queued job exists |
| `--recovery-interval-seconds` | Delay between stale-job recovery checks |
| `--stale-after-minutes` | Age before an active job is considered abandoned |
| `--max-attempts` | Maximum processing attempts before permanent failure |

Run one worker cycle:

```bash
python -m app.workers.file_processing_worker \
  --once \
  --stale-after-minutes 30 \
  --max-attempts 3
```

When no queued job exists, the command should exit normally.

---

# File-Upload and Processing Test

1. Start the frontend.
2. Start FastAPI.
3. Start the processing worker.
4. Sign in using a test student account.
5. Open `/subjects`.
6. Create or select a subject.
7. Enter a topic.
8. Upload a supported file.
9. Remain on the same page without refreshing manually.

Expected status flow:

```text
Uploading
→ Queued
→ Reading
→ Indexing
→ Ready
```

After the file becomes ready:

- Preview should appear
- Download should appear
- Automatic polling should stop
- No duplicate file record should be created
- Extracted content should exist
- At least one chunk should exist

---

# Supported Upload Formats

The frontend accepts:

```text
PDF
TXT
PPT
PPTX
XLS
XLSX
JPEG
PNG
WebP
```

Maximum upload size:

```text
20 MB
```

Backend text extraction is implemented for:

```text
PDF
TXT
PPTX
XLSX
XLS
```

The following are accepted for storage but do not yet have implemented text extraction:

```text
PPT
JPEG
PNG
WebP
```

OCR and legacy PPT extraction are planned for later phases.

---

# Extraction Dependencies

| Format | Library |
|---|---|
| PDF | `pypdf` |
| TXT | Python UTF-8 decoding |
| PPTX | `python-pptx` |
| XLSX | `openpyxl` |
| XLS | `xlrd` |

Extraction should preserve source locations:

| Format | Locator |
|---|---|
| PDF | Page |
| TXT | Document |
| PPTX | Slide |
| XLSX | Sheet |
| XLS | Sheet |

---

# Automatic Frontend Status Refresh

`FileUploadManager` polls while at least one file has an active state:

```text
uploading
queued
reading
indexing
```

Polling stops when every file reaches:

```text
ready
failed
```

Polling pauses when the browser tab is hidden and resumes when the tab becomes visible.

A user should not need to manually refresh the page for a completed file to display `Ready`.

---

# Preview and Download

Preview and download become available only when:

```text
processing_status = ready
```

The frontend:

1. Verifies the authenticated user owns the file.
2. Creates a short-lived signed Storage URL.
3. Opens the preview or starts the download.

The private Storage bucket must never be changed to public.

---

# Retry Failed Upload

Only files with:

```text
processing_status = failed
```

may be retried.

The replacement upload must use the same original filename.

Retry should:

1. Prepare the failed record for another upload.
2. Upload the replacement object.
3. Queue processing again.
4. Restart automatic status polling.
5. End in either `ready` or `failed`.

---

# Test the Health Connection

With the frontend and FastAPI running:

1. Open the frontend health-check interface.
2. Select **Check backend**.
3. Confirm it displays **Connected**.
4. Stop FastAPI.
5. Check again.
6. Confirm it displays **Unavailable**.
7. Restart FastAPI.
8. Select **Retry connection**.
9. Confirm it returns to **Connected**.

The frontend should use:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

The backend CORS origin should use:

```env
FRONTEND_URL=http://localhost:3000
```

Use `localhost:3000` consistently during browser testing.

---

# Internal Processing Endpoint Test

Internal processing endpoints require:

```http
X-Processor-Key
```

Load the key without printing it:

```bash
cd ~/stsp-capstone/backend

PROCESSOR_KEY=$(
  grep '^PROCESSOR_INTERNAL_KEY=' .env |
  cut -d '=' -f 2-
)
```

Validate a file source:

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/internal/file-processing/FILE_UUID/validate-source" \
  -H "X-Processor-Key: ${PROCESSOR_KEY}"
```

Process a file:

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/internal/file-processing/FILE_UUID/process" \
  -H "X-Processor-Key: ${PROCESSOR_KEY}"
```

Replace `FILE_UUID` with an actual study-file UUID.

Never print or paste `PROCESSOR_KEY`.

Normally, automatic processing should be performed by the worker instead of manually calling the endpoint.

---

# macOS Troubleshooting

## `code` Command Is Not Available

Open the repository using:

```bash
cd ~/stsp-capstone

open -a "Visual Studio Code" .
```

Open one file:

```bash
open -a "Visual Studio Code" \
  docs/setup-guide.md
```

---

## Python Command Not Found

Try:

```bash
python3 --version
```

Create the environment using:

```bash
python3 -m venv .venv
```

After activation, use:

```bash
python
```

---

## Port Already in Use

Check port `8000`:

```bash
lsof -i :8000
```

Check port `3000`:

```bash
lsof -i :3000
```

Stop only the process you recognize.

---

# Windows PowerShell Reference

The main development instructions use macOS/Linux shell syntax.

Equivalent Windows virtual-environment activation:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
```

Copy an environment example:

```powershell
Copy-Item .env.example .env
```

Clear Next.js output:

```powershell
Remove-Item -Recurse -Force .next
Remove-Item -Force tsconfig.tsbuildinfo -ErrorAction SilentlyContinue
```

All application behavior and validation requirements remain the same across operating systems.

---

# Git Safety Checks

Before committing:

```bash
cd ~/stsp-capstone

git status --short
git diff --check
git diff --stat
```

Confirm these are not staged or committed:

```text
frontend/node_modules/
frontend/.next/
frontend/.env.local
backend/.venv/
backend/.env
node_modules/
supabase/.temp/
__pycache__/
.pytest_cache/
*.pyc
```

Safe example files may be committed:

```text
frontend/.env.example
backend/.env.example
```

Never commit:

- Supabase secret keys
- Database passwords
- Processor internal keys
- Supabase access tokens
- Gemini API keys
- Signed Storage URLs
- Real student data

---

# Complete Validation Before Commit

## Root and Database

```bash
cd ~/stsp-capstone

git diff --check

npx supabase migration list --linked

npx supabase db push \
  --linked \
  --dry-run
```

Expected:

```text
Remote database is up to date.
```

## Backend

```bash
cd ~/stsp-capstone/backend

source .venv/bin/activate

python -m compileall app
python -m pytest
python -m pip check
```

## Frontend

```bash
cd ~/stsp-capstone/frontend

rm -rf .next
rm -f tsconfig.tsbuildinfo

npx next typegen
npm run lint
npx tsc --noEmit
npm run build
```

All checks must pass before Phase 3 is considered complete.

---

# Documentation References

Additional technical details are stored in:

```text
docs/ARCHITECTURE.md
docs/api-contracts.md
docs/authentication.md
docs/database.md
docs/git-workflow.md
docs/PROJECT_FILE_MAP.md
docs/testing-checklist.md
```

Update the relevant documents whenever:

- A new table is created
- A new migration is applied
- An endpoint changes
- An environment variable changes
- A worker option changes
- A file is added or moved
- A major architecture connection changes