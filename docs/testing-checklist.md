<!-- File: /docs/testing-checklist.md -->
<!-- Purpose: Tracks automated, manual, security, and regression tests required before a project phase is considered complete. -->

# Testing Checklist

A feature is not complete only because its page appears correctly.

A completed feature must also handle:

- Loading
- Success
- Empty data
- Invalid input
- Errors
- Retry behavior
- Mobile layout
- Authentication
- Authorization
- Database consistency
- Security boundaries
- Automated validation
- Regression testing

A checked item means the test has already been completed successfully.

An unchecked item must be completed before the related phase is merged.

---

# Phase 1 Repository Tests

- [x] Local Git repository exists
- [x] GitHub remote is connected
- [x] `main` branch exists
- [x] `development` branch exists
- [x] Initial project commit is pushed
- [x] Feature branches are used for active development
- [x] Generated environment folders are ignored
- [x] Private environment files are ignored
- [x] Git workflow is documented

---

# Documentation Tests

- [x] Root README exists
- [x] Project file map exists
- [x] Architecture document exists
- [x] Setup guide exists
- [x] API contracts document exists
- [x] Database document exists
- [x] Authentication document exists
- [x] Git workflow document exists
- [x] Testing checklist exists
- [ ] Every Mermaid diagram renders correctly
- [ ] Every documented file path exists
- [ ] Every documented command matches the current operating system
- [ ] No outdated `Planned` labels remain for implemented features
- [ ] No secrets appear in documentation
- [ ] `git diff --check` passes after all documentation edits

---

# Frontend Foundation Tests

- [x] Supported Node.js version is installed
- [x] Next.js project installs successfully
- [x] `npm run dev` starts
- [x] Home page opens
- [x] CSS Modules work
- [x] Tailwind is not used as the main styling system
- [x] Mantine styles load
- [x] Custom application theme is applied
- [x] Tabler icons display
- [x] Mantine notifications work
- [x] Confirmation modals work
- [x] Responsive card layout works
- [x] Buttons stack correctly on narrow screens
- [x] Browser console has no foundation errors
- [x] `npm run lint` passes
- [x] `npx tsc --noEmit` passes
- [x] `npm run build` passes

---

# Backend Foundation Tests

- [x] Python virtual environment is created
- [x] Python virtual environment activates
- [x] Locked dependencies install
- [x] `python -m pip check` reports no broken requirements
- [x] Typed environment settings load
- [x] Private `.env` is ignored by Git
- [x] FastAPI application imports successfully
- [x] FastAPI starts on port `8000`
- [x] `/docs` opens
- [x] `/openapi.json` opens
- [x] CORS permits `http://localhost:3000`
- [x] `/api/health` returns `200`
- [x] Health response matches its schema
- [x] Swagger displays the health endpoint
- [x] Backend tests pass

---

# Frontend-to-Backend Health Integration Tests

- [x] Frontend `.env.example` documents the backend base URL
- [x] Frontend `.env.local` is ignored by Git
- [x] `NEXT_PUBLIC_API_BASE_URL` loads correctly
- [x] Frontend API response types compile
- [x] API service validates the health response
- [x] API service handles missing configuration
- [x] API service handles connection failures
- [x] API request timeout is implemented
- [x] Health component displays the idle state
- [x] Health component displays the loading state
- [x] Health component displays the connected state
- [x] Health component displays all response fields
- [x] Health component displays the unavailable state
- [x] Retry reconnects after FastAPI restarts
- [x] Check again sends another successful request
- [x] Backend receives `GET /api/health`
- [x] Browser receives `200 OK`
- [x] CORS allows the frontend origin
- [x] Component remains usable after a failed request
- [x] Browser console has no unexpected errors
- [x] Frontend terminal has no compilation errors
- [x] Backend terminal has no unexpected traceback

---

# Supabase Foundation Tests

- [x] Hosted Supabase development project exists
- [x] Repository is linked to the hosted project
- [x] Supabase publishable key is used by the frontend
- [x] Supabase backend secret is used only by trusted backend code
- [x] Private environment files are ignored by Git
- [x] Supabase CLI is installed as a project dependency
- [x] Migration history is available through the linked project
- [x] Linked dry-run workflow works
- [x] Generated database types are committed
- [x] Browser Supabase client uses generated database types
- [x] Server Supabase client uses generated database types
- [x] Backend trusted access is isolated from frontend code
- [ ] Final linked migration check reports the remote database is up to date
- [ ] Final generated database types match the hosted schema

