<!-- File: /docs/api-contracts.md -->
<!-- Purpose: Documents implemented communication contracts between the Next.js frontend, FastAPI backend, worker, and Supabase database functions. -->

# API Contracts

This document records the request, response, authentication, and error contracts used by the STS Capstone Project.

Update this document whenever:

- A new API endpoint is created
- A request field changes
- A response field changes
- An endpoint is removed
- Authentication requirements change
- An error response changes
- A trusted database function changes
- A frontend feature begins using a new backend contract

---

# General API Information

| Item | Value |
|---|---|
| Development API URL | `http://127.0.0.1:8000` |
| API prefix | `/api` |
| Data format | JSON |
| Backend framework | FastAPI |
| Frontend framework | Next.js |
| Backend entry point | `/backend/app/main.py` |
| Main router | `/backend/app/api/router.py` |

The full development endpoint is formed by combining:

```text
Backend base URL
        +
API prefix
        +
Route path
```

Example:

```text
http://127.0.0.1:8000
        +
/api
        +
/health
        =
http://127.0.0.1:8000/api/health
```

---

# Standard HTTP Status Codes

## Successful Responses

| Status | Meaning |
|---|---|
| `200 OK` | Request completed successfully |
| `201 Created` | A new resource was created |
| `204 No Content` | Request completed without a response body |

## Error Responses

FastAPI errors generally use:

```json
{
  "detail": "A clear explanation of what went wrong."
}
```

The frontend should convert technical messages into student-friendly text when appropriate.

Example:

```text
Technical message:
File extraction failed.

Student-facing message:
We could not read this file. Try uploading a supported or clearer version.
```

---

# Public Endpoint

## Health Check

Checks whether the FastAPI application is running.

### Request

```http
GET /api/health
```

### Authentication

Not required.

### Request Headers

No special headers are required.

### Request Body

None.

### Successful Response

Status:

```text
200 OK
```

Body:

```json
{
  "status": "healthy",
  "service": "STS Capstone API",
  "version": "0.1.0",
  "environment": "development"
}
```

### Response Fields

| Field | Type | Description |
|---|---|---|
| `status` | String | Health state of the API |
| `service` | String | FastAPI service name |
| `version` | String | Current backend application version |
| `environment` | String | Current runtime environment |

Supported environment values include:

```text
development
testing
production
```

### Frontend Consumer

```text
/frontend/services/api.ts
/frontend/types/api.ts
/frontend/components/foundation/BackendHealthCheck.tsx
```

### Backend Provider

```text
/backend/app/main.py
/backend/app/api/router.py
/backend/app/api/health.py
/backend/app/schemas/health.py
/backend/app/core/config.py
```

### Environment Configuration

Frontend:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Backend:

```env
FRONTEND_URL=http://localhost:3000
API_PREFIX=/api
```

### Frontend States

| State | Meaning |
|---|---|
| `idle` | No connection test has been performed |
| `loading` | The frontend is waiting for the backend |
| `success` | A valid response was received |
| `error` | The backend could not be reached or returned invalid data |

### Frontend Error Messages

| Condition | Message |
|---|---|
| API URL missing | `The frontend API address is not configured.` |
| Backend unavailable | `The frontend could not connect to the backend.` |
| Request timeout | `The backend took too long to respond.` |
| Invalid response | `The backend returned an unexpected health response.` |
| HTTP error | Uses the backend detail or status message |

### CORS Requirement

The backend allows the configured frontend origin:

```text
http://localhost:3000
```

The value is loaded from:

```text
/backend/.env
```

through:

```text
/backend/app/core/config.py
```

### Automated Test

```text
/backend/tests/test_health.py
```

The test verifies:

- `200 OK`
- Correct response fields
- Correct service information
- Allowed frontend CORS origin

---

# Internal File-Processing Security

Phase 3 introduces trusted internal processing endpoints.

These endpoints are not public upload APIs and are not intended to be called directly by an unauthenticated browser.

Required header:

```http
X-Processor-Key: INTERNAL_PROCESSOR_SECRET
```

The expected value is loaded from:

```text
/backend/.env
```

Environment variable:

```env
PROCESSOR_INTERNAL_KEY=replace-with-a-private-random-value
```

The processor key must never be:

- Added to a `NEXT_PUBLIC_` environment variable
- Exposed in browser code
- Included in screenshots
- Committed to Git
- Written in documentation
- Shared through frontend API responses

Security provider:

```text
/backend/app/core/security.py
```

The backend compares the provided processor key with the configured value using a secure comparison.

---

