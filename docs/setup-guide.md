<!-- File: /docs/setup-guide.md -->

# Development Setup Guide

This document explains how to install, configure, test, and run the STS Capstone Project.

## Required Software

- Git
- Visual Studio Code
- Node.js 20.9 or newer
- npm
- Python 3.14
- A supported web browser

## Versions Used During Initial Setup

```text
Node.js: v22.15.0
npm: 11.16.0
Next.js: 16.2.10
Python: 3.14.3
```

These are the versions used during the initial setup. Team members should use compatible versions and install the exact project dependencies from the lock files.

# Frontend Setup

## Install Frontend Dependencies

From the project root:

```powershell
cd frontend
npm install
```

The command reads:

```text
frontend/package.json
frontend/package-lock.json
```

It installs local dependencies inside:

```text
frontend/node_modules/
```

The `node_modules` folder is generated locally and must not be committed.

## Run the Frontend

From the `frontend` folder:

```powershell
npm run dev
```

Open:

```text
http://localhost:3000
```

Stop the server with:

```text
Ctrl + C
```

## Check the Frontend

Run ESLint:

```powershell
npm run lint
```

Create a production build:

```powershell
npm run build
```

Both commands must pass before frontend changes are submitted for review.

## Frontend Structure

```text
frontend/
├── app/
│   ├── favicon.ico
│   ├── globals.css
│   ├── layout.tsx
│   ├── page.tsx
│   └── providers.tsx
├── components/
│   └── foundation/
│       ├── MantineFoundationCheck.module.css
│       └── MantineFoundationCheck.tsx
├── public/
├── theme/
│   ├── colors.ts
│   ├── components.ts
│   └── theme.ts
├── eslint.config.mjs
├── next-env.d.ts
├── next.config.ts
├── package-lock.json
├── package.json
├── postcss.config.cjs
└── tsconfig.json
```

## Frontend Styling

The approved styling system is:

- Mantine UI
- CSS Modules
- Global CSS variables
- Tabler Icons
- Motion for small animations

Tailwind is not part of the approved frontend stack.

## Mantine Design-System Packages

Installed packages include:

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

The Mantine configuration is stored in:

```text
frontend/
├── app/
│   └── providers.tsx
├── theme/
│   ├── colors.ts
│   ├── components.ts
│   └── theme.ts
└── postcss.config.cjs
```

### Provider Connection

```text
app/layout.tsx
    ↓
app/providers.tsx
    ├── MantineProvider
    ├── ModalsProvider
    └── Notifications
```

Only one global `Notifications` component should be rendered.

## Test the Mantine Foundation

Run:

```powershell
cd frontend
npm run lint
npm run build
npm run dev
```

Open:

```text
http://localhost:3000
```

Confirm that:

1. The purple theme and cards display.
2. The notification test works.
3. The confirmation modal opens.
4. Confirming the modal produces another notification.
5. The cards and buttons stack correctly on a narrow screen.
6. The browser console has no red errors.

## Frontend Cache Troubleshooting

When the development server starts but the page keeps loading with an error such as `Unexpected end of JSON input`, stop the server and clear the generated Next.js cache:

```powershell
cd frontend
Remove-Item -Recurse -Force .next
npm run dev
```

The `.next` folder contains generated files and is recreated automatically. Do not delete source files.

# Backend Setup

## Create the Python Virtual Environment

From the project root:

```powershell
cd backend
py -3.14 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, the terminal should begin with:

```text
(.venv)
```

If PowerShell temporarily blocks the activation script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Do not change the execution policy globally.

## Install Backend Dependencies

Install the exact locked environment:

```powershell
python -m pip install -r requirements.txt
```

Verify the environment:

```powershell
python -m pip check
```

Expected result:

```text
No broken requirements found.
```

## Backend Dependency Files

| File | Purpose |
|---|---|
| `requirements.in` | Lists the direct packages intentionally selected by the team |
| `requirements.txt` | Locks all installed packages to exact versions |
| `.venv/` | Stores local packages and must not be committed |

The backend currently keeps both HTTP client packages:

- `httpx` because some installed services may still depend on it.
- `httpx2` for the current Starlette and FastAPI test client.

Do not remove either package without running `pip check` and the complete backend test suite.

When intentionally changing backend dependencies:

```text
Edit requirements.in
        ↓
Install requirements.in
        ↓
Run import and dependency checks
        ↓
Regenerate requirements.txt
        ↓
Run backend tests
```

## Backend Environment Configuration

Create the private environment file from the safe example:

```powershell
cd backend
Copy-Item .env.example .env
```

The safe template may be committed:

```text
backend/.env.example
```

The real local file must not be committed:

```text
backend/.env
```

Initial development values:

```env
APP_NAME=STS Capstone API
APP_VERSION=0.1.0
ENVIRONMENT=development
API_PREFIX=/api
FRONTEND_URL=http://localhost:3000

SUPABASE_URL=
SUPABASE_SECRET_KEY=
GEMINI_API_KEY=
```

Supabase and Gemini values remain empty until their setup phases.

Test the loaded settings:

```powershell
python -c "from app.core.config import get_settings; settings = get_settings(); print(settings.app_name, settings.environment, settings.frontend_url)"
```

Do not display or share the real `.env` contents after secrets are added.

## Run the FastAPI Backend

From the project root:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

Open the generated OpenAPI document:

```text
http://127.0.0.1:8000/openapi.json
```

Stop the backend server using:

```text
Ctrl + C
```

The frontend origin currently allowed by CORS is:

```text
http://localhost:3000
```

This value comes from `FRONTEND_URL` inside the private backend `.env` file.

## Current Backend Status

The following backend foundation is already available:

- Python virtual environment
- Locked dependencies
- FastAPI package folders
- Typed configuration in `app/core/config.py`
- Safe `.env.example`
- Private local `.env`

The FastAPI application entry point, CORS middleware, API router, health endpoint, and automated health test are the next backend files to be created.

# Git Safety Checks

Before every commit, run:

```powershell
git status
```

Confirm that these do not appear:

```text
frontend/node_modules/
frontend/.next/
backend/.venv/
backend/.env
__pycache__/
```

The following safe example files may be committed:

```text
frontend/.env.example
backend/.env.example
```