---

# Profiles Foundation Tests

- [x] Profiles migration passed its dry-run preview
- [x] Profiles migration was applied successfully
- [x] Local and remote migration timestamps match
- [x] `public.profiles` exists
- [x] Row Level Security is enabled
- [x] Own-profile policies are present
- [x] Profile timestamp trigger is present
- [x] New-user profile trigger is present
- [x] Generated definitions contain `public.profiles`
- [x] Trusted backend access can reach the profile table
- [x] Frontend lint passes with generated definitions
- [x] Frontend production build passes
- [x] TypeScript validation passes
- [x] Backend dependency check passes
- [x] Backend tests pass

---

# Authentication Proxy Tests

- [x] Supabase Site URL is configured for `http://localhost:3000`
- [x] Email-confirmation redirect URL is configured
- [x] Email provider is enabled
- [x] Email confirmation is enabled
- [x] Authentication architecture is documented
- [x] Next.js root proxy exists
- [x] Supabase session utility exists
- [x] Proxy uses publishable Supabase configuration
- [x] Proxy uses generated database types
- [x] Proxy validates sessions
- [x] Proxy does not use the backend secret
- [x] Request cookies are synchronized
- [x] Response cookies are synchronized
- [x] Static assets are excluded from session matching
- [x] Repeated refreshes do not create a redirect loop
- [x] Browser console has no unexpected authentication errors

---

# Registration Tests

- [x] Public authentication layout is responsive
- [x] Registration route loads
- [x] Check-email route loads
- [x] Login route loads
- [x] Registration form uses a Server Action
- [x] Registration form uses action state
- [x] Full name is validated
- [x] Email format is validated
- [x] Password minimum length is validated
- [x] Password letter requirement is validated
- [x] Password number requirement is validated
- [x] Password confirmation is validated
- [x] Platform-rules acceptance is validated
- [x] Passwords are excluded from browser-visible action state
- [x] Registration metadata uses `full_name`
- [x] Email redirect points to `/auth/confirm`
- [x] Invalid registration does not create a Supabase user
- [x] Valid registration creates an Auth user
- [x] Profile row is created automatically
- [x] Email confirmation succeeds
- [x] Confirmed student can log in
- [x] Invalid credentials display a friendly error
- [x] Student session remains after refresh
- [x] Student can log out
- [x] Logged-out student returns to login

---

# Protected Route Tests

- [x] Unauthenticated student cannot open the dashboard
- [x] Unauthenticated student cannot open the profile page
- [x] Unauthenticated student cannot open onboarding pages
- [x] Unauthenticated student cannot open subject pages
- [x] Authenticated student can open protected pages
- [x] Incomplete onboarding redirects to onboarding
- [x] Completed onboarding permits dashboard access
- [x] Logout removes access to protected routes
- [x] Session refresh does not produce a redirect loop

---

# Phase 2 Learning-Profile Database Tests

## Tables

- [x] `public.learning_profiles` exists
- [x] `public.learning_profile_subjects` exists
- [x] `public.study_availability` exists
- [x] Generated database types include all learning-profile tables
- [x] Row Level Security is enabled on all learning-profile tables
- [x] Students can read only their own learning-profile records
- [x] Students can update only their own learning-profile records

## General Preferences

- [x] Preferred study duration saves
- [x] Preferred study times save
- [x] Study challenges save
- [x] Estimated task time saves
- [x] Preferred learning methods save
- [x] Existing values load during onboarding
- [x] Save and continue works

## Subject Strengths and Confidence

- [x] Strong subject records save
- [x] Weak subject records save
- [x] Confidence values save
- [x] Confidence values are restricted to the valid range
- [x] Replacing subject records does not create unexpected duplicates
- [x] Existing subject records reload correctly

## Study Availability

- [x] Availability periods save
- [x] ISO weekday values are validated
- [x] Start time must be earlier than end time
- [x] Overlapping periods are rejected
- [x] Existing availability records reload correctly
- [x] Replacing availability does not leave duplicate periods

