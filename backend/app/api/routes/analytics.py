# File: /backend/app/api/routes/analytics.py
# Purpose: Provides authenticated study analytics endpoints.

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.api.analytics_dependency import get_analytics_service
from app.api.authenticated_user_dependency import (
    AuthenticatedUser,
    require_authenticated_user,
)
from app.schemas.analytics import (
    AnalyticsApiErrorResponse,
    AnalyticsOverviewResponse,
    AnalyticsPeriod,
)
from app.services.analytics_errors import AnalyticsRepositoryError
from app.services.analytics_service import AnalyticsService

router = APIRouter(
    prefix="/analytics",
    tags=[
        "analytics",
    ],
)


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": (
                "Missing, invalid, or expired student authentication."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": AnalyticsApiErrorResponse,
            "description": (
                "Canonical analytics data is temporarily unavailable."
            ),
        },
    },
)
async def get_analytics_overview(
    authenticated_user: Annotated[
        AuthenticatedUser,
        Depends(
            require_authenticated_user,
        ),
    ],
    service: Annotated[
        AnalyticsService,
        Depends(
            get_analytics_service,
        ),
    ],
    period: Annotated[
        AnalyticsPeriod,
        Query(
            description=(
                "Reporting period for period-sensitive performance "
                "analytics. Current inventory counts are not "
                "period-filtered."
            ),
        ),
    ] = AnalyticsPeriod.ALL_TIME,
) -> AnalyticsOverviewResponse | JSONResponse:
    """Return the analytics overview for the authenticated student."""

    try:
        return service.get_overview(
            user_id=authenticated_user.user_id,
            period=period,
        )
    except AnalyticsRepositoryError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": (
                    "Analytics data is temporarily unavailable."
                ),
            },
        )