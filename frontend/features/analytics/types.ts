// File: /frontend/features/analytics/types.ts
// Purpose: Defines frontend contracts for authenticated
// study Analytics overview data.

export const ANALYTICS_PERIODS = [
  "all_time",
  "last_7_days",
  "last_30_days",
] as const;

export type AnalyticsPeriod =
  (typeof ANALYTICS_PERIODS)[number];

export type AnalyticsAvailability =
  | "available"
  | "unavailable";

export type AnalyticsDataState =
  | "partial"
  | "ready";

export type AnalyticsCountScope =
  "current_inventory";

export interface AnalyticsMetric {
  availability:
    AnalyticsAvailability;

  value:
    number | null;

  sample_size:
    number;

  message:
    string | null;
}

export interface AnalyticsCountMetric {
  availability:
    AnalyticsAvailability;

  value:
    number | null;

  scope:
    AnalyticsCountScope;

  message:
    string | null;
}

export interface AnalyticsTopicPerformance {
  topic:
    string;

  score_percent:
    number;

  sample_size:
    number;
}

export interface AnalyticsOverviewResponse {
  period:
    AnalyticsPeriod;

  data_state:
    AnalyticsDataState;

  subject_count:
    AnalyticsCountMetric;

  study_material_count:
    AnalyticsCountMetric;

  ready_study_material_count:
    AnalyticsCountMetric;

  quiz_accuracy_percent:
    AnalyticsMetric;

  flashcard_performance_percent:
    AnalyticsMetric;

  study_minutes:
    AnalyticsMetric;

  strong_topics:
    AnalyticsTopicPerformance[];

  weak_topics:
    AnalyticsTopicPerformance[];
}

export interface AnalyticsApiErrorResponse {
  detail?:
    unknown;

  message?:
    unknown;

  error_code?:
    unknown;
}

export interface AnalyticsPeriodOption {
  value:
    AnalyticsPeriod;

  label:
    string;
}

export const ANALYTICS_PERIOD_OPTIONS:
  readonly AnalyticsPeriodOption[] = [
    {
      value:
        "all_time",
      label:
        "All Time",
    },
    {
      value:
        "last_30_days",
      label:
        "Last 30 Days",
    },
    {
      value:
        "last_7_days",
      label:
        "Last 7 Days",
    },
  ];