## Onboarding Completion

- [x] Completion RPC validates required profile data
- [x] Completion RPC requires general preferences
- [x] Completion RPC requires study challenges
- [x] Completion RPC requires a strong subject
- [x] Completion RPC requires a weak subject
- [x] Completion RPC requires study availability
- [x] Successful completion sets `onboarding_completed`
- [x] Successful completion sets `onboarding_completed_at`
- [x] Successful completion sets the final onboarding step
- [x] Required-data edits reset onboarding completion
- [x] Required-data deletion resets onboarding completion
- [x] Database trigger notices for missing old triggers are treated as non-errors

---

# Phase 3 Subject Management Tests

- [x] `public.subjects` exists
- [x] Subject Row Level Security is enabled
- [x] Student can create a subject
- [x] Student can view owned subjects
- [x] Student can edit an owned subject
- [x] Student can delete an owned subject
- [x] Student cannot read another student's subject
- [x] Student cannot update another student's subject
- [x] Student cannot delete another student's subject
- [x] Empty subject state displays correctly
- [x] Subject validation rejects invalid names
- [x] Subject tabs display
- [x] Subject workspace route loads
- [x] Missing or unowned subject returns a safe not-found response
- [x] `/files` redirects to the subject workspace
- [x] Sidebar displays owned subjects

---

# Phase 3 Storage Tests

- [x] Private `study-materials` bucket exists
- [x] Bucket is not public
- [x] Storage upload policies exist
- [x] Storage read policies exist
- [x] Storage delete policies exist
- [x] Storage paths begin with the authenticated user's ID
- [x] Student can upload inside their own folder
- [x] Student cannot upload inside another student's folder
- [x] Student cannot read another student's object
- [x] Student cannot delete another student's object
- [x] Signed URLs are short-lived
- [x] Real signed URLs are not written to documentation
- [ ] Final two-account Storage isolation test passes

---

# Phase 3 File Upload Tests

## Accepted Files

- [x] PDF is accepted
- [x] TXT is accepted
- [x] PPT is accepted for storage
- [x] PPTX is accepted
- [x] XLS is accepted
- [x] XLSX is accepted
- [x] JPEG is accepted for storage
- [x] PNG is accepted for storage
- [x] WebP is accepted for storage
- [x] Unsupported file formats are rejected
- [x] Files larger than 20 MB are rejected
- [x] Only one file may be selected per upload
- [x] Selected filename displays
- [x] Selected file size displays

## Upload Form

- [x] Subject is required
- [x] Topic is required
- [x] File is required
- [x] Field errors display correctly
- [x] Upload progress displays
- [x] Upload button disables during active operations
- [x] Successful upload clears the form
- [x] Successful upload creates one study-file row
- [x] Successful upload creates one private Storage object
- [x] Successful upload queues file processing
- [x] Failed upload is marked `failed`
- [x] Failed upload displays a friendly message
- [x] No duplicate file record is created during upload

---

# Phase 3 Study-File Database Tests

- [x] `public.study_files` exists
- [x] `public.file_processing_jobs` exists
- [x] `public.study_file_contents` exists
- [x] `public.study_file_chunks` exists
- [x] Row Level Security is enabled on all file-processing tables
- [x] Student can read only owned study-file rows
- [x] Student can read only owned processing jobs
- [x] Student can read only owned extracted content
- [x] Student can read only owned chunks
- [x] File is connected to an owned subject
- [x] Processing-job row is connected to one study file
- [x] Content row is connected to one study file
- [x] Chunks are connected to one study file
- [x] Chunk order begins at zero
- [x] File and job terminal statuses remain synchronized

---

# File-Processing Status Tests

- [x] New reservation uses `uploading`
- [x] Completed upload uses `queued`
- [x] Claimed job sets file to `reading`
- [x] Extraction completion sets file to `indexing`
- [x] Successful persistence sets file to `ready`
- [x] Successful persistence sets job to `completed`
- [x] Failed processing sets file to `failed`
- [x] Failed processing sets job to `failed`
- [x] Failure code is saved
- [x] Failure message is saved
- [x] Successful retry clears previous failure information

Expected file-status flow:

```text
uploading
→ queued
→ reading
→ indexing
→ ready
```

Possible failure flow:

```text
uploading
→ failed
```

or:

```text
queued
→ reading
→ failed
```

---

# Queue and Atomic Claim Tests

- [x] Queue RPC exists
- [x] Queue RPC changes the file to `queued`
- [x] Queue RPC creates or resets the processing job
- [x] Queue RPC avoids duplicate active jobs
- [x] Atomic claim RPC exists
- [x] Atomic claim returns the processing-job ID
- [x] Atomic claim returns the study-file ID
- [x] Atomic claim changes the job to `processing`
- [x] Atomic claim increments `attempt_count`
- [x] Atomic claim changes the file to `reading`
- [x] Atomic claim uses locking
- [x] Atomic claim uses `SKIP LOCKED`
- [x] Two workers cannot claim the same queued job
- [x] Empty queue returns no claimed job

---

# Backend Private File Access Tests

- [x] Backend can retrieve a study-file row
- [x] Backend can retrieve the connected processing job
- [x] Backend can download an owned private Storage object
- [x] Invalid Storage paths are rejected
- [x] Empty Storage objects are rejected
- [x] Oversized processing files are rejected
- [x] Missing Storage objects return a controlled error
- [x] Supabase request failures return a controlled error
- [x] Backend secret remains backend-only
- [x] Trusted Supabase request uses the configured secret key
- [x] Secrets are not returned in API error responses

---

# File Extraction Tests

## PDF

- [x] PDF extractor loads
- [x] PDF text is extracted
- [x] PDF page count is recorded
- [x] PDF chunks preserve page locators
- [x] Empty PDF text produces a controlled extraction error

## TXT

- [x] UTF-8 text is extracted
- [x] TXT character count is recorded
- [x] TXT uses a document locator
- [x] Invalid text encoding produces a controlled error
- [x] Empty text produces a controlled extraction error

## PPTX

- [x] PPTX extractor loads
- [x] Slide text is extracted
- [x] Table text is extracted
- [x] Grouped-shape text is handled
- [x] Notes are handled when available
- [x] Slide count is recorded
- [x] PPTX chunks preserve slide locators

## XLSX

- [x] XLSX extractor loads
- [x] Workbook sheets are read
- [x] Cell values are extracted
- [x] Empty rows are handled
- [x] Sheet count is recorded
- [x] XLSX chunks preserve sheet locators

## XLS

- [x] Legacy XLS extractor loads
- [x] Workbook sheets are read
- [x] Cell values are extracted
- [x] Sheet count is recorded
- [x] XLS chunks preserve sheet locators

## Unsupported Extraction

- [x] Unsupported extractable MIME type returns a controlled error
- [x] Image upload does not falsely report successful text extraction
- [x] Legacy PPT does not falsely report successful text extraction
- [x] OCR remains marked as a future feature

---

# Processing Persistence Tests

- [x] Full extracted text is stored
- [x] Character count is stored
- [x] Page count is stored for PDF
- [x] Slide count is stored for PPTX
- [x] Sheet count is stored for XLSX and XLS
- [x] Extraction metadata is stored
- [x] At least one chunk is required for completion
- [x] Existing content is replaced during successful reprocessing
- [x] Existing chunks are replaced during successful reprocessing
- [x] Chunk order is preserved
- [x] Successful completion sets `processed_at`
- [x] Successful completion clears previous failures
- [x] Partial processing results are not marked ready

---

# Reusable File Processor Tests

- [x] Processor validates the study-file row
- [x] Processor validates the processing-job row
- [x] Processor accepts a newly queued file
- [x] Processor accepts a file already claimed by the worker
- [x] Processor does not start an already claimed job twice
- [x] Processor downloads the private object
- [x] Processor selects the correct extractor
- [x] Processor creates chunks
- [x] Processor marks indexing
- [x] Processor completes persistence
- [x] Processor returns a typed success result
- [x] Processor returns a controlled not-found error
- [x] Processor returns a controlled conflict error
- [x] Processor returns a controlled oversized-file error
- [x] Processor returns a controlled extraction error
- [x] Processor saves a failure state when possible

---

