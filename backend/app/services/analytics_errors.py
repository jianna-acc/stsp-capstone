# File: /backend/app/services/analytics_errors.py
# Purpose: Defines controlled errors raised by the Analytics feature.


class AnalyticsError(Exception):
    """Base exception for controlled Analytics failures."""


class AnalyticsRepositoryError(AnalyticsError):
    """Raised when canonical Analytics data cannot be read safely."""