# Internal File-Processing Endpoints

## Validate File Source

Validates that a study-file record, processing job, and private Storage object are available before processing.

### Request

```http
POST /api/internal/file-processing/{file_id}/validate-source
```

### Path Parameter

| Parameter | Type | Description |
|---|---|---|
| `file_id` | UUID | Study-file record to validate |

### Authentication

Required internal processor key.

### Required Header

```http
X-Processor-Key: configured-private-value
```

### Request Body

None.

### Successful Response

Status:

```text
200 OK
```

Representative body:

```json
{
  "study_file_id": "f0dbc2c6-3e77-4609-a5b5-ecf8f64b60c7",
  "processing_job_id": "9b8d5ad3-6f55-477a-b916-72cf668dc76d",
  "filename": "lesson.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 245760,
  "processing_status": "queued",
  "job_status": "queued"
}
```

### Response Fields

| Field | Type | Description |
|---|---|---|
| `study_file_id` | UUID | Validated study-file record |
| `processing_job_id` | UUID | Connected processing-job record |
| `filename` | String | Original uploaded filename |
| `mime_type` | String | Stored MIME type |
| `size_bytes` | Integer | Stored file size |
| `processing_status` | String | Current study-file processing status |
| `job_status` | String | Current processing-job status |

### Validation Performed

The service verifies that:

- The study-file row exists
- The processing job exists
- The file has a supported processing state
- The private Storage path is valid
- The private Storage object exists
- The downloaded object is not empty
- The object does not exceed the backend processing limit

### Backend Provider

```text
/backend/app/api/routes/file_processing.py
/backend/app/core/security.py
/backend/app/schemas/file_processing.py
/backend/app/services/file_processor.py
/backend/app/services/supabase_admin.py
```

---

## Process Study File

Processes one queued or previously claimed study file.

### Request

```http
POST /api/internal/file-processing/{file_id}/process
```

### Path Parameter

| Parameter | Type | Description |
|---|---|---|
| `file_id` | UUID | Study-file record to process |

### Authentication

Required internal processor key.

### Required Header

```http
X-Processor-Key: configured-private-value
```

### Request Body

None.

### Successful Response

Status:

```text
200 OK
```

Representative body:

```json
{
  "study_file_id": "f0dbc2c6-3e77-4609-a5b5-ecf8f64b60c7",
  "processing_job_id": "9b8d5ad3-6f55-477a-b916-72cf668dc76d",
  "filename": "lesson.pdf",
  "mime_type": "application/pdf",
  "character_count": 12540,
  "chunk_count": 8,
  "page_count": 6,
  "slide_count": null,
  "sheet_count": null,
  "processing_status": "ready",
  "job_status": "completed"
}
```

### Response Fields

| Field | Type | Description |
|---|---|---|
| `study_file_id` | UUID | Processed study-file record |
| `processing_job_id` | UUID | Connected processing-job record |
| `filename` | String | Original uploaded filename |
| `mime_type` | String | Processed MIME type |
| `character_count` | Integer | Number of extracted characters |
| `chunk_count` | Integer | Number of stored chunks |
| `page_count` | Integer or null | PDF page count |
| `slide_count` | Integer or null | PowerPoint slide count |
| `sheet_count` | Integer or null | Spreadsheet sheet count |
| `processing_status` | String | Final study-file state |
| `job_status` | String | Final processing-job state |

### Processing Workflow

The endpoint:

1. Loads the study-file record.
2. Loads the connected processing job.
3. Validates the processing state.
4. Downloads the private Storage object.
5. Selects the extractor based on MIME type.
6. Extracts text and metadata.
7. Creates ordered chunks.
8. Marks the file as `indexing`.
9. Stores full extracted content.
10. Replaces file chunks.
11. Marks the file as `ready`.
12. Marks the processing job as `completed`.

When processing fails, the service attempts to save a synchronized failed state.

### Supported Extractors

| Format | MIME or type | Extractor |
|---|---|---|
| PDF | `application/pdf` | `pypdf` |
| Plain text | `text/plain` | UTF-8 decoder |
| PowerPoint | PPTX | `python-pptx` |
| Excel | XLSX | `openpyxl` |
| Legacy Excel | XLS | `xlrd` |

PPT upload is accepted by the frontend foundation, but legacy PPT extraction may require conversion or a later extractor.

Image upload is supported, but OCR extraction is planned for a later phase.

### Backend Provider

```text
/backend/app/api/routes/file_processing.py
/backend/app/core/security.py
/backend/app/schemas/file_processing.py
/backend/app/services/file_processor.py
/backend/app/services/file_extraction.py
/backend/app/services/supabase_admin.py
```

