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

# Frontend-to-Backend Health Interface

```mermaid
flowchart LR
    PAGE["MantineFoundationCheck.tsx"]
    HEALTH_COMPONENT["BackendHealthCheck.tsx"]
    HEALTH_CSS["BackendHealthCheck.module.css"]
    API_SERVICE["frontend/services/api.ts"]
    API_TYPES["frontend/types/api.ts"]
    ENV_LOCAL["frontend/.env.local"]
    ENV_EXAMPLE["frontend/.env.example"]
    FASTAPI["FastAPI GET /api/health"]

    ENV_EXAMPLE -. copied locally .-> ENV_LOCAL
    ENV_LOCAL --> API_SERVICE
    API_TYPES --> API_SERVICE

    PAGE --> HEALTH_COMPONENT
    HEALTH_CSS --> HEALTH_COMPONENT
    HEALTH_COMPONENT --> API_SERVICE
    API_SERVICE --> FASTAPI
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

# Implemented Frontend-to-Backend Health Check

```mermaid
sequenceDiagram
    actor Developer
    participant Frontend as Next.js Frontend
    participant Component as BackendHealthCheck.tsx
    participant APIService as frontend/services/api.ts
    participant CORS as FastAPI CORSMiddleware
    participant HealthRoute as GET /api/health

    Developer->>Frontend: Opens http://localhost:3000
    Frontend->>Component: Displays idle state

    Developer->>Component: Selects Check backend
    Component->>Component: Displays loading state
    Component->>APIService: Calls getApiHealth()
    APIService->>APIService: Reads NEXT_PUBLIC_API_BASE_URL
    APIService->>CORS: Sends GET /api/health
    CORS->>HealthRoute: Allows configured frontend origin
    HealthRoute-->>CORS: Returns typed health response
    CORS-->>APIService: Returns 200 JSON response
    APIService->>APIService: Validates response structure
    APIService-->>Component: Returns ApiHealthResponse
    Component->>Component: Displays connected state
    Component-->>Developer: Shows service details
```

## Implemented Error and Retry Flow

```mermaid
sequenceDiagram
    actor Developer
    participant Component as BackendHealthCheck.tsx
    participant APIService as frontend/services/api.ts
    participant Backend as FastAPI Backend

    Developer->>Component: Selects Check again
    Component->>APIService: Calls getApiHealth()
    APIService-xBackend: Connection fails
    APIService-->>Component: Throws ApiRequestError
    Component-->>Developer: Displays Unavailable and Retry connection

    Developer->>Backend: Restarts FastAPI
    Developer->>Component: Selects Retry connection
    Component->>APIService: Calls getApiHealth()
    APIService->>Backend: Sends GET /api/health
    Backend-->>APIService: Returns 200 health response
    APIService-->>Component: Returns validated health data
    Component-->>Developer: Displays Connected
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

# Repository Tooling and Hosted Supabase Workflow

```mermaid
flowchart LR
    PACKAGE["Root package.json"]
    LOCK["Root package-lock.json"]
    CLI["Project-scoped Supabase CLI"]
    CONFIG["supabase/config.toml"]
    README["supabase/README.md"]
    MIGRATIONS["supabase/migrations - next database phase"]
    HOSTED["Hosted Supabase development project - next phase"]
    TEMP["supabase/.temp - local only after linking"]

    PACKAGE --> CLI
    LOCK --> CLI

    CLI --> CONFIG
    README --> CONFIG

    CONFIG -. link next phase .-> HOSTED
    CONFIG -. future .-> MIGRATIONS
    MIGRATIONS -. db push .-> HOSTED
    HOSTED -. local link metadata .-> TEMP
```

The repository uses a hosted Supabase development project. Docker-based local Supabase services are not part of the current workflow.

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

# Implemented Supabase Client Foundation

```mermaid
flowchart LR
    HOSTED["Hosted Supabase Development Project"]

    subgraph FRONTEND["Next.js Frontend"]
        FRONT_ENV["frontend/.env.local"]
        FRONT_CONFIG["lib/supabase/config.ts"]
        BROWSER["lib/supabase/client.ts"]
        SERVER["lib/supabase/server.ts"]
        COOKIES["Next.js cookies"]
    end

    subgraph BACKEND["FastAPI Backend"]
        BACK_ENV["backend/.env"]
        SETTINGS["app/core/config.py"]
        TRUSTED["app/database/supabase_client.py"]
    end

    FRONT_ENV --> FRONT_CONFIG
    FRONT_CONFIG --> BROWSER
    FRONT_CONFIG --> SERVER
    COOKIES --> SERVER

    BROWSER -. publishable key and RLS .-> HOSTED
    SERVER -. publishable key and user session .-> HOSTED

    BACK_ENV --> SETTINGS
    SETTINGS --> TRUSTED
    TRUSTED -. secret key and trusted access .-> HOSTED
```

The frontend browser and server clients use the publishable key. The FastAPI client uses the secret key and is restricted to trusted backend code.

# Profiles Database Foundation

```mermaid
flowchart TD
    AUTH["Supabase Auth: auth.users"]
    SIGNUP["Future registration flow"]
    TRIGGER["on_auth_user_created trigger"]
    PROFILE["public.profiles"]
    RLS["Profile Row Level Security"]
    BROWSER["Authenticated browser client"]
    SERVER["Trusted FastAPI client"]

    SIGNUP --> AUTH
    AUTH --> TRIGGER
    TRIGGER --> PROFILE

    BROWSER --> RLS
    RLS --> PROFILE

    SERVER --> PROFILE
```

The browser client may access only the signed-in student's profile through Row Level Security. The trusted FastAPI client may perform approved server-side operations using the backend secret key.

# Generated Supabase Database Types

```mermaid
flowchart LR
    MIGRATION["profiles migration"]
    HOSTED["Hosted Supabase public schema"]
    CLI["Supabase CLI gen types"]
    TYPES["frontend/types/database.ts"]
    BROWSER["Typed browser client"]
    SERVER["Typed Next.js server client"]
    FEATURES["Future profile and authentication features"]

    MIGRATION --> HOSTED
    HOSTED --> CLI
    CLI --> TYPES

    TYPES --> BROWSER
    TYPES --> SERVER

    BROWSER --> FEATURES
    SERVER --> FEATURES
```

Database migrations remain the source of schema changes. After a migration is applied to the hosted development project, the generated frontend database types must be refreshed and committed with the related code.