<!-- File: /docs/ANALYTICS_DESIGN.md -->
<!-- Purpose: Documents Phase 6 Track E Analytics, canonical metric sources, Flashcard review evidence, security, and validation. -->

# STUDY AI — Analytics Design

## Purpose

Phase 6 Track E provides authenticated study analytics using canonical data already stored by STUDY AI.

The Analytics feature helps a student understand:

- current subject and study-material inventory;
- Quiz performance;
- self-assessed Flashcard performance;
- strong Quiz topics;
- weak Quiz topics;
- future study-activity metrics when a trustworthy duration source becomes available.

Analytics does not fabricate performance values when canonical evidence does not exist.

---

# Current Status

Track E is implemented in code and independently validated for the canonical data sources currently available on the Track E branch.

Implemented Analytics sources are:

```text
subjects
study_files
quiz_attempts
quiz_attempt_answers
flashcard_review_events
```

The current implementation provides:

- authenticated subject counts;
- authenticated study-material counts;
- authenticated ready-study-material counts;
- weighted Quiz accuracy;
- Quiz topic-performance aggregation;
- strong-topic classification;
- weak-topic classification;
- self-assessed Flashcard performance;
- all-time reporting;
- last-7-days reporting;
- last-30-days reporting;
- an explicit unavailable state for general study duration;
- controlled canonical-data failure handling.

General study duration remains unavailable because the application does not yet have a canonical persisted study-duration source.

The Flashcard review migration has been applied to the shared remote database. Linked local and remote migration history is aligned through `20260811162000`, and a subsequent linked dry run reports that the remote database is up to date.

---

# Protected Analytics Endpoint

```text
GET /api/analytics/overview
```

Authentication is required.

The authenticated student's UUID is derived from the validated Supabase bearer token.

The request cannot provide or override a trusted `user_id`.

Supported reporting periods:

```text
all_time
last_7_days
last_30_days
```

Default:

```text
all_time
```

---

# Metric Scope

Inventory metrics represent the student's current stored resources and are not filtered by the selected performance period.

Current-inventory metrics are:

```text
subject_count
study_material_count
ready_study_material_count
```

Performance-period metrics are:

```text
quiz_accuracy_percent
flashcard_performance_percent
strong_topics
weak_topics
```

The selected period affects completed Quiz evidence through `completed_at` and Flashcard review evidence through `reviewed_at`.

---

# Canonical Data Principle

Analytics reads canonical feature data rather than maintaining replacement copies of feature state.

```text
Canonical Feature Data
        |
        v
Analytics Repository
        |
        v
Analytics Service
        |
        v
Authenticated Analytics API
```

Track E does not duplicate Quiz or Flashcard content merely for reporting.

---

# Quiz Analytics

Canonical Quiz evidence comes from:

```text
quiz_attempts
├── user_id
├── status
├── correct_count
├── question_count
└── completed_at

quiz_attempt_answers
├── attempt_id
├── topic
├── is_correct
└── answered_at
```

Only completed Quiz attempts are used for performance Analytics.

## Overall Quiz Accuracy

Overall accuracy is weighted by the number of questions:

```text
sum(correct_count)
------------------ × 100
sum(question_count)
```

Analytics does not average individual attempt percentages because attempts may contain different numbers of questions.

The Quiz metric `sample_size` represents the total number of completed Quiz questions included in the selected period.

When no completed Quiz attempts exist for the selected period, the source remains available but the metric has no value and a sample size of zero.

---

# Quiz Topic Performance

Topic performance is calculated from persisted Quiz answers.

Topic names are normalized case-insensitively for aggregation while retaining a stable display name.

For each topic:

```text
correct answers
--------------- × 100
total answers
```

The `sample_size` for a topic is the number of persisted answers included in that topic.

Track E follows Track B's Quiz topic classification threshold:

```text
Strong topic: accuracy >= 70%
Weak topic:   accuracy < 70%
```

This keeps Analytics consistent with the Quiz result feature.

---

# Flashcard Review Evidence

The original Track A Flashcard feature persists generated cards but does not persist whether a student knew an answer.

Track E therefore adds a minimal durable self-assessment signal instead of guessing performance from navigation.

After revealing a Flashcard answer, the student can choose:

```text
I Know This
Review Again
```

These actions create canonical review events in:

```text
flashcard_review_events
├── id
├── user_id
├── deck_id
├── card_position
├── outcome
├── reviewed_at
└── created_at
```

Supported outcomes:

```text
known
review_again
```

A review target is identified by:

```text
deck_id + card_position
```

The existing Flashcard schema guarantees that each position is unique within a deck.

The review persistence layer also verifies that the deck belongs to the authenticated student and that the requested card position exists.