# Internal Processing Endpoint Tests

## Security

- [x] Missing `X-Processor-Key` returns `401`
- [x] Incorrect `X-Processor-Key` returns `403`
- [x] Correct processor key permits access
- [x] Processor key uses secure comparison
- [x] Processor key is not exposed to the browser
- [x] Processor key is ignored by Git
- [x] Processor key is not logged

## Validate Source Endpoint

- [x] Endpoint is registered
- [x] Valid source returns `200`
- [x] Missing study file returns `404`
- [x] Missing processing job returns `404`
- [x] Missing Storage object returns a controlled error
- [x] Invalid state returns `409`
- [x] Oversized file returns `413`
- [x] Supabase failure maps to `502`

## Process Endpoint

- [x] Endpoint is registered
- [x] Successful processing returns `200`
- [x] Response includes file ID
- [x] Response includes job ID
- [x] Response includes character count
- [x] Response includes chunk count
- [x] Response includes file-type count metadata
- [x] Successful response reports `ready`
- [x] Successful response reports job `completed`
- [x] Unreadable content returns `422`
- [x] Invalid state returns `409`
- [x] Unexpected processing error returns `500`
- [x] Supabase or Storage failure returns `502`

---

# Automatic Worker Tests

- [x] Worker module imports
- [x] Worker help command works
- [x] `--once` option exists
- [x] `--poll-seconds` option exists
- [x] `--recovery-interval-seconds` option exists
- [x] `--stale-after-minutes` option exists
- [x] `--max-attempts` option exists
- [x] Worker validates polling configuration
- [x] Worker validates recovery configuration
- [x] Worker returns a no-work result for an empty queue
- [x] Worker claims one queued job
- [x] Worker processes a claimed file
- [x] Worker returns a successful result
- [x] Worker handles processor failure
- [x] Worker saves failure state when possible
- [x] Worker handles unexpected errors
- [x] Worker waits when no work exists
- [x] Worker stops gracefully
- [x] Worker can run continuously
- [x] Worker logs claimed and completed jobs

---

# Stale-Job Recovery Tests

- [x] Recovery RPC exists
- [x] Recovery RPC accepts a stale threshold
- [x] Recovery RPC accepts a maximum attempt count
- [x] Invalid stale threshold is rejected
- [x] Invalid maximum attempts value is rejected
- [x] Stale processing jobs are detected
- [x] Recoverable jobs are requeued
- [x] Connected files return to `queued`
- [x] Exhausted jobs are marked `failed`
- [x] Connected exhausted files are marked `failed`
- [x] Recovery returns requeued count
- [x] Recovery returns failed count
- [x] Worker calls recovery periodically
- [x] Worker runs recovery before `--once` processing
- [x] Recovery does not affect active recent jobs
- [ ] Manual stale-job simulation has been completed against the hosted database

---

# Frontend Automatic Status Refresh Tests

- [x] Local file state detects `uploading`
- [x] Local file state detects `queued`
- [x] Local file state detects `reading`
- [x] Local file state detects `indexing`
- [x] Polling begins after upload is queued
- [x] Polling uses `router.refresh()`
- [x] Refreshed server props synchronize with local state
- [x] Local active records are preserved until returned by the server
- [x] File changes to `Ready` without manual browser refresh
- [x] Preview button appears automatically
- [x] Download button appears automatically
- [x] Polling stops after `ready`
- [x] Polling stops after `failed`
- [x] Polling pauses when the browser tab is hidden
- [x] Polling resumes when the tab becomes visible
- [x] Status refresh does not create duplicate file records
- [x] Frontend lint accepts the synchronization implementation
- [x] TypeScript accepts the synchronization implementation
- [x] Production build accepts the synchronization implementation

---

# Preview and Download Tests

- [x] Preview is unavailable before `ready`
- [x] Download is unavailable before `ready`
- [x] Preview action verifies authenticated ownership
- [x] Download action verifies authenticated ownership
- [x] Preview creates a signed URL
- [x] Download creates a signed URL
- [x] Signed preview opens
- [x] Signed download starts
- [x] Signed URLs are not stored permanently
- [x] Signed URLs are not written to the database
- [x] Student cannot create access for another student's file
- [x] Missing Storage object produces a friendly error