### Automated Tests

```text
/backend/tests/test_file_processor.py
/backend/tests/test_file_processing_worker.py
```

---

# Internal Endpoint Errors

Both internal processing endpoints may return the following responses.

| Status | Reason |
|---|---|
| `401 Unauthorized` | `X-Processor-Key` header is missing |
| `403 Forbidden` | Processor key is incorrect |
| `404 Not Found` | Study file, processing job, or Storage object was not found |
| `409 Conflict` | File or job is in an invalid processing state |
| `413 Content Too Large` | File exceeds the backend processing limit |
| `422 Unprocessable Content` | File exists but its content cannot be extracted |
| `500 Internal Server Error` | Unexpected backend processing error |
| `502 Bad Gateway` | Supabase or Storage failed during the request |

Error body:

```json
{
  "detail": "The file could not be processed."
}
```

The backend must not return:

- Supabase secret values
- Processor keys
- Database passwords
- Raw environment variables
- Full private Storage credentials

---

# File-Processing Worker Contract

The automatic worker normally processes queued files without calling the HTTP processing endpoint.

Worker module:

```text
/backend/app/workers/file_processing_worker.py
```

Development command:

```bash
cd ~/stsp-capstone/backend

source .venv/bin/activate

python -m app.workers.file_processing_worker \
  --poll-seconds 2 \
  --recovery-interval-seconds 30 \
  --stale-after-minutes 30 \
  --max-attempts 3
```

Supported arguments:

| Argument | Purpose |
|---|---|
| `--once` | Recover stale jobs, process at most one queued job, and exit |
| `--poll-seconds` | Delay when no queued job is found |
| `--recovery-interval-seconds` | Delay between stale-job recovery checks |
| `--stale-after-minutes` | Age before a processing job is considered abandoned |
| `--max-attempts` | Maximum claim attempts before permanent failure |

Worker workflow:

```text
Recover stale jobs
        ↓
Claim next queued job
        ↓
Download private file
        ↓
Extract text
        ↓
Create chunks
        ↓
Persist content
        ↓
Mark ready or failed
```

---

# Database RPC Contracts

Database functions are accessed through Supabase PostgREST RPC calls.

Applied functions are database API contracts. Changes must use a new migration.

---

## Queue Study File Processing

Function:

```text
public.queue_study_file_processing(uuid)
```

Expected parameter:

```json
{
  "p_study_file_id": "study-file-uuid"
}
```

Purpose:

- Verifies the file may be queued
- Changes `study_files.processing_status` to `queued`
- Creates or resets the connected processing job
- Clears previous failure information
- Avoids duplicate active jobs

Called after the private Storage upload finishes successfully.

---

## Claim Next Processing Job

Function:

```text
public.claim_next_file_processing_job()
```

Request payload:

```json
{}
```

Representative response:

```json
[
  {
    "processing_job_id": "9b8d5ad3-6f55-477a-b916-72cf668dc76d",
    "study_file_id": "f0dbc2c6-3e77-4609-a5b5-ecf8f64b60c7"
  }
]
```

When no queued job exists, the function returns no row.

Purpose:

- Locks the next queued job
- Uses `SKIP LOCKED`
- Marks the job as `processing`
- Increments `attempt_count`
- Records the start time
- Marks the study file as `reading`
- Returns the claimed identifiers

---

## Start Study File Processing

Function:

```text
public.start_study_file_processing(uuid)
```

Expected parameter:

```json
{
  "p_study_file_id": "study-file-uuid"
}
```

Purpose:

- Starts processing for a queued file
- Marks the file as `reading`
- Marks the job as `processing`
- Records the processing start time

The reusable processor supports both newly queued files and files already claimed by the automatic worker.

---

## Mark Study File Indexing

Function:

```text
public.mark_study_file_indexing(uuid)
```

Expected parameter:

```json
{
  "p_study_file_id": "study-file-uuid"
}
```

Purpose:

- Verifies the file is actively processing
- Marks the study file as `indexing`
- Keeps the connected job active

---

## Complete Study File Processing

Function:

```text
public.complete_study_file_processing(...)
```

Representative request payload:

```json
{
  "p_study_file_id": "study-file-uuid",
  "p_extracted_text": "Complete extracted document text.",
  "p_page_count": 5,
  "p_slide_count": null,
  "p_sheet_count": null,
  "p_character_count": 12450,
  "p_extraction_metadata": {
    "extractor": "pypdf"
  },
  "p_chunks": [
    {
      "chunk_index": 0,
      "content": "First extracted section.",
      "locator_type": "page",
      "locator_label": "Page 1",
      "token_count": 35,
      "metadata": {}
    }
  ]
}
```

