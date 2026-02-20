"""
Google Analytics 4 Data API connector.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    FilterExpression,
    Filter,
    FilterExpressionList,
)

from auth import get_ga4_credentials
from config import GA4_DIMENSIONS, GA4_METRICS, ALL_REFERRER_DOMAINS


class GA4Connector:
    def __init__(self, property_id: str):
        self.property_id = f"properties/{property_id}"
        self._client = None

    def _get_client(self) -> BetaAnalyticsDataClient:
        if self._client is None:
            credentials, error = get_ga4_credentials()
            if error:
                raise ConnectionError(error)
            self._client = BetaAnalyticsDataClient(credentials=credentials)
        return self._client

    def _run_report(
        self,
        dimensions: list[str],
        metrics: list[str],
        date_range_days: int = 30,
        dimension_filter: FilterExpression | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """Run a GA4 report and return results as a DataFrame."""
        client = self._get_client()

        if start_date and end_date:
            dr = DateRange(start_date=start_date, end_date=end_date)
        else:
            end = datetime.now()
            start = end - timedelta(days=date_range_days)
            dr = DateRange(
                start_date=start.strftime("%Y-%m-%d"),
                end_date=end.strftime("%Y-%m-%d"),
            )

        request = RunReportRequest(
            property=self.property_id,
            date_ranges=[dr],
            dimensions=[Dimension(name=d) for d in dimensions],
            metrics=[Metric(name=m) for m in metrics],
            dimension_filter=dimension_filter,
            limit=10000,
        )

        response = client.run_report(request)
        return self._response_to_dataframe(response, dimensions, metrics)

    def _response_to_dataframe(self, response, dimensions, metrics) -> pd.DataFrame:
        """Convert a GA4 API response to a pandas DataFrame."""
        rows = []
        for row in response.rows:
            record = {}
            for i, dim in enumerate(dimensions):
                record[dim] = row.dimension_values[i].value
            for i, met in enumerate(metrics):
                val = row.metric_values[i].value
                try:
                    record[met] = float(val)
                except ValueError:
                    record[met] = val
            rows.append(record)
        return pd.DataFrame(rows)

    def get_all_traffic_by_source(
        self, date_range_days: int = 30, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """Get all traffic broken down by source and medium."""
        df = self._run_report(
            dimensions=[
                GA4_DIMENSIONS["source"],
                GA4_DIMENSIONS["medium"],
                GA4_DIMENSIONS["date"],
            ],
            metrics=[
                GA4_METRICS["sessions"],
                GA4_METRICS["users"],
                GA4_METRICS["pageviews"],
                GA4_METRICS["avg_session_duration"],
                GA4_METRICS["engagement_rate"],
            ],
            date_range_days=date_range_days,
            start_date=start_date,
            end_date=end_date,
        )
        # Rename columns for consistency
        df = df.rename(columns={
            GA4_DIMENSIONS["source"]: "source",
            GA4_DIMENSIONS["medium"]: "medium",
            GA4_DIMENSIONS["date"]: "date",
            GA4_METRICS["sessions"]: "sessions",
            GA4_METRICS["users"]: "users",
            GA4_METRICS["pageviews"]: "pageviews",
            GA4_METRICS["avg_session_duration"]: "avg_session_duration",
            GA4_METRICS["engagement_rate"]: "engagement_rate",
        })
        return df

    def get_landing_pages_by_source(
        self, date_range_days: int = 30, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """Get landing page data broken down by source."""
        df = self._run_report(
            dimensions=[
                GA4_DIMENSIONS["source"],
                GA4_DIMENSIONS["landing_page"],
            ],
            metrics=[
                GA4_METRICS["sessions"],
                GA4_METRICS["users"],
                GA4_METRICS["engagement_rate"],
            ],
            date_range_days=date_range_days,
            start_date=start_date,
            end_date=end_date,
        )
        df = df.rename(columns={
            GA4_DIMENSIONS["source"]: "source",
            GA4_DIMENSIONS["landing_page"]: "landing_page",
            GA4_METRICS["sessions"]: "sessions",
            GA4_METRICS["users"]: "users",
            GA4_METRICS["engagement_rate"]: "engagement_rate",
        })
        return df

    def get_traffic_with_campaign(
        self, date_range_days: int = 30, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """Get traffic data including campaign (UTM) parameters."""
        df = self._run_report(
            dimensions=[
                GA4_DIMENSIONS["source"],
                GA4_DIMENSIONS["medium"],
                GA4_DIMENSIONS["campaign"],
                GA4_DIMENSIONS["date"],
            ],
            metrics=[
                GA4_METRICS["sessions"],
                GA4_METRICS["users"],
            ],
            date_range_days=date_range_days,
            start_date=start_date,
            end_date=end_date,
        )
        df = df.rename(columns={
            GA4_DIMENSIONS["source"]: "source",
            GA4_DIMENSIONS["medium"]: "medium",
            GA4_DIMENSIONS["campaign"]: "campaign",
            GA4_DIMENSIONS["date"]: "date",
            GA4_METRICS["sessions"]: "sessions",
            GA4_METRICS["users"]: "users",
        })
        return df
