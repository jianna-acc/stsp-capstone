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

- [ ] Node.js version is supported
- [ ] Next.js project installs successfully
- [ ] `npm run dev` starts
- [ ] Home page opens
- [ ] Mantine styles load
- [ ] Notifications work
- [ ] CSS Modules work
- [ ] Browser console has no errors
- [ ] `npm run lint` passes
- [ ] `npm run build` passes

## Backend Foundation Tests

- [ ] Python virtual environment is created
- [ ] Virtual environment activates
- [ ] Backend dependencies install
- [ ] FastAPI starts
- [ ] `/api/health` returns a successful response
- [ ] `/docs` opens
- [ ] CORS permits the frontend
- [ ] `pytest` passes

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