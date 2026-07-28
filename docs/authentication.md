<!-- File: /docs/authentication.md -->
<!-- Purpose: Documents the authentication routes, session flow, security boundaries, and implementation phases. -->

# Authentication Architecture

The STS Capstone Project uses Supabase Auth with email and password.

Authentication sessions are stored in cookies through the Supabase SSR package and refreshed through the Next.js Proxy.

## Authentication Components

```text
Supabase Auth
├── Email and password registration
├── Email confirmation
├── Password-based login
├── Session refresh
└── Logout

Next.js Frontend
├── Public authentication pages
├── Server Actions
├── Email-confirmation Route Handler
├── Session Proxy
├── Protected route checks
└── Authenticated Supabase clients

Supabase Database
├── auth.users
├── public.profiles
├── New-user profile trigger
└── Profile Row Level Security
```

## Planned Public Routes

| Route | Purpose |
|---|---|
| `/login` | Allows an existing student to sign in |
| `/register` | Creates a new student account |
| `/register/check-email` | Tells the student to confirm their email |
| `/auth/confirm` | Verifies the email-confirmation token |
| `/auth/auth-code-error` | Shows a friendly confirmation-link error |

## Planned Protected Routes

```text
/dashboard
/subjects
/files
/tasks
/study-plan
/calendar
/progress
/assistant
/analytics
/settings
```

Unauthenticated visitors attempting to open a protected page will be redirected to:

```text
/login
```

The original route may be stored in a safe `next` query parameter so that the student can return after signing in.

## Registration Flow

```mermaid
sequenceDiagram
    actor Student
    participant Register as Registration Page
    participant Action as Registration Server Action
    participant Supabase as Supabase Auth
    participant Trigger as on_auth_user_created
    participant Profile as public.profiles
    participant Email as Confirmation Email

    Student->>Register: Enters name, email, and password
    Register->>Action: Submits registration form
    Action->>Supabase: Calls auth.signUp
    Supabase->>Trigger: Creates auth.users row
    Trigger->>Profile: Creates profile row
    Supabase->>Email: Sends confirmation email
    Action-->>Student: Redirects to check-email page
```

## Email-Confirmation Flow

```mermaid
sequenceDiagram
    actor Student
    participant Email as Confirmation Email
    participant Confirm as /auth/confirm
    participant Supabase as Supabase Auth
    participant Dashboard as Dashboard or Onboarding

    Student->>Email: Selects confirmation link
    Email->>Confirm: Sends token hash and confirmation type
    Confirm->>Supabase: Verifies the one-time token
    Supabase-->>Confirm: Creates authenticated session
    Confirm-->>Dashboard: Redirects confirmed student
```

## Login Flow

```mermaid
sequenceDiagram
    actor Student
    participant Login as Login Page
    participant Action as Login Server Action
    participant Supabase as Supabase Auth
    participant Proxy as Next.js Proxy
    participant App as Protected Application

    Student->>Login: Enters email and password
    Login->>Action: Submits login form
    Action->>Supabase: Calls signInWithPassword
    Supabase-->>Action: Returns authenticated session
    Action-->>App: Redirects student
    App->>Proxy: Sends request with session cookies
    Proxy->>Supabase: Validates and refreshes claims
    Proxy-->>App: Returns synchronized cookies
```

## Session Security Rules

1. Use the Supabase publishable key in the frontend.
2. Never expose the Supabase secret key to browser code.
3. Store frontend sessions in secure authentication cookies managed by Supabase SSR.
4. Use validated claims or a fresh user lookup for authorization decisions.
5. Do not trust client-submitted user identifiers.
6. Keep profile access protected through Row Level Security.
7. Redirect unauthenticated users away from protected application pages.
8. Do not include passwords, tokens, or session values in logs.

## Authentication Route Decisions

| Situation | Expected destination |
|---|---|
| New account awaiting confirmation | `/register/check-email` |
| Successful email confirmation | `/dashboard` or `/onboarding` |
| Successful login | `/dashboard` or `/onboarding` |
| Invalid confirmation link | `/auth/auth-code-error` |
| Unauthenticated protected-route access | `/login` |
| Authenticated visit to login/register | `/dashboard` or `/onboarding` |
| Successful logout | `/login` |

## Onboarding Gate

After authentication, the application will read:

```text
public.profiles.onboarding_completed
```

Expected behavior:

```text
false → /onboarding
true  → /dashboard
```

The onboarding redirect will be implemented after the core registration and login flow is working.

## Current Implementation Status

```text
Phase 1H.1: Authentication architecture complete
Phase 1H.2: Session Proxy foundation complete
Phase 1H.3: Shared validation and action-state types complete
Phase 1H.4: Registration Server Action and interface complete
Phase 1H.5: Email-confirmation callback pending
Phase 1H.6: Password login pending