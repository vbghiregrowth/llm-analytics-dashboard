"""
LLM traffic detection logic — combines referrer, UTM, and user-agent signals.
"""

from __future__ import annotations

from typing import Optional
import pandas as pd
from config import ALL_REFERRER_DOMAINS, ALL_UTM_SOURCES, ALL_USER_AGENTS


def classify_source(source: str, medium: str = "", user_agent: str = "") -> str | None:
    """
    Classify a traffic source as an LLM or return None.
    Checks referrer domain, UTM source, and user-agent in priority order.
    """
    source_lower = (source or "").lower().strip()
    medium_lower = (medium or "").lower().strip()
    ua_lower = (user_agent or "").lower().strip()

    # 1. Check referrer domain match
    for domain, llm_name in ALL_REFERRER_DOMAINS.items():
        if domain in source_lower:
            return llm_name

    # 2. Check UTM source match
    for utm, llm_name in ALL_UTM_SOURCES.items():
        if utm == source_lower or utm in source_lower:
            return llm_name

    # 3. Check medium for LLM indicators
    if medium_lower in ("ai", "llm", "chatbot", "ai-referral"):
        return _guess_from_source(source_lower)

    # 4. Check user-agent match
    if ua_lower:
        for ua_pattern, llm_name in ALL_USER_AGENTS.items():
            if ua_pattern in ua_lower:
                return llm_name

    return None


def _guess_from_source(source: str) -> str:
    """Try to match a source string to an LLM name, or return 'Unknown LLM'."""
    for utm, llm_name in ALL_UTM_SOURCES.items():
        if utm in source:
            return llm_name
    return "Unknown LLM"


def tag_llm_traffic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'llm_source' and 'is_llm' columns to a DataFrame.

    Expects columns: 'source' (required), 'medium' (optional), 'user_agent' (optional).
    """
    if df.empty:
        df["llm_source"] = pd.Series(dtype=str)
        df["is_llm"] = pd.Series(dtype=bool)
        return df

    df = df.copy()
    medium_col = "medium" if "medium" in df.columns else None
    ua_col = "user_agent" if "user_agent" in df.columns else None

    df["llm_source"] = df.apply(
        lambda row: classify_source(
            source=row.get("source", ""),
            medium=row.get(medium_col, "") if medium_col else "",
            user_agent=row.get(ua_col, "") if ua_col else "",
        ),
        axis=1,
    )
    df["is_llm"] = df["llm_source"].notna()
    df["llm_source"] = df["llm_source"].fillna("Other")
    return df


def aggregate_llm_traffic(df: pd.DataFrame, metric_cols: list[str]) -> pd.DataFrame:
    """
    Aggregate metrics by LLM source.
    Returns a DataFrame with llm_source as index and summed metrics.
    """
    if df.empty or "llm_source" not in df.columns:
        return pd.DataFrame()

    llm_df = df[df["is_llm"]].copy()
    if llm_df.empty:
        return pd.DataFrame()

    return llm_df.groupby("llm_source")[metric_cols].sum().sort_values(
        metric_cols[0], ascending=False
    )


def get_llm_trend(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """
    Get daily LLM traffic trend, pivoted by LLM source.
    Returns a DataFrame with date as index and LLM sources as columns.
    """
    if df.empty or "llm_source" not in df.columns:
        return pd.DataFrame()

    llm_df = df[df["is_llm"]].copy()
    if llm_df.empty:
        return pd.DataFrame()

    pivot = llm_df.pivot_table(
        index=date_col,
        columns="llm_source",
        values="sessions",
        aggfunc="sum",
        fill_value=0,
    )
    pivot.index = pd.to_datetime(pivot.index)
    return pivot.sort_index()
