<!-- File: /docs/testing-checklist.md -->
<!-- Purpose: Tracks the tests required before a feature is considered complete. -->

# Testing Checklist

A feature is not finished only because its page appears correctly.

A completed feature must also handle:

- Loading
- Success
- Empty data
- Invalid input
- Errors
- Retry behavior
- Mobile layout
- Access control

## Phase 1 Repository Tests

- [x] Local Git repository exists
- [x] GitHub remote is connected
- [x] `main` branch exists
- [x] `development` branch exists
- [x] First commit is pushed
- [x] Working tree is clean

## Documentation Tests

- [ ] Root README exists
- [ ] Project file map exists
- [ ] Architecture document exists
- [ ] Setup guide exists
- [ ] API contracts document exists
- [ ] Database document exists
- [ ] Git workflow document exists
- [ ] Testing checklist exists
- [ ] Mermaid diagrams display correctly
- [ ] File paths in documentation are accurate

## Frontend Foundation Tests

- [x] Node.js version is supported
- [x] Next.js project installs successfully
- [x] `npm run dev` starts
- [x] Home page opens
- [x] CSS Modules work
- [x] Tailwind is not installed
- [x] Mantine styles load
- [x] Custom purple theme is applied
- [x] Tabler icons display
- [x] Mantine notification appears
- [x] Confirmation modal opens
- [x] Cancel closes the modal
- [x] Confirming the modal triggers a success notification
- [x] Responsive card layout works
- [x] Buttons stack on narrow screens
- [x] Browser console has no red errors
- [x] `npm run lint` passes
- [x] `npm run build` passes

## Backend Foundation Tests

- [x] Python virtual environment is created
- [x] Virtual environment activates
- [x] Backend dependencies install
- [x] `pip check` reports no broken requirements
- [x] Typed environment settings load
- [x] Private `.env` is ignored by Git
- [x] FastAPI application imports successfully
- [x] FastAPI starts on port 8000
- [x] `/docs` opens
- [x] `/openapi.json` opens
- [x] CORS permits `http://localhost:3000`
- [x] `/api/health` returns `200`
- [x] Health response matches its schema
- [x] Swagger displays the health endpoint
- [x] `pytest` passes

## Frontend-to-Backend Integration Tests

- [x] Frontend `.env.example` documents the backend base URL
- [x] Frontend `.env.local` is ignored by Git
- [x] `NEXT_PUBLIC_API_BASE_URL` loads correctly
- [x] Frontend API response types compile
- [x] API service validates the backend health response
- [x] API service handles missing configuration
- [x] API service handles connection failures
- [x] API service includes an eight-second timeout
- [x] Health-check component displays the idle state
- [x] Health-check component displays the loading state
- [x] Health-check component displays the connected state
- [x] Health-check component displays all response fields
- [x] Health-check component displays the unavailable state
- [x] Retry reconnects after FastAPI restarts
- [x] Check again sends another successful request
- [x] Backend receives `GET /api/health`
- [x] Browser receives `200 OK`
- [x] CORS allows the Next.js frontend origin
- [x] Component remains usable after a failed request
- [x] Notification and modal systems continue working
- [x] Connected interface is responsive
- [x] Error interface is responsive
- [x] Browser console has no unexpected errors
- [x] Frontend terminal has no compilation errors
- [x] Backend terminal has no traceback
- [x] `npm run lint` passes
- [x] `npm run build` passes
- [x] `npx tsc --noEmit` passes
- [x] `python -m pip check` passes
- [x] `python -m pytest -v` passes

## Frontend and Backend Integration

- [ ] Frontend calls the health endpoint
- [ ] Loading state appears during the request
- [ ] Success notification appears
- [ ] Friendly error appears when the backend is stopped
- [ ] Retry works after restarting the backend

## Supabase Tests

- [ ] Supabase project exists
- [ ] Publishable key is used in the frontend
- [ ] Secret key is used only in the backend
- [ ] Environment files are ignored by Git
- [ ] Profiles table exists
- [ ] Subjects table exists
- [ ] Study-files table exists
- [ ] Row Level Security is enabled
- [ ] Private storage bucket exists
- [ ] One student cannot access another student's data

## Authentication Tests

- [ ] Student can register
- [ ] Full name is saved
- [ ] Profile row is created
- [ ] Student can log in
- [ ] Invalid credentials show a friendly error
- [ ] Protected dashboard rejects unauthenticated users
- [ ] Session remains after refresh
- [ ] Student can log out
- [ ] Logged-out student returns to login

## Bug Report Template

Use this format:

```text
Title:
Feature:
Branch:
Steps to reproduce:
Expected result:
Actual result:
Error message:
Screenshot:
Browser or device:
Priority:
Assigned member: