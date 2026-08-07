<!-- File: /docs/setup-guide.md -->
<!-- Purpose: Explains how to install, configure, run, and validate STUDY AI through Phase 5G. -->

# Development Setup Guide

STUDY AI currently uses:

- Next.js
- TypeScript
- Mantine
- FastAPI
- Python 3.12
- Supabase Auth
- Supabase PostgreSQL
- Private Supabase Storage
- pgvector
- Gemini generation and embeddings
- Vitest
- pytest
- Ruff

---

# Required Software

Install:

- Git
- Visual Studio Code
- Node.js 20.9+
- npm
- Python 3.12
- Web browser
- Supabase account/project access
- Gemini API credentials for live AI execution

Verified development versions include:

```text
Node.js: v22.15.0
npm: 11.16.0
Next.js: 16.2.10
Python: 3.12
```

---

# Clone Repository

```powershell
git clone <repository-url>
Set-Location ".\stsp-capstone"
```

Check:

```powershell
git status
git branch --show-current
```

Use a feature branch for development.

---

# Install Root Tooling

```powershell
npm install
```

Verify Supabase CLI:

```powershell
npx supabase --version
```

---

# Frontend Setup

```powershell
Set-Location ".\frontend"

npm install
```

Create:

```text
frontend/.env.local
```

from:

```text
frontend/.env.example
```

Important browser-safe variables:

```env
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
```

Never put backend secrets in a `NEXT_PUBLIC_` variable.

---

# Backend Setup

From repository root:

```powershell
Set-Location ".\backend"

py -3.12 -m venv .venv

.\.venv\Scripts\Activate.ps1
```

Install:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

Expected:

```text
No broken requirements found.
```

---

# Backend Environment

Create:

```text
backend/.env
```

from:

```text
backend/.env.example
```

Important private settings include:

```env
APP_NAME=STS Capstone API
ENVIRONMENT=development
API_PREFIX=/api
FRONTEND_URL=http://localhost:3000

SUPABASE_URL=
SUPABASE_SECRET_KEY=
PROCESSOR_INTERNAL_KEY=
STUDY_MATERIALS_BUCKET=study-materials

GEMINI_API_KEY=

AI_LIVE_SMOKE_TESTS_ENABLED=false
```

Use the remaining AI and processing settings already documented in `.env.example`.

Never display or commit real secret values.

---

# Hosted Supabase Workflow

The project uses hosted Supabase.

Docker-based local Supabase is not required.

Authenticate:

```powershell
Set-Location ".."

npx supabase login
```

Link if needed:

```powershell
npx supabase link --project-ref YOUR_PROJECT_REFERENCE
```

Check migration history:

```powershell
npx supabase migration list --linked
```

Dry-run:

```powershell
npx supabase db push --linked --dry-run
```

Expected when synchronized:

```text
Remote database is up to date.
```

---

# Applying a Migration

Create:

```powershell
npx supabase migration new descriptive_name
```

Validate:

```powershell
git diff --check

npx supabase db push --linked --dry-run
```

Apply:

```powershell
npx supabase db push --linked
```

Verify:

```powershell
npx supabase migration list --linked

npx supabase db push --linked --dry-run
```

Never edit an already applied migration.

---

# Generate Database Types

```powershell
npx supabase gen types typescript `
    --linked `
    --schema public |
    Set-Content `
        ".\frontend\types\database.ts"
```

Do not manually edit generated database types.

---

# Run the Application

Three processes are normally used during full development.

---

## Terminal 1 — Frontend

```powershell
Set-Location ".\frontend"

npm run dev
```

Open:

```text
http://localhost:3000
```

---

## Terminal 2 — FastAPI

```powershell
Set-Location ".\backend"

.\.venv\Scripts\Activate.ps1

python -m uvicorn app.main:app `
    --reload `
    --host 127.0.0.1 `
    --port 8000
```

Health:

```text
http://127.0.0.1:8000/api/health
```

OpenAPI:

```text
http://127.0.0.1:8000/docs
```

---

## Terminal 3 — Processing Worker

```powershell
Set-Location ".\backend"

.\.venv\Scripts\Activate.ps1

python -m app.workers.file_processing_worker `
    --poll-seconds 2 `
    --recovery-interval-seconds 30 `
    --stale-after-minutes 30 `
    --max-attempts 3
```