Purpose:

- Replaces full extracted content
- Replaces ordered chunks
- Saves file-type metadata
- Marks the study file as `ready`
- Sets `processed_at`
- Marks the processing job as `completed`
- Sets `completed_at`
- Clears previous errors

---

## Fail Study File Processing

Function:

```text
public.fail_study_file_processing(...)
```

Expected parameters:

```json
{
  "p_study_file_id": "study-file-uuid",
  "p_error_code": "EXTRACTION_ERROR",
  "p_error_message": "The file content could not be extracted."
}
```

Purpose:

- Marks the study file as `failed`
- Stores `failure_code`
- Stores `failure_message`
- Marks the processing job as `failed`
- Stores worker error information
- Sets the completion time

---

## Recover Stale File-Processing Jobs

Function:

```text
public.recover_stale_file_processing_jobs(
  integer,
  integer
)
```

Expected parameters:

```json
{
  "p_stale_after_minutes": 30,
  "p_max_attempts": 3
}
```

Representative response:

```json
[
  {
    "requeued_count": 2,
    "failed_count": 1
  }
]
```

Purpose:

- Finds abandoned processing jobs
- Requeues jobs with remaining attempts
- Returns connected files to `queued`
- Permanently fails jobs that reached the maximum attempts
- Returns requeued and failed counts

This function is called periodically by the automatic worker.

---

# Frontend File Operations

Student-facing file operations are implemented primarily through Next.js Server Actions and Supabase authenticated clients rather than public FastAPI endpoints.

Implemented operations include:

- Reserve an upload
- Complete an upload
- Mark an upload as failed
- Retry a failed upload
- Create a signed preview URL
- Create a signed download URL
- Delete a study file

Primary frontend contract provider:

```text
/frontend/features/files/actions.ts
```

Main consumer:

```text
/frontend/features/files/components/FileUploadManager.tsx
```

These actions verify the authenticated Supabase user and rely on Row Level Security.

---

# Planned API Groups

The following API groups remain planned.

| API Group | Purpose |
|---|---|
| `/api/auth` | Backend authentication validation |
| `/api/chat` | Source-grounded student questions and answers |
| `/api/reviewers` | Reviewer generation and retrieval |
| `/api/flashcards` | Flashcard generation and practice |
| `/api/quizzes` | Quiz generation, explanations, and scoring |
| `/api/tasks` | Academic task management |
| `/api/study-plans` | Personalized study-plan generation |
| `/api/progress` | Quiz, task, and study-session analytics |
| `/api/retrieval` | Semantic retrieval from uploaded material |

These routes must not be treated as implemented until corresponding FastAPI route files and tests exist.

---

# Manual Internal Endpoint Test

Load the private processor key from the backend environment without printing it:

```bash
cd ~/stsp-capstone/backend

PROCESSOR_KEY=$(
  grep '^PROCESSOR_INTERNAL_KEY=' .env |
  cut -d '=' -f 2-
)
```

Validate a source:

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/internal/file-processing/FILE_UUID/validate-source" \
  -H "X-Processor-Key: ${PROCESSOR_KEY}"
```

Process a source:

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/internal/file-processing/FILE_UUID/process" \
  -H "X-Processor-Key: ${PROCESSOR_KEY}"
```

Replace:

```text
FILE_UUID
```

with an actual study-file UUID.

Do not print or paste the processor key.

---

# OpenAPI Verification

Start FastAPI:

```bash
cd ~/stsp-capstone/backend

source .venv/bin/activate

python -m uvicorn app.main:app \
  --reload \
  --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

The OpenAPI interface should show:

```text
GET  /api/health
POST /api/internal/file-processing/{file_id}/validate-source
POST /api/internal/file-processing/{file_id}/process
```

The route list may also be checked using:

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

---

# API Change Rules

When changing an API or RPC contract:

1. Update the FastAPI schema.
2. Update the route or database function.
3. Add or update automated tests.
4. Update the frontend consumer.
5. Update this document.
6. Update `/docs/ARCHITECTURE.md`.
7. Update `/docs/PROJECT_FILE_MAP.md`.
8. Create a new migration for database-function changes.
9. Never edit an already applied migration.
10. Regenerate database types after schema changes.
11. Verify the OpenAPI output.
12. Do not expose secrets in responses, logs, or screenshots.