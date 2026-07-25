<!-- File: /supabase/README.md -->

# Supabase

This folder contains the database, authentication, storage, migration, and security files for the STS Capstone Project.

## Planned Responsibilities

- Student authentication
- Student profiles
- Subjects
- Uploaded-file records
- Academic tasks
- Study plans
- Quiz attempts
- Reviewer records
- Private file storage
- Row-level security policies

## Planned Structure

```text
supabase/
├── migrations/
├── policies/
├── seed.sql
└── README.md

## Current Development Workflow

The project currently uses a hosted Supabase development project.

Repository configuration:

```text
supabase/config.toml
```

Future schema changes will be stored as versioned SQL migrations:

```text
supabase/migrations/
```

The intended workflow is:

```text
Create migration
      ↓
Review SQL
      ↓
Preview remote changes
      ↓
Push to hosted development project
      ↓
Verify tables and policies
```

Docker-based local Supabase services are not currently used.

Do not run:

```text
supabase start
supabase db reset
```

Database changes should not be made directly in the Supabase Dashboard unless they are also recorded in a repository migration.