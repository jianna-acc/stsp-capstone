<!-- File: /docs/ARCHITECTURE.md -->

# STS Capstone Project Architecture

This document shows how the main parts of the application connect.

The diagrams use Mermaid syntax. View this file using a Markdown viewer that supports Mermaid diagrams.

## Main System Architecture

```mermaid
flowchart LR
    USER[Student]

    subgraph FRONTEND[Next.js Frontend]
        UI[Mantine User Interface]
        AUTH_UI[Login and Registration]
        DASHBOARD[Dashboard]
        FILE_UI[File Upload Interface]
        CHAT_UI[AI Assistant Interface]
        QUIZ_UI[Reviewer and Quiz Interface]
        PLAN_UI[Tasks and Study Plan Interface]
        API_SERVICE[Frontend API Service]
        SUPABASE_CLIENT[Supabase Browser Client]
    end

    subgraph BACKEND[FastAPI Backend]
        API[FastAPI Routes]
        AUTH_SERVICE[Authentication Validation]
        FILE_SERVICE[File Processing Service]
        RAG_SERVICE[Study Retrieval Service]
        AI_SERVICE[Gemini AI Service]
        QUIZ_SERVICE[Quiz and Reviewer Service]
        PLAN_SERVICE[Task and Study Plan Service]
    end

    subgraph SUPABASE[Supabase Platform]
        AUTH[Supabase Authentication]
        DATABASE[(PostgreSQL Database)]
        STORAGE[(Private File Storage)]
    end

    GEMINI[Gemini API]

    USER --> UI

    UI --> AUTH_UI
    UI --> DASHBOARD
    UI --> FILE_UI
    UI --> CHAT_UI
    UI --> QUIZ_UI
    UI --> PLAN_UI

    AUTH_UI --> SUPABASE_CLIENT
    SUPABASE_CLIENT --> AUTH
    SUPABASE_CLIENT --> DATABASE

    DASHBOARD --> API_SERVICE
    FILE_UI --> API_SERVICE
    CHAT_UI --> API_SERVICE
    QUIZ_UI --> API_SERVICE
    PLAN_UI --> API_SERVICE

    API_SERVICE --> API

    API --> AUTH_SERVICE
    API --> FILE_SERVICE
    API --> RAG_SERVICE
    API --> QUIZ_SERVICE
    API --> PLAN_SERVICE

    AUTH_SERVICE --> AUTH
    FILE_SERVICE --> STORAGE
    FILE_SERVICE --> DATABASE
    RAG_SERVICE --> DATABASE
    RAG_SERVICE --> STORAGE

    RAG_SERVICE --> AI_SERVICE
    QUIZ_SERVICE --> AI_SERVICE
    PLAN_SERVICE --> AI_SERVICE

    AI_SERVICE --> GEMINI

    QUIZ_SERVICE --> DATABASE
    PLAN_SERVICE --> DATABASE
```

## Initial Phase 1 Connection

```mermaid
sequenceDiagram
    actor Student
    participant Frontend as Next.js Frontend
    participant APIService as frontend/services/api.ts
    participant FastAPI as FastAPI Backend
    participant HealthRoute as GET /api/health

    Student->>Frontend: Opens the application
    Student->>Frontend: Clicks Check Backend
    Frontend->>APIService: Calls getApiHealth()
    APIService->>FastAPI: Sends GET /api/health
    FastAPI->>HealthRoute: Runs health check
    HealthRoute-->>FastAPI: Returns healthy response
    FastAPI-->>APIService: Returns JSON
    APIService-->>Frontend: Returns health result
    Frontend-->>Student: Shows Backend Connected
```

## Repository Ownership

```mermaid
flowchart TD
    REPO[STS Capstone Repository]

    REPO --> ROOT[Shared Root Files]
    REPO --> FRONTEND_FOLDER[frontend]
    REPO --> BACKEND_FOLDER[backend]
    REPO --> SUPABASE_FOLDER[supabase]
    REPO --> DOCS_FOLDER[docs]

    ROOT --> MEMBER1[Member 1: Technical Lead]

    FRONTEND_FOLDER --> MEMBER2[Member 2: UI and Design System]
    FRONTEND_FOLDER --> MEMBER1

    BACKEND_FOLDER --> MEMBER3[Member 3: FastAPI and AI Services]

    SUPABASE_FOLDER --> MEMBER4[Member 4: Database and Security]

    DOCS_FOLDER --> MEMBER5[Member 5: Testing and Documentation]
    DOCS_FOLDER --> MEMBER1
```

## Planned Data Relationships