---

# Flashcard Performance

Flashcard performance is explicitly a student self-assessment metric.

It is calculated as:

```text
known review events
------------------- × 100
all review events
```

For example:

```text
8 known
2 review_again
----------------
80% performance
```

The metric `sample_size` represents the number of persisted Flashcard review events in the selected period.

This value must not be interpreted as an automatically graded knowledge score.

When no review events exist for the selected period:

```text
availability = available
value = null
sample_size = 0
```

This is different from an unavailable data source.

---

# Flashcard Review API

Flashcard self-assessment is persisted through:

```text
POST /api/flashcards/{deck_id}/reviews
```

Representative request:

```json
{
  "card_position": 0,
  "outcome": "known"
}
```

Representative response:

```json
{
  "id": "review-uuid",
  "deck_id": "deck-uuid",
  "card_position": 0,
  "outcome": "known",
  "reviewed_at": "2026-08-11T08:00:00Z"
}
```

The trusted student identity comes from authentication and is never accepted from the request body.

---

# Security

Analytics and Flashcard review operations preserve authenticated ownership boundaries.

Important controls include:

1. Analytics repository queries are scoped to the authenticated student's UUID.
2. Quiz attempts are read only when owned by that student.
3. Quiz-answer topic evidence is loaded only from already owner-scoped completed attempts.
4. Flashcard review events store the authenticated student's UUID.
5. Flashcard review creation verifies that the deck belongs to that student.
6. Flashcard review creation verifies that the requested card position exists in that deck.
7. Browser clients cannot directly insert Flashcard review events.
8. Review writes pass through the protected FastAPI backend and trusted Supabase client.
9. Authenticated browser reads of review events are owner-scoped through RLS.
10. Controlled API errors do not expose database details or backend secrets.

---

# Data Availability

Current Track E metric state:

| Metric | Status | Canonical Source |
|---|---|---|
| Subject count | Available | `subjects` |
| Study-material count | Available | `study_files` |
| Ready study-material count | Available | `study_files.processing_status` |
| Quiz accuracy | Available | `quiz_attempts` |
| Strong topics | Available | `quiz_attempt_answers` |
| Weak topics | Available | `quiz_attempt_answers` |
| Flashcard performance | Available | `flashcard_review_events` |
| General study minutes | Unavailable | No canonical duration source yet |

Because at least one requested Analytics area remains unavailable, the overview currently reports:

```text
data_state = partial
```

---

# Track Dependencies

Track E currently depends on:

```text
Track A
└── Flashcard decks and cards

Track B
└── Quiz attempts and answer history
```

Track C and Track D are now synchronized into the Track E branch but are not required for the currently implemented Track E metrics.

Future integration may use their canonical data only when later Analytics requirements define trustworthy task, workload, scheduling, or study-plan evidence.

---

# Database Migration

Track E adds:

```text
20260811162000_create_flashcard_review_events.sql
```

The migration creates:

```text
public.flashcard_review_events
```

with:

- authenticated owner linkage;
- Flashcard deck linkage;
- stable card position;
- constrained self-assessment outcome;
- review timestamps;
- ownership/card validation;
- indexes;
- Row Level Security;
- restricted authenticated browser privileges;
- trusted service-role write access.

The migration has been applied to the shared remote database.

Track C and Track D migration files were first synchronized into the Track E branch and linked migration history was re-inspected. Local and remote history now match through `20260811162000`, and a subsequent `db push --linked --dry-run` reports that the remote database is up to date. No migration repair was required.

---

# Current Validation

Track E and its C/D synchronization have passed:

```text
Backend full suite:
1296 passed

Post-migration Track E targeted suite:
29 passed

Frontend full suite:
25 test files passed
153 tests passed

Focused C/D/E frontend suite:
6 test files passed
58 tests passed

Production frontend build:
successful

TypeScript:
successful

Ruff:
successful

pip check:
successful
```

The frontend lint run completed with zero errors and one unrelated existing warning in the subject page.

Known Python warnings are dependency/deprecation warnings and do not represent Track E test failures.

---

# Remaining Work

Track E's application code and shared database migration are complete for the available canonical Quiz and Flashcard evidence.

Live browser validation is complete. The Analytics overview loads successfully against the shared database, all supported reporting periods work, persisted Flashcard review evidence is reflected in Analytics, and general study time remains explicitly unavailable because no canonical actual study-duration source exists.

Future Analytics expansion may include:

- canonical study-duration tracking;
- task/workload analytics when trustworthy canonical task evidence is defined;
- study-plan adherence only when canonical completion or adherence evidence exists;
- calendar/schedule analytics;
- longer-term progress visualization.

These future metrics should be implemented only when their canonical sources exist.
