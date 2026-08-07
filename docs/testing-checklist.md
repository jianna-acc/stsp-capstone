<!-- File: /docs/testing-checklist.md -->
<!-- Purpose: Tracks required automated, manual, security, regression, and release checks. -->

# Testing Checklist

A feature is complete only when its functionality, errors, security boundaries, and regressions have been tested.

---

# Phase 1 — Foundation

- [x] Git repository configured
- [x] Feature-branch workflow established
- [x] Next.js frontend runs
- [x] Mantine UI loads
- [x] FastAPI runs
- [x] `/api/health` returns `200`
- [x] CORS configured
- [x] Supabase foundation configured
- [x] Frontend lint passes
- [x] Frontend TypeScript passes
- [x] Frontend build passes
- [x] Backend tests pass

---

# Authentication

- [x] Registration works
- [x] Registration validation works
- [x] Profile is created for new user
- [x] Email confirmation works
- [x] Password login works
- [x] Invalid credentials produce safe feedback
- [x] Session survives refresh
- [x] Logout works
- [x] Unauthenticated protected access redirects to login
- [x] Session proxy works
- [x] Backend secret is not exposed to browser code

---

# Phase 2 — Learning Profile

- [x] Learning-profile tables exist
- [x] RLS enabled
- [x] General preferences save
- [x] Strong subjects save
- [x] Weak subjects save
- [x] Confidence levels save
- [x] Availability saves
- [x] Invalid availability is rejected
- [x] Onboarding completion validates required data
- [x] Completed onboarding permits protected application access
- [x] Required-data changes reset completion when required

---

# Phase 3 — Subjects and Files

## Subjects

- [x] Subject creation works
- [x] Subject editing works
- [x] Subject deletion works
- [x] Subject RLS works
- [x] Missing/unowned subjects fail safely

## Uploads

- [x] PDF accepted
- [x] TXT accepted
- [x] PPT accepted for storage
- [x] PPTX accepted
- [x] XLS accepted
- [x] XLSX accepted
- [x] JPEG accepted for storage
- [x] PNG accepted for storage
- [x] WebP accepted for storage
- [x] Unsupported formats rejected
- [x] Files over 20 MB rejected
- [x] Upload progress displays
- [x] Failed upload is recorded safely

## Processing

- [x] Queue RPC works
- [x] Atomic job claim works
- [x] `SKIP LOCKED` prevents duplicate claims
- [x] Worker processes queued jobs
- [x] PDF extraction works
- [x] TXT extraction works
- [x] PPTX extraction works
- [x] XLSX extraction works
- [x] XLS extraction works
- [x] Source locators are preserved
- [x] Failed processing is recorded
- [x] Stale processing recovery works
- [x] Automatic frontend status refresh works
- [x] Preview works
- [x] Download works
- [x] Delete works
- [x] Failed upload retry works

---

# Phase 4 — AI Preparation and Vector Indexing

- [x] AI configuration validation works
- [x] Provider-independent generation contract works
- [x] Provider-independent embedding contract works
- [x] Gemini provider has offline unit tests
- [x] Normal tests do not call live Gemini
- [x] Deterministic text chunking works
- [x] Chunk overlap validation works
- [x] Embedding batches preserve ordering
- [x] AI preparation integrates with file processing
- [x] Vector migration exists
- [x] pgvector enabled
- [x] `study_file_ai_chunks` exists
- [x] Vector dimensions validated
- [x] Vector persistence RPC works
- [x] HNSW vector index exists
- [x] Vector RLS exists
- [x] Vector indexing integrates with worker
- [x] Controlled vector-indexing failures work

---

# Phase 5A–5C — Retrieval

- [x] Query embedding uses retrieval-query task type
- [x] Query vectors validated
- [x] Retrieval request contracts validated
- [x] Subject filter validated
- [x] Study-file filter validated
- [x] Owned vector search implemented
- [x] Similarity threshold supported
- [x] Match limit supported
- [x] No-context retrieval supported
- [x] Retrieval orchestration tested
- [x] Unowned resources rejected

---

# Phase 5D — Grounded Answer Generation

- [x] Grounded prompt created
- [x] Retrieved sources become factual context
- [x] No-context result supported
- [x] Source numbering validated
- [x] Citation markers validated
- [x] Provider failures converted to safe errors
- [x] Grounded answer tests use fake providers

---

# Phase 5E — Protected RAG API

- [x] `POST /api/rag/answer` registered
- [x] Missing bearer token rejected
- [x] Invalid token rejected
- [x] Authenticated user derived from token
- [x] Request cannot override `user_id`
- [x] Subject ownership validated
- [x] Study-file ownership validated
- [x] Controlled upstream failures mapped safely
- [x] No raw provider traceback returned
- [x] No access token returned
- [x] No raw vectors returned

