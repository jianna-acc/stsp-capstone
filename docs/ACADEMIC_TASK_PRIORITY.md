<!--
File: /docs/ACADEMIC_TASK_PRIORITY.md
Purpose: Documents the deterministic academic-task priority engine,
its data sources, scoring rules, fallbacks, and API integration.
-->

# Academic Task Priority Engine

## Overview

STUDY AI ranks a student's academic tasks using a deterministic
priority engine.

The priority engine does not use generative AI. It calculates an
explainable score from task information and student learning context.

Each active academic task receives a priority score from 0 to 100.
Higher scores indicate tasks that should generally receive attention
sooner.

The prioritized task endpoint is:

```text
GET /api/academic-tasks/prioritized

The endpoint only processes tasks owned by the authenticated student.

Priority Factors

The total score uses seven weighted factors.

Factor	Weight
Deadline proximity	30%
Task difficulty	20%
Estimated completion time	15%
Output confidence	15%
Previous performance	10%
Available study time	5%
Task status	5%
Total	100%

The calculation is:

priority =
    deadline_score × 0.30
  + difficulty_score × 0.20
  + estimated_time_score × 0.15
  + output_confidence_score × 0.15
  + previous_performance_score × 0.10
  + available_study_time_score × 0.05
  + status_score × 0.05

The final score is rounded to one decimal place.

Completed and cancelled tasks always receive a total priority score
of 0.

Deadline Proximity

Deadline urgency increases as the deadline approaches.

Time until deadline	Score
Overdue or within 24 hours	100
Within 72 hours	85
Within 7 days	70
Within 14 days	50
Within 30 days	25
More than 30 days	10
Task Difficulty
Difficulty	Score
Easy	25
Medium	60
Hard	100
Estimated Completion Time

Longer tasks receive higher urgency because they require more time to
complete.

Estimated duration	Score
Up to 30 minutes	20
Up to 60 minutes	40
Up to 120 minutes	60
Up to 240 minutes	80
More than 240 minutes	100
Output Confidence

STUDY AI stores reusable student confidence ratings for academic
output skills rather than confidence per subject.

Supported confidence categories are:

writing
computation
research
presentation
creative
reading_analysis
memorization

Confidence is rated from 1 to 5.

Lower confidence increases task urgency.

confidence urgency = (5 - confidence level) × 25
Confidence	Priority factor score
1	100
2	75
3	50
4	25
5	0

Academic tasks also support:

mixed
other

For mixed, the engine uses the average of all seven confidence
categories when all seven values are available.

For other, or when confidence data is unavailable, the engine uses
the neutral score of 50.

Previous Performance

The engine reserves 10% of the score for previous academic
performance.

The intended calculation is:

performance urgency = 100 - previous performance percent

A lower historical performance therefore increases urgency.

The quiz/performance subsystem is not yet the source of this value.
Until real performance data becomes available, the priority engine
uses the neutral score of 50.

No fabricated performance values are stored.

Available Study Time

Study availability is calculated from the student's recurring weekly
availability and profile timezone.

The data sources are:

profiles.timezone
study_availability

study_availability.day_of_week follows ISO weekday numbering:

1 = Monday
2 = Tuesday
3 = Wednesday
4 = Thursday
5 = Friday
6 = Saturday
7 = Sunday

Only availability between the current time and the task deadline is
counted.

The engine compares available minutes with the estimated task
duration.

Available / estimated time	Score
No usable time	100
Less than 1×	100
Less than 1.5×	80
Less than 2×	60
Less than 3×	40
At least 3×	20

If availability data is missing entirely, the orchestration service
uses the neutral score of 50 rather than assuming the student has zero
available time.

Timezone calculations use Python zoneinfo.

The backend includes the tzdata dependency so IANA timezone data is
available in environments such as Windows.

Task Status
Status	Score
Pending	50
In progress	100
Completed	0
Cancelled	0

Completed and cancelled tasks receive a final total priority of 0.

Priority Context

The priority context repository loads the following authenticated
student data:

profiles
    timezone

learning_output_confidences
    output_type
    confidence_level

study_availability
    day_of_week
    start_time
    end_time

All queries are filtered using the authenticated student's user ID.

The context is loaded once when scoring a collection of tasks instead
of once for every task.

API Response

Endpoint:

GET /api/academic-tasks/prioritized

Optional query parameter:

limit

Range:

1 to 100

Example response structure:

{
  "items": [
    {
      "task": {
        "id": "uuid",
        "subject_id": "uuid",
        "title": "Research assignment",
        "description": "Complete the first draft.",
        "deadline": "2026-08-10T12:00:00Z",
        "estimated_minutes": 120,
        "difficulty": "medium",
        "task_type": "assignment",
        "output_type": "writing",
        "status": "pending",
        "created_at": "2026-08-09T10:00:00Z",
        "updated_at": "2026-08-09T10:00:00Z"
      },
      "priority": {
        "total_score": 72.5,
        "deadline_score": 85.0,
        "difficulty_score": 60.0,
        "estimated_time_score": 60.0,
        "output_confidence_score": 75.0,
        "previous_performance_score": 50.0,
        "available_study_time_score": 80.0,
        "status_score": 50.0
      }
    }
  ]
}

Tasks are returned in descending total priority order.

Tie breaking uses:

earlier deadline
earlier creation time
task ID
Backend Components
Schemas
backend/app/schemas/academic_task.py
backend/app/schemas/academic_task_priority.py
Repositories
backend/app/repositories/academic_task_repository.py
backend/app/repositories/academic_task_priority_context_repository.py
Services
backend/app/services/academic_task_service.py
backend/app/services/academic_task_priority.py
backend/app/services/academic_task_priority_context.py
backend/app/services/academic_task_priority_service.py
API
backend/app/api/academic_task_dependency.py
backend/app/api/academic_task_priority_dependency.py
backend/app/api/routes/academic_tasks.py
Design Principles

The Academic Task priority engine follows these principles:

deterministic rather than generative
explainable factor scores
authenticated student ownership
no fabricated academic-performance values
neutral fallbacks for unavailable context
timezone-aware scheduling
reusable confidence by academic output type
one context load per task batch
bounded API results
completed and cancelled work does not compete with active work

Future quiz-performance integration can replace the neutral previous
performance input without changing the overall priority-engine
contract.