---

# Delete File Tests

- [x] Delete control opens confirmation
- [x] Cancel preserves the file
- [x] Confirm removes the file
- [x] Study-file row is deleted
- [x] Processing-job row is removed
- [x] Extracted-content row is removed
- [x] Chunk rows are removed
- [x] Private Storage object is removed
- [x] Deleted file disappears from the interface
- [x] Student cannot delete another student's file
- [x] Delete failure displays a friendly message

---

# Retry Failed Upload Tests

- [x] Retry is shown only for failed files
- [x] Retry requires the same original filename
- [x] Selecting a different filename is rejected
- [x] Retried file returns to an active upload state
- [x] Retry uploads the replacement object
- [x] Retry queues processing
- [x] Retry restarts automatic polling
- [x] Successful retry reaches `ready`
- [x] Failed retry remains `failed`
- [x] Successful retry clears old failure information
- [x] Retry does not create duplicate study-file rows

---

# Responsive and Usability Tests

- [x] Subject page works on desktop
- [x] Subject page works on narrow screens
- [x] Upload form remains usable on mobile width
- [x] File cards remain readable on mobile width
- [x] Long filenames do not break the layout
- [x] Status badge remains visible
- [x] Action buttons remain usable
- [x] Progress bar remains readable
- [x] Empty state is understandable
- [x] Error messages are student-friendly
- [x] Loading controls prevent accidental duplicate actions

---

# Phase 3 Security Tests

- [x] Supabase backend secret exists only in backend configuration
- [x] Processor internal key exists only in backend configuration
- [x] Database password is not committed
- [x] Supabase access token is not committed
- [x] Local environment files are ignored
- [x] Private Storage bucket remains private
- [x] Browser clients use only publishable credentials
- [x] Backend credentials do not use a `NEXT_PUBLIC_` prefix
- [x] Row Level Security protects subject records
- [x] Row Level Security protects file metadata
- [x] Row Level Security protects extracted content
- [x] Row Level Security protects chunks
- [x] Internal routes require a processor key
- [x] API errors do not expose secret values
- [ ] Final Git history and staged-diff secret scan passes

---

# Final Database Regression Tests

- [ ] `npx supabase migration list --linked` succeeds
- [ ] Local and remote migration histories match
- [ ] `npx supabase db push --linked --dry-run` reports the remote database is up to date
- [ ] Generated database types include `subjects`
- [ ] Generated database types include `study_files`
- [ ] Generated database types include `file_processing_jobs`
- [ ] Generated database types include `study_file_contents`
- [ ] Generated database types include `study_file_chunks`
- [ ] Generated database types include the queue RPC
- [ ] Generated database types include the claim RPC
- [ ] Generated database types include the completion RPC
- [ ] Generated database types include the failure RPC
- [ ] Generated database types include the stale-recovery RPC
- [ ] Two-account Row Level Security test passes
- [ ] Two-account private Storage isolation test passes

---

# Final Backend Regression Tests

Run:

```bash
cd ~/stsp-capstone/backend

source .venv/bin/activate

python -m compileall app
python -m pytest
python -m pip check
```

Checklist:

- [ ] Application compilation passes
- [ ] All backend tests pass
- [ ] Dependency check passes
- [ ] No unexpected warnings require correction
- [ ] Health route remains registered
- [ ] Source-validation route remains registered
- [ ] Processing route remains registered
- [ ] Worker help command succeeds
- [ ] Worker `--once` succeeds
- [ ] Continuous worker starts successfully
- [ ] Continuous worker stops gracefully

---

# Final Frontend Regression Tests

Run:

```bash
cd ~/stsp-capstone/frontend

rm -rf .next
rm -f tsconfig.tsbuildinfo

npx next typegen
npm run lint
npx tsc --noEmit
npm run build
```

Checklist:

- [ ] Next.js route type generation passes
- [ ] ESLint passes
- [ ] TypeScript validation passes
- [ ] Production build passes
- [ ] Registration still works
- [ ] Login still works
- [ ] Logout still works
- [ ] Protected routes still work
- [ ] Onboarding still works
- [ ] Profile page still works
- [ ] Subject creation still works
- [ ] Subject editing still works
- [ ] Subject deletion still works
- [ ] File upload still works
- [ ] Automatic status refresh still works
- [ ] Preview still works
- [ ] Download still works
- [ ] Delete still works
- [ ] Retry still works
- [ ] Browser console has no unexpected errors

---

# Final End-to-End Phase 3 Test

Start three terminals.

## Terminal 1 — Frontend

```bash
cd ~/stsp-capstone/frontend

npm run dev
```

## Terminal 2 — FastAPI

```bash
cd ~/stsp-capstone/backend

source .venv/bin/activate

python -m uvicorn app.main:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000
```

## Terminal 3 — Worker

```bash
cd ~/stsp-capstone/backend

source .venv/bin/activate

python -m app.workers.file_processing_worker \
  --poll-seconds 2 \
  --recovery-interval-seconds 30 \
  --stale-after-minutes 30 \
  --max-attempts 3
```

Perform these final tests:

- [ ] Sign in using a test student account
- [ ] Create a new subject
- [ ] Upload a PDF
- [ ] Confirm PDF reaches `Ready` without manual refresh
- [ ] Confirm PDF content and chunks exist
- [ ] Preview the PDF
- [ ] Download the PDF
- [ ] Upload a TXT file
- [ ] Confirm TXT reaches `Ready`
- [ ] Upload a PPTX file
- [ ] Confirm PPTX reaches `Ready`
- [ ] Upload an XLSX file
- [ ] Confirm XLSX reaches `Ready`
- [ ] Upload an XLS file
- [ ] Confirm XLS reaches `Ready`
- [ ] Confirm no duplicate file rows exist
- [ ] Delete one uploaded file
- [ ] Confirm its database and Storage data are removed
- [ ] Test one failed upload or processing case
- [ ] Retry the failed file
- [ ] Confirm retry reaches `Ready` or returns a controlled failure
- [ ] Confirm polling stops after terminal status
- [ ] Confirm frontend terminal has no unexpected errors
- [ ] Confirm backend terminal has no unexpected traceback
- [ ] Confirm worker terminal has no unexpected traceback

---

# Final Documentation Regression Tests

- [ ] `docs/ARCHITECTURE.md` reflects Phase 3
- [ ] `docs/api-contracts.md` reflects internal processing endpoints
- [ ] `docs/database.md` reflects Phase 2 and Phase 3 tables
- [ ] `docs/setup-guide.md` reflects macOS and current worker commands
- [ ] `docs/testing-checklist.md` reflects Phase 3 tests
- [ ] `docs/PROJECT_FILE_MAP.md` lists all Phase 3 files
- [ ] Mermaid diagrams render
- [ ] Code fences are properly paired
- [ ] No real secrets appear in documentation
- [ ] No outdated Python 3.14 requirement remains
- [ ] No implemented Phase 2 or Phase 3 component is incorrectly labeled planned

---

# Final Git Safety Tests

Run:

```bash
cd ~/stsp-capstone

git branch --show-current
git status --short
git diff --check
git diff --stat
```

Confirm:

- [ ] Current branch is `phase3/subject-file-management`
- [ ] No unexpected files are staged
- [ ] `backend/.env` is not tracked
- [ ] `frontend/.env.local` is not tracked
- [ ] `.venv` is not tracked
- [ ] `node_modules` is not tracked
- [ ] `.next` is not tracked
- [ ] `.pytest_cache` is not tracked
- [ ] `__pycache__` is not tracked
- [ ] Supabase temporary files are not tracked
- [ ] No secret values appear in the staged diff
- [ ] `git diff --check` reports no errors

---

# Phase 3 Completion Approval

Phase 3 may be declared complete only after all final unchecked regression items above have passed.

Completion record:

```text
Phase: Phase 3 — Subject and File Management
Branch: phase3/subject-file-management
Database migrations synchronized:
Backend checks passed:
Frontend checks passed:
End-to-end upload test passed:
Auto-refresh test passed:
Stale-job recovery test passed:
Security review passed:
Documentation review passed:
Git review passed:
Ready to commit:
Ready to push:
Ready to merge into development:
Reviewed by:
Completion date:
```

---

# Bug Report Template

Use this format when a test fails:

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