---

# Phase 5F — Study Assistant Frontend

## API Client

- [x] Supabase session required
- [x] Bearer token sent to FastAPI
- [x] Subject filter serialized correctly
- [x] Study-file filter serialized correctly
- [x] Successful response validated
- [x] No-context response validated
- [x] Malformed response rejected
- [x] Backend errors displayed safely
- [x] Network errors do not expose credentials

## UI

- [x] `/study-assistant` protected
- [x] Study Assistant navigation exists
- [x] Subject options load
- [x] Ready study files load
- [x] Selecting file selects related subject
- [x] Incompatible file is cleared after subject change
- [x] Question submission works
- [x] Loading state works
- [x] Grounded answer renders
- [x] Sources render
- [x] No-context result renders
- [x] Safe API errors render
- [x] Responsive layout works

---

# Phase 5G — Conversation Database

- [x] `study_conversations` exists
- [x] `study_messages` exists
- [x] Conversation ownership foreign key exists
- [x] Message deletion cascades with conversation deletion
- [x] Conversation filter ownership validated
- [x] Conversation RLS enabled
- [x] Message RLS enabled
- [x] Anonymous access revoked
- [x] Assistant messages require valid outcome
- [x] User messages reject assistant outcomes
- [x] Saved source metadata is limited to safe fields
- [x] Summary maximum is 4,000 characters
- [x] Summary count cannot be negative
- [x] Summary-state consistency enforced
- [x] Authenticated clients cannot update internal summary state
- [x] Service role can perform backend summary updates
- [x] Phase 5G migrations synchronized
- [x] Linked database dry run reports no pending migrations
- [x] Generated database types include conversation fields

---

# Phase 5G — Conversation API

- [x] Conversation create route registered
- [x] Conversation list route registered
- [x] Conversation detail route registered
- [x] Conversation update route registered
- [x] Conversation delete route registered
- [x] Conversation routes require authentication
- [x] List returns only owned conversations
- [x] Detail requires ownership
- [x] Update requires ownership
- [x] Delete requires ownership
- [x] Missing conversation returns controlled error
- [x] Unowned conversation returns controlled error
- [x] Conversation client does not send raw `user_id`
- [x] Delete client handles `204 No Content`

---

# Phase 5G — RAG Persistence

- [x] RAG request accepts optional `conversation_id`
- [x] RAG response requires `conversation_id`
- [x] First question creates conversation
- [x] Current user message saved
- [x] Assistant answer saved
- [x] No-context answer saved
- [x] Existing conversation ownership checked
- [x] Conflicting saved/requested filters rejected
- [x] Source metadata persisted safely

---

# Phase 5G — Bounded Memory

- [x] Memory supports only user/assistant roles
- [x] Memory limited to 10 items
- [x] Memory limited to 8,000 characters
- [x] Recent messages ordered chronologically
- [x] Current question not duplicated in prior memory
- [x] Memory remains backend-internal
- [x] Client cannot submit arbitrary memory
- [x] Memory reaches grounded generation
- [x] Memory does not reach vector retrieval
- [x] Conversation history identified as non-evidence
- [x] Study-material retrieval remains factual evidence

---

# Phase 5G — Deterministic Summary

- [x] Summary does not call Gemini
- [x] Summary does not call another AI provider
- [x] User/assistant entries labeled
- [x] Citation markers removed
- [x] Individual entries bounded
- [x] Complete summary bounded to 4,000 characters
- [x] Newest summary entries preserved
- [x] Output deterministic
- [x] Summary version validated
- [x] Cross-conversation messages rejected
- [x] Summary uses one memory slot
- [x] Nine messages remain with summary
- [x] Ten messages remain without summary
- [x] Summary refresh occurs before saving current question
- [x] Already summarized messages are not summarized twice

---

# Phase 5G — Frontend Conversation API

- [x] Typed conversation contracts exist
- [x] List API works
- [x] Detail API works
- [x] Rename API works
- [x] Delete API works
- [x] Authentication required
- [x] Error responses validated
- [x] Malformed responses rejected
- [x] Network errors do not expose access token

---

# Phase 5G — Conversation History UI

- [x] Loading state implemented
- [x] Empty state implemented
- [x] Error state implemented
- [x] Retry implemented
- [x] Conversation selection implemented
- [x] Selected conversation highlighted
- [x] New conversation implemented
- [x] Selected detail loads
- [x] Saved messages load
- [x] Saved subject filter restored
- [x] Saved study-file filter restored
- [x] Follow-up sends selected `conversation_id`
- [x] Successful answer clears question input
- [x] Conversation detail refreshes after answer
- [x] Conversation history refreshes after answer
- [x] Conversation requests are aborted safely when switching

