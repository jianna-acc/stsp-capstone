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

# Phase 6A — Reviewer Backend Foundation

## Database and Security

- [x] Effective `reviewers` foundation migration created and applied
- [x] `public.reviewers` verified remotely with 14 columns
- [x] Reviewer table verified with 2 RLS policies
- [x] Reviewer table verified with 2 application triggers
- [x] Local and remote migration histories include `20260808053929`
- [x] Reviewer ownership references authenticated users
- [x] Reviewer subject/file scope constraints are enforced
- [x] Reviewer RLS policies are defined
- [x] Browser clients cannot directly insert or update reviewer records

## Reviewer Source Loading

- [x] File-scope reviewer loads one owned ready study file
- [x] Subject-scope reviewer loads owned ready files for the subject
- [x] Reviewer generation uses `study_file_chunks`
- [x] Source chunks are ordered deterministically
- [x] Missing or incomplete chunk sequences fail safely
- [x] Reviewer sources preserve file/chunk locator metadata

## Reviewer Generation

- [x] Reviewer supports `short`, `medium`, and `long`
- [x] Generated content includes overview, topics, key points, and definitions
- [x] Generation is grounded only in supplied study material
- [x] Study-material text is treated as untrusted prompt content
- [x] Malformed model output receives one controlled repair attempt
- [x] Reviewer generation uses reviewer-specific output-token budgets
- [x] Oversized source collections fail safely instead of silently dropping content

## Reviewer Persistence

- [x] Generated reviewers can be saved
- [x] Saved reviewers can be listed
- [x] One owned reviewer can be retrieved
- [x] One owned reviewer can be deleted
- [x] Reviewer operations remain scoped to the authenticated user

## Reviewer API

- [x] `POST /api/reviewers/generate` registered
- [x] `GET /api/reviewers` registered
- [x] `GET /api/reviewers/{reviewer_id}` registered
- [x] `DELETE /api/reviewers/{reviewer_id}` registered
- [x] Reviewer API does not accept trusted `user_id`
- [x] Controlled reviewer errors use safe public responses
- [x] Successful delete returns `204 No Content`

## Reviewer Automated Validation

- [x] Reviewer migration tests pass
- [x] Reviewer schema tests pass
- [x] Reviewer repository tests pass
- [x] Reviewer service tests pass
- [x] Reviewer source-loader tests pass
- [x] Reviewer Supabase-admin tests pass
- [x] Reviewer prompt tests pass
- [x] Reviewer generation tests pass
- [x] Reviewer orchestration tests pass
- [x] Reviewer API endpoint tests pass
- [x] Focused reviewer regression passes
- [x] Reviewer Ruff validation passes
- [x] Reviewer application modules compile successfully
- [x] `git diff --check` passes

## Deferred Beyond Phase 6A

- [x] Reviewer frontend UI — implemented in Phase 6B
- [ ] Reviewer saved-history and reopening UI
- [ ] Reviewer regeneration
- [ ] Multi-pass generation for very large source collections
- [ ] Quiz generation

---

# Phase 6B — Reviewer Frontend

## Reviewer API Client

- [x] Authenticated Supabase session required
- [x] Bearer token sent to Reviewer FastAPI endpoint
- [x] Reviewer request serialized correctly
- [x] File-scope request supported
- [x] Subject-scope request supported
- [x] Successful reviewer response validated
- [x] Malformed successful response rejected
- [x] Inconsistent scope response rejected
- [x] Controlled backend errors displayed safely
- [x] Network errors do not expose access tokens

## Reviewer Filter Options

- [x] Authenticated subjects load
- [x] Ready study files load
- [x] Study files remain scoped to authenticated user
- [x] Only `processing_status = ready` files are selectable
- [x] Filter-loading failures disable generation safely

## Reviewer Generation UI

- [x] `/reviewers` protected route exists
- [x] Reviewer navigation entry exists
- [x] Whole-subject scope supported
- [x] Single-study-material scope supported
- [x] Subject selection required
- [x] File selection required for file scope
- [x] File options filter by selected subject
- [x] Changing subject clears incompatible selected file
- [x] Short reviewer selectable
- [x] Medium reviewer selectable
- [x] Long reviewer selectable
- [x] Loading state displayed
- [x] Safe API error state displayed
- [x] Successful generation state displayed

## Reviewer Result UI

- [x] Reviewer title renders
- [x] Scope badge renders
- [x] Length badge renders
- [x] Overview renders
- [x] Topic summaries render
- [x] Key points render
- [x] Definitions render when available
- [x] Source files render
- [x] Source locator labels render
- [x] Missing locator label uses safe section fallback

## Live Integration

- [x] Single study material + Medium generation succeeded
- [x] Whole subject + Medium generation succeeded
- [x] Whole subject generation combined 3 ready files
- [x] Whole subject + Short generation succeeded after output-budget fix
- [x] Generated reviewer persisted successfully
- [x] Generated reviewer displayed successfully
- [x] Final Short whole-subject request returned `201 Created`
- [x] Final Short whole-subject request produced valid JSON on first generation attempt

## Reviewer Generation Robustness

- [x] Malformed AI JSON detected
- [x] One bounded repair attempt retained
- [x] Short reviewer output budget increased from 2,048 to 4,096 tokens
- [x] Short prompt remains concise despite larger maximum output budget
- [x] Medium output budget remains 4,096 tokens
- [x] Long output budget remains 6,144 tokens

## Phase 6B Automated Validation