This is an initial database outline. It will be finalized during the Supabase database phase.

```mermaid
erDiagram
    AUTH_USERS ||--|| PROFILES : has
    AUTH_USERS ||--o{ SUBJECTS : creates
    AUTH_USERS ||--o{ STUDY_FILES : uploads
    AUTH_USERS ||--o{ ACADEMIC_TASKS : owns
    AUTH_USERS ||--o{ STUDY_PLANS : receives
    AUTH_USERS ||--o{ QUIZ_ATTEMPTS : completes

    SUBJECTS ||--o{ STUDY_FILES : contains
    SUBJECTS ||--o{ ACADEMIC_TASKS : includes
    SUBJECTS ||--o{ REVIEWERS : organizes
    SUBJECTS ||--o{ QUIZZES : organizes

    STUDY_FILES ||--o{ REVIEWERS : supports
    STUDY_FILES ||--o{ QUIZZES : supports
    STUDY_PLANS ||--o{ STUDY_SESSIONS : contains
    QUIZZES ||--o{ QUIZ_ATTEMPTS : records

    PROFILES {
        uuid id PK
        string full_name
        boolean onboarding_completed
        datetime created_at
    }

    SUBJECTS {
        uuid id PK
        uuid student_id FK
        string name
        string color
        datetime created_at
    }

    STUDY_FILES {
        uuid id PK
        uuid student_id FK
        uuid subject_id FK
        string filename
        string storage_path
        string processing_status
    }

    ACADEMIC_TASKS {
        uuid id PK
        uuid student_id FK
        uuid subject_id FK
        string title
        datetime deadline
        integer estimated_minutes
        string status
    }

    STUDY_PLANS {
        uuid id PK
        uuid student_id FK
        date plan_date
        string status
    }

    STUDY_SESSIONS {
        uuid id PK
        uuid study_plan_id FK
        datetime start_time
        integer duration_minutes
        string status
    }

    REVIEWERS {
        uuid id PK
        uuid student_id FK
        uuid subject_id FK
        string title
        datetime created_at
    }

    QUIZZES {
        uuid id PK
        uuid student_id FK
        uuid subject_id FK
        string title
        integer question_count
    }

    QUIZ_ATTEMPTS {
        uuid id PK
        uuid quiz_id FK
        uuid student_id FK
        integer score
        datetime completed_at
    }
```

## Diagram Update Rules

Update this document when:

1. A new major service is introduced.
2. A new database table is created.
3. A frontend feature begins calling a new endpoint.
4. A backend service starts using Gemini.
5. A module begins reading from Supabase Storage.
6. Ownership of a module changes.
7. A major connection is removed.

## Phase 1C Frontend Foundation

```mermaid
flowchart TD
    BROWSER[Web Browser]
    NEXT_DEV[Next.js Development Server]
    ROOT_LAYOUT[app/layout.tsx]
    GLOBAL_CSS[app/globals.css]
    HOME_PAGE[app/page.tsx]
    PAGE_CSS[app/page.module.css]
    NEXT_CONFIG[next.config.ts]
    PACKAGE_JSON[package.json]
    TYPESCRIPT[tsconfig.json]
    ESLINT[eslint.config.mjs]

    PACKAGE_JSON --> NEXT_DEV
    NEXT_CONFIG --> NEXT_DEV
    TYPESCRIPT --> NEXT_DEV
    ESLINT --> LINT_CHECK[npm run lint]

    BROWSER --> NEXT_DEV
    NEXT_DEV --> ROOT_LAYOUT
    ROOT_LAYOUT --> GLOBAL_CSS
    ROOT_LAYOUT --> HOME_PAGE
    HOME_PAGE --> PAGE_CSS
    HOME_PAGE --> BROWSER
```

## Frontend Development Commands

```mermaid
flowchart LR
    DEVELOPER[Developer]
    INSTALL[npm install]
    DEV[npm run dev]
    LINT[npm run lint]
    BUILD[npm run build]
    PACKAGE[package.json]
    LOCK[package-lock.json]
    NODE_MODULES[node_modules]
    NEXT_OUTPUT[.next]

    DEVELOPER --> INSTALL
    INSTALL --> PACKAGE
    INSTALL --> LOCK
    INSTALL --> NODE_MODULES

    DEVELOPER --> DEV
    DEV --> PACKAGE
    DEV --> NEXT_OUTPUT

    DEVELOPER --> LINT
    LINT --> PACKAGE

    DEVELOPER --> BUILD
    BUILD --> PACKAGE
    BUILD --> NEXT_OUTPUT
```