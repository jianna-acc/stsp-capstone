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

## Health Check

Checks whether the FastAPI backend is running.

### Request

```http
GET /api/health
```

### Authentication

Not required.

### Successful Response

```json
{
  "status": "healthy",
  "service": "sts-capstone-api",
  "version": "0.1.0"
}
```

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

#### Request

```http
METHOD /api/example
```

#### Authentication

State whether a valid student session or access token is required.

#### Request Body

```json
{
  "example_field": "example value"
}
```

#### Successful Response

```json
{
  "example_result": "example value"
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

#### Frontend Consumer

List the frontend files that call this endpoint.

#### Backend Provider

List the route and service files that implement it.