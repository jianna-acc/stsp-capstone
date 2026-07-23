<!-- File: /docs/ARCHITECTURE.md -->

# STS Capstone Project Architecture

This document shows the current implementation and the planned final architecture of the STS Capstone Project.

The diagrams use Mermaid syntax. View this file in a Markdown viewer that supports Mermaid.

# Architecture Status

| Label | Meaning |
|---|---|
| Implemented | The file or connection currently exists and has been tested |
| In Progress | Part of the current development phase |
| Planned | Expected in a future phase but not yet implemented |

# Planned Final System Architecture

The following diagram is the target architecture of the completed application.

```mermaid
flowchart LR
    USER["Student"]

    subgraph FRONTEND["Next.js Frontend"]
        UI["Mantine User Interface"]
        AUTH_UI["Login and Registration"]
        DASHBOARD["Dashboard"]
        FILE_UI["File Upload Interface"]
        CHAT_UI["AI Assistant Interface"]
        QUIZ_UI["Reviewer and Quiz Interface"]
        PLAN_UI["Tasks and Study Plan Interface"]
        API_SERVICE["Frontend API Service"]
        SUPABASE_CLIENT["Supabase Browser Client"]
    end

    subgraph BACKEND["FastAPI Backend"]
        API["FastAPI Routes"]
        AUTH_SERVICE["Authentication Validation"]
        FILE_SERVICE["File Processing Service"]
        RAG_SERVICE["Study Retrieval Service"]
        AI_SERVICE["Gemini AI Service"]
        QUIZ_SERVICE["Quiz and Reviewer Service"]
        PLAN_SERVICE["Task and Study Plan Service"]
    end

    subgraph SUPABASE["Supabase Platform"]
        AUTH["Supabase Authentication"]
        DATABASE[("PostgreSQL Database")]
        STORAGE[("Private File Storage")]
    end

    GEMINI["Gemini API"]

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

# Current Implemented Foundation

```mermaid
flowchart LR
    USER["Developer or Student"]
    BROWSER["Web Browser"]

    subgraph FRONTEND["Implemented Next.js Frontend"]
        ROOT_LAYOUT["app/layout.tsx"]
        PROVIDERS["app/providers.tsx"]
        HOME["app/page.tsx"]
        CHECK["MantineFoundationCheck.tsx"]
        COMPONENT_CSS["MantineFoundationCheck.module.css"]
        GLOBAL_CSS["app/globals.css"]
        THEME["theme/theme.ts"]
        COLORS["theme/colors.ts"]
        OVERRIDES["theme/components.ts"]
        POSTCSS["postcss.config.cjs"]
    end

    subgraph BACKEND_FOUNDATION["Backend Foundation In Progress"]
        REQUIREMENTS["requirements.in and requirements.txt"]
        ENV_TEMPLATE[".env.example"]
        ENV_LOCAL[".env - local only"]
        CONFIG["app/core/config.py"]
        PACKAGES["app package folders"]
    end

    USER --> BROWSER
    BROWSER --> ROOT_LAYOUT

    COLORS --> THEME
    OVERRIDES --> THEME
    THEME --> PROVIDERS

    ROOT_LAYOUT --> GLOBAL_CSS
    ROOT_LAYOUT --> PROVIDERS
    PROVIDERS --> HOME
    HOME --> CHECK
    COMPONENT_CSS --> CHECK
    POSTCSS --> COMPONENT_CSS

    REQUIREMENTS --> PACKAGES
    ENV_TEMPLATE -. copied locally .-> ENV_LOCAL
    ENV_LOCAL --> CONFIG
    CONFIG --> PACKAGES
```

# Frontend Provider Hierarchy

```mermaid
flowchart TD
    ROOT["RootLayout"]
    MANTINE["MantineProvider"]
    MODALS["ModalsProvider"]
    NOTIFICATIONS["Notifications"]
    APPLICATION["Application Pages and Components"]

    ROOT --> MANTINE
    MANTINE --> MODALS
    MODALS --> NOTIFICATIONS
    MODALS --> APPLICATION