- [x] Reviewer API tests: 7 passed
- [x] Reviewer option-loader tests: 3 passed
- [x] Reviewer generation-form tests: 6 passed
- [x] Reviewer result tests: 4 passed
- [x] Reviewer workspace tests: 2 passed
- [x] Full frontend suite: 54 passed
- [x] Full backend suite: 700 passed
- [x] Backend Ruff validation passes
- [x] Backend compilation passes
- [x] Frontend TypeScript validation passes
- [x] Frontend production build passes
- [x] Frontend ESLint has 0 errors
- [x] Existing unrelated subject-page ESLint warning remains documented
- [x] `git diff --check` passes

## Deferred Beyond Phase 6B

- [ ] Saved reviewer history UI
- [ ] Open previously saved reviewer
- [ ] Reviewer deletion UI
- [ ] Reviewer regeneration
- [ ] Multi-pass generation for source collections above the single-pass limit
- [ ] Quiz generation

````markdown
---

# Track A — Flashcard Backend

## Database and Security

- [x] `flashcard_decks` foundation migration created
- [x] `flashcards` child table created
- [x] Flashcard foundation migration applied to linked Supabase
- [x] Atomic Flashcard persistence RPC migration created and applied
- [x] Flashcard deck ownership references authenticated users
- [x] File/subject scope constraints are database enforced
- [x] Requested card count is database bounded
- [x] Flashcard text constraints are database enforced
- [x] Flashcard deck and card tables use RLS
- [x] Browser clients cannot directly insert generated Flashcard data
- [x] Students can read only cards belonging to owned decks
- [x] Trusted Flashcard creation RPC is restricted to `service_role`
- [x] Deck deletion cascades to child Flashcards

## Flashcard Source Loading

- [x] File scope loads one owned ready study file
- [x] Subject scope loads owned ready study files within one subject
- [x] Flashcard generation uses `study_file_chunks`
- [x] Source chunks remain deterministically ordered
- [x] Missing chunk collections fail safely
- [x] Non-contiguous chunk sequences fail safely
- [x] Source/file ownership mismatches fail safely
- [x] Flashcard sources preserve safe file/chunk locator metadata

## Flashcard AI Generation

- [x] Flashcard requests support 5 to 50 cards
- [x] Default Flashcard count is 20
- [x] Generation is grounded only in supplied study material
- [x] Study-material text is treated as untrusted prompt content
- [x] Flashcard prompt requires JSON-only output
- [x] Generated output must contain exactly the requested card count
- [x] Duplicate Flashcards are rejected
- [x] Malformed generated output receives one controlled repair attempt
- [x] Provider identity is validated
- [x] Standard Flashcard generation uses a 4,096-token output budget
- [x] Larger Flashcard requests use an 8,192-token output budget
- [x] Source material above the current 80,000-character single-pass limit fails safely
- [x] Source material is never silently truncated

## Flashcard Persistence

- [x] Deck and child cards are created atomically
- [x] Generated Flashcards can be saved
- [x] Saved decks can be listed
- [x] Saved decks can be filtered by subject
- [x] One owned saved deck can be retrieved
- [x] One owned saved deck can be deleted
- [x] Persistence operations remain scoped to the authenticated student
- [x] Public deck responses do not expose `user_id`

## Flashcard API

- [x] `POST /api/flashcards/generate` registered
- [x] `GET /api/flashcards` registered
- [x] `GET /api/flashcards/{deck_id}` registered
- [x] `DELETE /api/flashcards/{deck_id}` registered
- [x] Real FastAPI OpenAPI schema exposes Flashcard paths
- [x] Flashcard API derives owner identity from authentication
- [x] Flashcard API does not accept trusted `user_id`
- [x] Invalid card counts are rejected by request validation
- [x] Controlled Flashcard errors use safe public responses
- [x] Successful deletion returns `204 No Content`
- [x] Existing Reviewer API regression remains green

## Flashcard Automated Validation

- [x] Flashcard schema tests pass
- [x] Flashcard migration tests pass
- [x] Flashcard persistence RPC migration tests pass
- [x] Flashcard repository tests pass
- [x] Flashcard persistence-service tests pass
- [x] Flashcard source-loader tests pass
- [x] Flashcard prompt tests pass
- [x] Flashcard generation tests pass
- [x] Flashcard orchestration tests pass
- [x] Flashcard API endpoint tests pass
- [x] Flashcard router/OpenAPI registration tests pass
- [x] Full backend regression passes after protected Flashcard API integration
- [x] Flashcard Ruff validation passes
- [x] `git diff --check` passes

## Deferred Beyond Current Track A Backend

- [ ] Student-facing Flashcard page
- [ ] Authenticated frontend Flashcard API client
- [ ] Flashcard generation form
- [ ] Interactive card flip/study interface
- [ ] Saved-deck management UI
- [ ] Multi-pass generation for materials above the current single-pass source limit

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
- [x] `ARCHITECTURE.md` reflects Phase 6A reviewer backend
- [x] `PROJECT_FILE_MAP.md` includes Phase 6A files
- [x] `api-contracts.md` includes reviewer endpoints
- [x] `database.md` includes the implemented `reviewers` table
- [x] `testing-checklist.md` includes Phase 6A validation
- [x] `ARCHITECTURE.md` reflects Phase 6B Reviewer frontend
- [x] `PROJECT_FILE_MAP.md` includes Phase 6B Reviewer frontend files
- [x] `testing-checklist.md` includes Phase 6B automated and live validation
- [x] Reviewer API contracts remain current
- [x] `ARCHITECTURE.md` reflects implemented Track A Flashcard backend
- [x] `PROJECT_FILE_MAP.md` includes Track A Flashcard backend files
- [x] `api-contracts.md` includes protected Flashcard endpoints
- [x] `database.md` includes `flashcard_decks`, `flashcards`, and the trusted persistence RPC
- [x] `testing-checklist.md` includes Track A Flashcard backend validation

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