The worker is required when processing new uploaded files.

---

# File Processing

Expected status flow:

```text
Uploading
→ Queued
→ Reading
→ Indexing
→ Ready
```

Possible terminal failure:

```text
Failed
```

Supported text extraction:

```text
PDF
TXT
PPTX
XLSX
XLS
```

Accepted storage formats also include:

```text
PPT
JPEG
PNG
WebP
```

OCR is not currently implemented.

---

# Vector Indexing

After extraction:

```text
Extracted text
→ AI chunks
→ embedding batches
→ Gemini embeddings
→ validation
→ study_file_ai_chunks
```

Vectors use:

```text
768 dimensions
cosine similarity
HNSW indexing
```

---

# Study Assistant

Protected route:

```text
/study-assistant
```

The assistant can:

- Search all ready materials
- Filter by subject
- Filter by study material
- Return grounded answers
- Show citations
- Return no-context results
- Save conversations
- Load conversation history
- Continue saved conversations

---

# Study Assistant API

Backend endpoint:

```text
POST /api/rag/answer
```

The frontend sends the Supabase access token using bearer authentication.

For an existing thread it also sends:

```text
conversation_id
```

---

# Conversation API

Implemented routes:

```text
POST   /api/study-conversations
GET    /api/study-conversations
GET    /api/study-conversations/{conversation_id}
PATCH  /api/study-conversations/{conversation_id}
DELETE /api/study-conversations/{conversation_id}
```

---

# Frontend Validation

Run:

```powershell
Set-Location ".\frontend"

npm test
```

Then:

```powershell
npx tsc --noEmit
```

Then:

```powershell
npm run lint
```

Then:

```powershell
npm run build
```

All must pass before committing.

After any final CSS/layout change, rerun at least:

```powershell
npm run lint
npx tsc --noEmit
npm run build
```

---

# Backend Validation

```powershell
Set-Location ".\backend"

.\.venv\Scripts\Activate.ps1

python -m pytest -q
```

Ruff:

```powershell
python -m ruff check `
    app `
    tests `
    scripts
```

Compilation:

```powershell
python -m compileall `
    -q `
    app `
    tests `
    scripts
```

Dependency check:

```powershell
python -m pip check
```

---

# Git Validation

From repository root:

```powershell
git diff --check

git status --short --untracked-files=all

git diff --stat
```

Before staging, verify that no unexpected files are present.

---

# Secret Safety

Never commit:

```text
frontend/.env.local
backend/.env
backend/.venv
frontend/.next
node_modules
supabase/.temp
__pycache__
.pytest_cache
```

Never expose:

- Supabase secret key
- Database password
- Gemini API key
- Processor internal key
- Access tokens
- Signed private URLs
- Real student information

---

# Phase 5G Database Resources

```text
public.study_conversations
public.study_messages
```

Phase 5G migrations:

```text
20260806192800_create_study_conversations_and_messages.sql
20260806200500_fix_study_message_outcome_constraint.sql
20260806223000_add_study_conversation_summary_state.sql
20260806234000_restrict_study_conversation_summary_updates.sql
```

---

# Full Validation Before Commit

From the root:

```powershell
git diff --check

npx supabase migration list --linked

npx supabase db push --linked --dry-run
```

Backend:

```powershell
Set-Location ".\backend"

.\.venv\Scripts\Activate.ps1

python -m pytest -q
python -m ruff check app tests scripts
python -m compileall -q app tests scripts
python -m pip check
```

Frontend:

```powershell
Set-Location "..\frontend"

npm test
npx tsc --noEmit
npm run lint
npm run build
```

Return to root:

```powershell
Set-Location ".."

git diff --check
git status --short --untracked-files=all
```

Do not stage or push until every expected check passes.

---

# Documentation

Technical references:

```text
docs/ARCHITECTURE.md
docs/api-contracts.md
docs/authentication.md
docs/database.md
docs/PROJECT_FILE_MAP.md
docs/testing-checklist.md
docs/AI_PROVIDER.md
docs/AI_PREPARATION_PIPELINE.md
docs/AI_VECTOR_PIPELINE.md
```

Update documentation whenever implementation changes.