<!-- File: /docs/api-contracts.md -->
<!-- Purpose: Documents communication between the Next.js frontend and FastAPI backend. -->

# API Contracts

This document records the agreed request and response formats used by the frontend and backend.

The team must update this document whenever:

- A new API endpoint is created.
- A request field changes.
- A response field changes.
- An endpoint is removed.
- Authentication requirements change.
- An error response changes.

## General API Information

| Item | Value |
|---|---|
| Development API URL | `http://127.0.0.1:8000` |
| API prefix | `/api` |
| Data format | JSON |
| Backend framework | FastAPI |
| Frontend consumer | Next.js |

## Standard Success Response

Features may return their own data structures, but successful requests should use clear HTTP status codes.

| Status | Meaning |
|---|---|
| `200` | Request completed successfully |
| `201` | New resource created successfully |
| `204` | Request completed with no response body |

## Standard Error Response

The initial backend error format should follow:

```json
{
  "detail": "A clear explanation of what went wrong."
}
```

The frontend should convert technical messages into friendly language when needed.

Example:

```text
Technical:
File extraction failed.

Student-facing:
We could not read this file. Try uploading a clearer or supported version.
```

### Request

```http
GET /api/health
```

### Authentication

Not required.

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
| `status` | `"healthy"` | Confirms that the application is operating normally |
| `service` | String | Name of the FastAPI service |
| `version` | String | Current backend application version |
| `environment` | `"development"`, `"testing"`, or `"production"` | Environment in which the backend is running |

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

The frontend API service combines:

```text
NEXT_PUBLIC_API_BASE_URL
        +
/api/health
        =
http://127.0.0.1:8000/api/health
```

### Frontend Behavior

The health-check interface supports the following states:

| State | Meaning |
|---|---|
| `idle` | No connection test has been performed |
| `loading` | The frontend is waiting for the backend |
| `success` | A valid health response was received |
| `error` | The backend could not be reached or returned invalid data |

A successful request displays:

- Service name
- Health status
- Backend version
- Current environment

A failed connection displays a friendly error and a retry button.

### Frontend Error Messages

| Condition | Message |
|---|---|
| API base URL missing | `The frontend API address is not configured.` |
| Connection unavailable | `The frontend could not connect to the backend.` |
| Request timeout | `The backend took too long to respond.` |
| Unexpected response | `The backend returned an unexpected health response.` |
| HTTP error | Uses the backend detail or HTTP status message |

### CORS Requirement

The FastAPI backend allows requests from:

```text
http://localhost:3000
```

This value is loaded from:

```text
backend/.env
```

through:

```text
backend/app/core/config.py
```

### Automated Backend Test

```text
/backend/tests/test_health.py
```

The test verifies:

- `200 OK`
- Correct health response data
- Allowed frontend CORS origin

### Manual Integration Test

1. Start FastAPI on port `8000`.
2. Start Next.js on port `3000`.
3. Open `http://localhost:3000`.
4. Select **Check backend**.
5. Confirm the status changes from **Checking** to **Connected**.
6. Stop FastAPI.
7. Select **Check again**.
8. Confirm the status changes to **Unavailable**.
9. Restart FastAPI.
10. Select **Retry connection**.
11. Confirm the status returns to **Connected**.
### Request

```http
GET /api/health
```

### Authentication

Not required.


### Used By

- `/frontend/services/api.ts`
- `/frontend/components/foundation/FoundationCheck.tsx`

### Provided By

- `/backend/app/api/health.py`

## Planned API Groups

| API Group | Purpose |
|---|---|
| `/api/auth` | Authentication validation and account-related backend actions |
| `/api/subjects` | Subject creation, reading, updating, and deletion |
| `/api/files` | File upload metadata and file-processing status |
| `/api/chat` | AI questions and source-grounded answers |
| `/api/reviewers` | Reviewer generation and retrieval |
| `/api/quizzes` | Quiz generation, answers, explanations, and scoring |
| `/api/tasks` | Academic task management |
| `/api/study-plans` | Personalized study-plan generation and adjustment |
| `/api/progress` | Quiz, task, and study-session progress data |

## Endpoint Documentation Template

Copy this section whenever a new endpoint is added.

### Endpoint Name

Briefly explain what the endpoint does.

### Request

```http
GET /api/health
```

### Authentication

Not required.

#### Request Body

```json
{
  "example_field": "example value"
}
```

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

#### Possible Errors

| Status | Reason |
|---|---|
| `400` | Invalid request |
| `401` | Student is not authenticated |
| `403` | Student does not own the requested resource |
| `404` | Resource was not found |
| `500` | Unexpected server error |

### Frontend Consumer

Planned:

```text
/frontend/services/api.ts
/frontend/components/foundation/BackendHealthCheck.tsx
```

### Backend Provider

```text
/backend/app/api/health.py
/backend/app/schemas/health.py
/backend/app/api/router.py
/backend/app/main.py
```