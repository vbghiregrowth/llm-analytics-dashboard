"""
Google Search Console API connector.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
from googleapiclient.discovery import build

from auth import get_gsc_credentials


class GSCConnector:
    def __init__(self, site_url: str):
        self.site_url = site_url
        self._service = None

    def _get_service(self):
        if self._service is None:
            credentials, error = get_gsc_credentials()
            if error:
                raise ConnectionError(error)
            self._service = build("searchconsole", "v1", credentials=credentials)
        return self._service

    def get_queries(
        self,
        date_range_days: int = 30,
        start_date: str | None = None,
        end_date: str | None = None,
        row_limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Get search queries with clicks, impressions, CTR, and position.
        """
        service = self._get_service()

        if not start_date or not end_date:
            end_dt = datetime.now() - timedelta(days=3)  # GSC data has ~3 day lag
            start_dt = end_dt - timedelta(days=date_range_days)
            start_date = start_dt.strftime("%Y-%m-%d")
            end_date = end_dt.strftime("%Y-%m-%d")

        request = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query"],
            "rowLimit": row_limit,
            "dataState": "final",
        }

        response = (
            service.searchanalytics()
            .query(siteUrl=self.site_url, body=request)
            .execute()
        )

        return self._parse_response(response, dimensions=["query"])

    def get_queries_by_page(
        self,
        date_range_days: int = 30,
        start_date: str | None = None,
        end_date: str | None = None,
        row_limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Get search queries broken down by page.
        """
        service = self._get_service()

        if not start_date or not end_date:
            end_dt = datetime.now() - timedelta(days=3)
            start_dt = end_dt - timedelta(days=date_range_days)
            start_date = start_dt.strftime("%Y-%m-%d")
            end_date = end_dt.strftime("%Y-%m-%d")

        request = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query", "page"],
            "rowLimit": row_limit,
            "dataState": "final",
        }

        response = (
            service.searchanalytics()
            .query(siteUrl=self.site_url, body=request)
            .execute()
        )

        return self._parse_response(response, dimensions=["query", "page"])

    def get_pages(
        self,
        date_range_days: int = 30,
        start_date: str | None = None,
        end_date: str | None = None,
        row_limit: int = 500,
    ) -> pd.DataFrame:
        """Get page-level search performance."""
        service = self._get_service()

        if not start_date or not end_date:
            end_dt = datetime.now() - timedelta(days=3)
            start_dt = end_dt - timedelta(days=date_range_days)
            start_date = start_dt.strftime("%Y-%m-%d")
            end_date = end_dt.strftime("%Y-%m-%d")

        request = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["page"],
            "rowLimit": row_limit,
            "dataState": "final",
        }

        response = (
            service.searchanalytics()
            .query(siteUrl=self.site_url, body=request)
            .execute()
        )

        return self._parse_response(response, dimensions=["page"])

    def get_queries_by_date(
        self,
        date_range_days: int = 30,
        start_date: str | None = None,
        end_date: str | None = None,
        row_limit: int = 5000,
    ) -> pd.DataFrame:
        """Get search queries broken down by date."""
        service = self._get_service()

        if not start_date or not end_date:
            end_dt = datetime.now() - timedelta(days=3)
            start_dt = end_dt - timedelta(days=date_range_days)
            start_date = start_dt.strftime("%Y-%m-%d")
            end_date = end_dt.strftime("%Y-%m-%d")

        request = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query", "date"],
            "rowLimit": row_limit,
            "dataState": "final",
        }

        response = (
            service.searchanalytics()
            .query(siteUrl=self.site_url, body=request)
            .execute()
        )

        return self._parse_response(response, dimensions=["query", "date"])

    def _parse_response(
        self, response: dict, dimensions: list[str]
    ) -> pd.DataFrame:
        """Parse a Search Console API response into a DataFrame."""
        rows = response.get("rows", [])
        if not rows:
            return pd.DataFrame(
                columns=dimensions + ["clicks", "impressions", "ctr", "position"]
            )

        records = []
        for row in rows:
            record = {}
            for i, dim in enumerate(dimensions):
                record[dim] = row["keys"][i]
            record["clicks"] = row.get("clicks", 0)
            record["impressions"] = row.get("impressions", 0)
            record["ctr"] = row.get("ctr", 0.0)
            record["position"] = row.get("position", 0.0)
            records.append(record)

        return pd.DataFrame(records)
