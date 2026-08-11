<!-- File: /docs/ANALYTICS_DESIGN.md -->

# Phase 6 Track E — Analytics Design

## Purpose

Track E provides authenticated study-performance analytics.

The final feature combines canonical study-feature data to help students
understand:

- their available study materials;
- quiz performance;
- flashcard performance;
- strong topics;
- weak topics;
- study activity and performance trends.

## Current Independent Scope

The partial Track E implementation is designed to be mergeable before Tracks
A and B are complete.

The current implementation includes:

- authenticated Analytics API;
- Analytics schemas;
- Analytics dependency injection;
- Analytics service layer;
- canonical Analytics repository;
- authenticated subject counts;
- authenticated study-material counts;
- authenticated ready-study-material counts;
- reporting-period contracts;
- explicit unavailable states for deferred metrics;
- controlled canonical-data error handling;
- service, repository, endpoint, and router tests.

## Current Endpoint

```text
GET /api/analytics/overview

## Deferred Integrations

The following metrics require canonical data from other Phase 6 tracks:

| Metric | Dependency |
|---|---|
| Quiz accuracy | Track B |
| Quiz topic performance | Track B |
| Flashcard performance | Track A |
| Strong topics | Track B and optionally Track A |
| Weak topics | Track B and optionally Track A |
| General study duration | Future canonical study-activity source |

Track E must not create replacement quiz, flashcard, or activity tables merely
to enable early analytics development.

## Canonical Data Principle

Analytics reads and aggregates canonical feature data.

```text
Feature Data
    |
    v
Analytics Provider
    |
    v
Analytics Service
    |
    v
Authenticated Analytics API


### Canonical metrics available before Track A/B integration

The current backend can safely provide authenticated counts from canonical
Phase 3 study data:

- total subject count;
- total study-material count;
- ready study-material count.

These values are read directly from the existing `subjects` and `study_files`
tables and are scoped using the authenticated user's ID.

Performance metrics remain explicitly unavailable until their canonical feature
sources are merged.

## Track B Quiz Analytics Integration

Track B is now integrated into the Analytics service.

Canonical Quiz performance evidence comes from:

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