```

# Frontend Development Flow

```mermaid
flowchart LR
    DEVELOPER["Developer"]
    INSTALL["npm install"]
    DEV["npm run dev"]
    LINT["npm run lint"]
    BUILD["npm run build"]
    PACKAGE["package.json"]
    LOCK["package-lock.json"]
    MODULES["node_modules - local only"]
    NEXT_OUTPUT[".next - generated"]

    DEVELOPER --> INSTALL
    INSTALL --> PACKAGE
    INSTALL --> LOCK
    INSTALL --> MODULES

    DEVELOPER --> DEV
    DEV --> PACKAGE
    DEV --> NEXT_OUTPUT

    DEVELOPER --> LINT
    LINT --> PACKAGE

    DEVELOPER --> BUILD
    BUILD --> PACKAGE
    BUILD --> NEXT_OUTPUT
```

# FastAPI Application Structure

```mermaid
flowchart TD
    CLIENT["Browser or API Client"]
    MAIN["app/main.py"]
    CORS["CORSMiddleware"]
    ROUTER["app/api/router.py"]
    HEALTH["app/api/health.py"]
    HEALTH_SCHEMA["app/schemas/health.py"]
    CONFIG["app/core/config.py"]
    ENV["backend/.env - local only"]
    TEST["tests/test_health.py"]
    DATABASE["app/database - future"]
    MODULES["app/modules - future"]
    SERVICES["app/services - future"]

    ENV --> CONFIG
    CONFIG --> MAIN
    CONFIG --> HEALTH

    CLIENT --> CORS
    CORS --> MAIN
    MAIN --> ROUTER
    ROUTER --> HEALTH
    HEALTH --> HEALTH_SCHEMA
    HEALTH --> CLIENT

    TEST --> MAIN
    TEST --> HEALTH
    TEST --> CORS

    ROUTER -. future .-> MODULES
    MODULES -. future .-> SERVICES
    SERVICES -. future .-> DATABASE
```

# Planned Phase 1 Frontend-to-Backend Health Check

This sequence is planned for the next backend and integration phases. The API service and health endpoint are not yet implemented.

```mermaid
sequenceDiagram
    actor Student
    participant Frontend as Next.js Frontend
    participant APIService as frontend/services/api.ts
    participant FastAPI as FastAPI Backend
    participant HealthRoute as GET /api/health

    Student->>Frontend: Opens the system-check page
    Student->>Frontend: Selects Check Backend
    Frontend->>APIService: Calls getApiHealth()
    APIService->>FastAPI: Sends GET /api/health
    FastAPI->>HealthRoute: Runs health check
    HealthRoute-->>FastAPI: Returns healthy response
    FastAPI-->>APIService: Returns JSON response
    APIService-->>Frontend: Returns health result
    Frontend-->>Student: Shows Backend Connected
```

# Planned Data Relationships

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
        string original_filename
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

# Repository Ownership

```mermaid
flowchart TD
    REPO["STS Capstone Repository"]

    REPO --> ROOT["Shared Root Files"]
    REPO --> FRONTEND_FOLDER["frontend"]
    REPO --> BACKEND_FOLDER["backend"]
    REPO --> SUPABASE_FOLDER["supabase"]
    REPO --> DOCS_FOLDER["docs"]

    ROOT --> MEMBER1["Member 1: Technical Lead"]

    FRONTEND_FOLDER --> MEMBER1
    FRONTEND_FOLDER --> MEMBER2["Member 2: UI and Design System"]

    BACKEND_FOLDER --> MEMBER3["Member 3: FastAPI and AI Services"]

    SUPABASE_FOLDER --> MEMBER4["Member 4: Database and Security"]

    DOCS_FOLDER --> MEMBER1
    DOCS_FOLDER --> MEMBER5["Member 5: Testing and Documentation"]
```

# Diagram Update Rules

Update this document when:

1. A new major service is introduced.
2. A planned connection becomes implemented.
3. A new database table is created.
4. A frontend feature begins calling a new endpoint.
5. A backend service starts using Gemini.
6. A module begins reading from Supabase Storage.
7. Ownership of a module changes.
8. A major connection is removed.