---

# Phase 5G — Backend Regression

- [x] Full pytest suite passes
- [x] Full Ruff validation passes
- [x] Backend compilation passes
- [x] Focused conversation/RAG regression passes
- [x] Migration contract tests pass
- [x] Repository tests pass
- [x] RAG endpoint regression passes

---

# Phase 5G — Frontend Regression

The full frontend regression passed before the final conversation-history layout spacing adjustment.

- [x] Full frontend test suite passed
- [x] TypeScript validation passed
- [x] ESLint passed
- [x] Production build passed

Because the Study Assistant CSS layout was adjusted afterward, perform the final post-layout validation before the commit:

- [ ] Re-run `npm run lint`
- [ ] Re-run `npx tsc --noEmit`
- [ ] Re-run `npm run build`
- [ ] Visually confirm history/assistant spacing on desktop
- [ ] Visually confirm stacked mobile layout

---

# Phase 5G — Security

- [x] Conversation ownership comes from bearer authentication
- [x] Request cannot override user ID
- [x] Request cannot submit memory
- [x] Request cannot submit summary state
- [x] Frontend does not use internal summary state
- [x] Frontend does not directly query conversation tables
- [x] Backend service role remains server-side
- [x] Conversation history cannot replace retrieved evidence
- [x] Sources exclude raw vectors
- [x] Sources exclude complete retrieved chunks
- [x] API errors do not expose credentials
- [x] Network errors do not expose access tokens

---

# Final Documentation Checks

After replacing the documentation files:

- [ ] `ARCHITECTURE.md` reflects Phase 5G
- [ ] `api-contracts.md` reflects RAG and conversation endpoints
- [ ] `authentication.md` reflects implemented authentication
- [ ] `database.md` includes vector and conversation tables
- [ ] `PROJECT_FILE_MAP.md` includes Phase 4/5 files
- [ ] `setup-guide.md` reflects current application
- [ ] `testing-checklist.md` reflects Phase 5G
- [ ] Mermaid code fences are paired
- [ ] No stale Phase 4 `Planned` labels remain
- [ ] No duplicate planned `chat_*` tables remain
- [ ] No real secrets appear
- [ ] `git diff --check` passes

---

# Final Database Checks

```powershell
npx supabase migration list --linked

npx supabase db push --linked --dry-run
```

Confirm:

- [ ] Local and remote migration histories match
- [ ] Remote database is up to date
- [ ] Generated database types match hosted schema

---

# Final Backend Checks

```powershell
Set-Location ".\backend"

python -m pytest -q

python -m ruff check `
    app `
    tests `
    scripts

python -m compileall `
    -q `
    app `
    tests `
    scripts

python -m pip check
```

Confirm:

- [ ] All commands pass after final documentation/UI changes

---

# Final Frontend Checks

```powershell
Set-Location ".\frontend"

npm test

npx tsc --noEmit

npm run lint

npm run build
```

Confirm:

- [ ] All tests pass
- [ ] TypeScript passes
- [ ] ESLint passes
- [ ] Production build passes

---

# Final Git Safety

From repository root:

```powershell
git branch --show-current

git status --short --untracked-files=all

git diff --check

git diff --stat
```

Confirm:

- [ ] Correct feature branch
- [ ] No unexpected files
- [ ] `backend/.env` not tracked
- [ ] `frontend/.env.local` not tracked
- [ ] `.venv` not tracked
- [ ] `node_modules` not tracked
- [ ] `.next` not tracked
- [ ] `.pytest_cache` not tracked
- [ ] `__pycache__` not tracked
- [ ] Supabase temporary files not tracked
- [ ] No secret values in diff
- [ ] Only intended Phase 5G files are staged

---

# Phase 5G Completion Record

```text
Phase: Phase 5G — Conversation Persistence, Memory, Summary, and History UI

Branch: phase5/conversation-memory-summary

Database migrations synchronized:
Backend tests passed:
Backend Ruff passed:
Backend compile passed:

Frontend tests passed:
Frontend TypeScript passed:
Frontend lint passed:
Frontend build passed:

Conversation history browser test passed:
Conversation switching passed:
Conversation continuation passed:
Responsive layout passed:

Security review passed:
Documentation review passed:
Git scope review passed:

Ready to commit:
Ready to push:

Completion date:
Reviewed by:
```

---

# Bug Report Template

```text
Title:
Feature:
Branch:
Steps to reproduce:
Expected result:
Actual result:
Error message:
Relevant terminal output:
Screenshot:
Browser or device:
Priority:
Assigned member:
```