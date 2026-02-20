"""
LLM Traffic Analytics Dashboard
Visualizes traffic from LLMs (ChatGPT, Claude, Perplexity, etc.) using GA4 + Search Console.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from config import LLM_SOURCES, LLM_COLOR_MAP, DATE_RANGES
from ga4_connector import GA4Connector
from gsc_connector import GSCConnector
from llm_detector import tag_llm_traffic, aggregate_llm_traffic, get_llm_trend

# --- Page Config ---
st.set_page_config(
    page_title="LLM Traffic Analytics",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
st.sidebar.title("LLM Traffic Analytics")

ga4_property_id = st.sidebar.text_input(
    "GA4 Property ID",
    value=os.environ.get("GA4_PROPERTY_ID", ""),
    help="Numeric property ID from GA4 Admin > Property Details",
)

gsc_site_url = st.sidebar.text_input(
    "Search Console Site URL",
    value=os.environ.get("GSC_SITE_URL", ""),
    help="e.g. https://example.com or sc-domain:example.com",
)

date_range_label = st.sidebar.selectbox("Date Range", list(DATE_RANGES.keys()))
date_range_days = DATE_RANGES[date_range_label]

st.sidebar.markdown("---")
use_custom_dates = st.sidebar.checkbox("Use custom date range")
if use_custom_dates:
    col1, col2 = st.sidebar.columns(2)
    custom_start = col1.date_input("Start", datetime.now() - timedelta(days=30))
    custom_end = col2.date_input("End", datetime.now())
    start_date = custom_start.strftime("%Y-%m-%d")
    end_date = custom_end.strftime("%Y-%m-%d")
else:
    start_date = None
    end_date = None

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Tracked LLM Sources:** "
    + ", ".join(LLM_SOURCES.keys())
)
st.sidebar.markdown(
    "[Setup Guide](./setup_guide.md) · "
    "Built with Streamlit + GA4 Data API + Search Console API"
)


# --- Helper Functions ---
def show_error(message: str):
    st.error(message)
    st.info(
        "Make sure you have set up API credentials. "
        "See the setup_guide.md file for instructions."
    )
    st.stop()


@st.cache_data(ttl=600, show_spinner=False)
def load_ga4_traffic(_property_id, days, start, end):
    connector = GA4Connector(_property_id)
    return connector.get_all_traffic_by_source(
        date_range_days=days, start_date=start, end_date=end
    )


@st.cache_data(ttl=600, show_spinner=False)
def load_ga4_landing_pages(_property_id, days, start, end):
    connector = GA4Connector(_property_id)
    return connector.get_landing_pages_by_source(
        date_range_days=days, start_date=start, end_date=end
    )


@st.cache_data(ttl=600, show_spinner=False)
def load_gsc_queries(_site_url, days, start, end):
    connector = GSCConnector(_site_url)
    return connector.get_queries(
        date_range_days=days, start_date=start, end_date=end
    )


@st.cache_data(ttl=600, show_spinner=False)
def load_gsc_pages(_site_url, days, start, end):
    connector = GSCConnector(_site_url)
    return connector.get_pages(
        date_range_days=days, start_date=start, end_date=end
    )


@st.cache_data(ttl=600, show_spinner=False)
def load_gsc_queries_by_page(_site_url, days, start, end):
    connector = GSCConnector(_site_url)
    return connector.get_queries_by_page(
        date_range_days=days, start_date=start, end_date=end
    )


# --- Main Dashboard ---
st.title("LLM Traffic Analytics Dashboard")
st.caption(f"Showing data for the {date_range_label.lower()}")

if not ga4_property_id:
    st.warning("Enter your GA4 Property ID in the sidebar to get started.")
    st.info("See setup_guide.md for instructions on getting your Property ID and API credentials.")
    st.stop()

# --- Load GA4 Data ---
try:
    with st.spinner("Loading GA4 traffic data..."):
        traffic_df = load_ga4_traffic(ga4_property_id, date_range_days, start_date, end_date)
except Exception as e:
    show_error(f"Failed to connect to GA4: {e}")

if traffic_df.empty:
    st.warning("No traffic data found for this date range.")
    st.stop()

# Tag LLM traffic
traffic_df = tag_llm_traffic(traffic_df)

# --- Overview Metrics ---
st.header("Overview")

total_sessions = traffic_df["sessions"].sum()
llm_sessions = traffic_df[traffic_df["is_llm"]]["sessions"].sum()
llm_pct = (llm_sessions / total_sessions * 100) if total_sessions > 0 else 0
llm_users = traffic_df[traffic_df["is_llm"]]["users"].sum()
n_llm_sources = traffic_df[traffic_df["is_llm"]]["llm_source"].nunique()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sessions", f"{total_sessions:,.0f}")
col2.metric("LLM Sessions", f"{llm_sessions:,.0f}", f"{llm_pct:.1f}% of total")
col3.metric("LLM Users", f"{llm_users:,.0f}")
col4.metric("LLM Sources Detected", n_llm_sources)

# --- Traffic Split Pie Chart + Trend Line ---
overview_col1, overview_col2 = st.columns(2)

with overview_col1:
    st.subheader("Traffic Composition")
    non_llm_sessions = total_sessions - llm_sessions
    pie_df = pd.DataFrame({
        "Source": ["LLM Traffic", "Other Traffic"],
        "Sessions": [llm_sessions, non_llm_sessions],
    })
    fig_pie = px.pie(
        pie_df,
        values="Sessions",
        names="Source",
        color="Source",
        color_discrete_map={"LLM Traffic": "#10A37F", "Other Traffic": "#E5E7EB"},
        hole=0.4,
    )
    fig_pie.update_traces(textinfo="percent+value")
    fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350)
    st.plotly_chart(fig_pie, use_container_width=True)

with overview_col2:
    st.subheader("LLM Traffic Trend")
    trend_df = get_llm_trend(traffic_df)
    if not trend_df.empty:
        fig_trend = px.area(
            trend_df,
            x=trend_df.index,
            y=trend_df.columns,
            color_discrete_map=LLM_COLOR_MAP,
            labels={"value": "Sessions", "variable": "LLM Source"},
        )
        fig_trend.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            height=350,
            xaxis_title="Date",
            yaxis_title="Sessions",
            legend_title="LLM Source",
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No LLM traffic detected in this date range.")

# --- LLM Sources Breakdown ---
st.header("LLM Sources Breakdown")

llm_agg = aggregate_llm_traffic(traffic_df, ["sessions", "users", "pageviews"])

if not llm_agg.empty:
    src_col1, src_col2 = st.columns([1, 1])

    with src_col1:
        fig_bar = px.bar(
            llm_agg.reset_index(),
            x="llm_source",
            y="sessions",
            color="llm_source",
            color_discrete_map=LLM_COLOR_MAP,
            text="sessions",
        )
        fig_bar.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig_bar.update_layout(
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
            height=400,
            xaxis_title="LLM Source",
            yaxis_title="Sessions",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with src_col2:
        display_df = llm_agg.reset_index()
        display_df.columns = ["LLM Source", "Sessions", "Users", "Pageviews"]
        display_df["Sessions"] = display_df["Sessions"].apply(lambda x: f"{x:,.0f}")
        display_df["Users"] = display_df["Users"].apply(lambda x: f"{x:,.0f}")
        display_df["Pageviews"] = display_df["Pageviews"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Engagement metrics for LLM traffic
    st.subheader("Engagement by LLM Source")
    llm_traffic = traffic_df[traffic_df["is_llm"]].copy()
    if "engagement_rate" in llm_traffic.columns and "avg_session_duration" in llm_traffic.columns:
        engagement = llm_traffic.groupby("llm_source").agg({
            "sessions": "sum",
            "engagement_rate": "mean",
            "avg_session_duration": "mean",
        }).sort_values("sessions", ascending=False).reset_index()
        engagement.columns = ["LLM Source", "Sessions", "Avg Engagement Rate", "Avg Session Duration (s)"]
        engagement["Avg Engagement Rate"] = engagement["Avg Engagement Rate"].apply(lambda x: f"{x:.1%}")
        engagement["Avg Session Duration (s)"] = engagement["Avg Session Duration (s)"].apply(lambda x: f"{x:.1f}")
        engagement["Sessions"] = engagement["Sessions"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(engagement, use_container_width=True, hide_index=True)
else:
    st.info("No LLM traffic detected. This could mean:\n"
            "- LLM bots/users haven't visited your site yet\n"
            "- UTM parameters haven't been set up for LLM referrals\n"
            "- The date range is too narrow")

# --- Landing Pages ---
st.header("Top Landing Pages from LLMs")

try:
    with st.spinner("Loading landing page data..."):
        landing_df = load_ga4_landing_pages(ga4_property_id, date_range_days, start_date, end_date)
except Exception as e:
    st.warning(f"Could not load landing page data: {e}")
    landing_df = pd.DataFrame()

if not landing_df.empty:
    landing_df = tag_llm_traffic(landing_df)
    llm_landings = landing_df[landing_df["is_llm"]].copy()

    if not llm_landings.empty:
        lp_col1, lp_col2 = st.columns([2, 1])

        with lp_col1:
            # Top pages table
            top_pages = (
                llm_landings.groupby("landing_page")
                .agg({"sessions": "sum", "users": "sum"})
                .sort_values("sessions", ascending=False)
                .head(20)
                .reset_index()
            )
            top_pages.columns = ["Landing Page", "Sessions", "Users"]
            st.dataframe(top_pages, use_container_width=True, hide_index=True)

        with lp_col2:
            # Which LLMs send traffic to which pages (top 10 pages)
            top_page_list = top_pages["Landing Page"].head(10).tolist()
            heatmap_data = (
                llm_landings[llm_landings["landing_page"].isin(top_page_list)]
                .pivot_table(
                    index="landing_page",
                    columns="llm_source",
                    values="sessions",
                    aggfunc="sum",
                    fill_value=0,
                )
            )
            if not heatmap_data.empty:
                fig_heat = px.imshow(
                    heatmap_data,
                    labels=dict(x="LLM Source", y="Landing Page", color="Sessions"),
                    color_continuous_scale="Greens",
                    aspect="auto",
                )
                fig_heat.update_layout(
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=400,
                )
                st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("No LLM-referred landing pages found.")

# --- Search Console Queries ---
st.header("Search Console Queries")

if not gsc_site_url:
    st.info("Enter your Search Console site URL in the sidebar to see query data.")
else:
    try:
        with st.spinner("Loading Search Console data..."):
            gsc_queries_df = load_gsc_queries(gsc_site_url, date_range_days, start_date, end_date)
            gsc_pages_df = load_gsc_pages(gsc_site_url, date_range_days, start_date, end_date)
    except Exception as e:
        st.warning(f"Could not load Search Console data: {e}")
        gsc_queries_df = pd.DataFrame()
        gsc_pages_df = pd.DataFrame()

    if not gsc_queries_df.empty:
        gsc_col1, gsc_col2 = st.columns(2)

        with gsc_col1:
            st.subheader("Top Search Queries")
            top_queries = gsc_queries_df.sort_values("clicks", ascending=False).head(30).copy()
            top_queries["ctr"] = top_queries["ctr"].apply(lambda x: f"{x:.1%}")
            top_queries["position"] = top_queries["position"].apply(lambda x: f"{x:.1f}")
            top_queries.columns = ["Query", "Clicks", "Impressions", "CTR", "Avg Position"]
            st.dataframe(top_queries, use_container_width=True, hide_index=True)

        with gsc_col2:
            st.subheader("Query Click Distribution")
            top_10 = gsc_queries_df.sort_values("clicks", ascending=False).head(10)
            fig_q = px.bar(
                top_10,
                x="query",
                y="clicks",
                color="impressions",
                color_continuous_scale="Blues",
            )
            fig_q.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=400,
                xaxis_title="Query",
                yaxis_title="Clicks",
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_q, use_container_width=True)

        # Cross-reference: pages that appear in both LLM landing pages and GSC
        st.subheader("Pages Receiving Both LLM Traffic & Search Traffic")
        if not landing_df.empty and "landing_page" in landing_df.columns:
            llm_pages = set(
                landing_df[landing_df["is_llm"]]["landing_page"].unique()
            )
            if not gsc_pages_df.empty:
                gsc_page_set = set(gsc_pages_df["page"].unique())
                # Normalize: GSC pages are full URLs, GA4 landing pages are paths
                overlap_pages = []
                for gsc_page in gsc_page_set:
                    for llm_page in llm_pages:
                        if llm_page in gsc_page or gsc_page.endswith(llm_page):
                            overlap_pages.append(gsc_page)
                            break

                if overlap_pages:
                    overlap_df = gsc_pages_df[gsc_pages_df["page"].isin(overlap_pages)].copy()
                    overlap_df = overlap_df.sort_values("clicks", ascending=False)
                    overlap_df["ctr"] = overlap_df["ctr"].apply(lambda x: f"{x:.1%}")
                    overlap_df["position"] = overlap_df["position"].apply(lambda x: f"{x:.1f}")
                    overlap_df.columns = ["Page", "Clicks", "Impressions", "CTR", "Avg Position"]
                    st.dataframe(overlap_df, use_container_width=True, hide_index=True)
                    st.caption(
                        "These pages receive both organic search traffic and LLM referral traffic — "
                        "they're likely being cited by LLMs in response to user queries."
                    )
                else:
                    st.info("No overlapping pages found between LLM referrals and search traffic.")

        # Conversational query patterns
        st.subheader("Conversational / LLM-Style Queries")
        st.caption(
            "Queries that match conversational patterns often used when interacting with LLMs"
        )
        conversational_patterns = [
            "what is", "how to", "how do", "why does", "can i", "should i",
            "best way to", "difference between", "vs", "compared to",
            "explain", "tutorial", "guide", "example",
        ]

        def is_conversational(query: str) -> bool:
            q = query.lower()
            return any(p in q for p in conversational_patterns)

        conv_queries = gsc_queries_df[
            gsc_queries_df["query"].apply(is_conversational)
        ].sort_values("clicks", ascending=False).head(30).copy()

        if not conv_queries.empty:
            conv_queries["ctr"] = conv_queries["ctr"].apply(lambda x: f"{x:.1%}")
            conv_queries["position"] = conv_queries["position"].apply(lambda x: f"{x:.1f}")
            conv_queries.columns = ["Query", "Clicks", "Impressions", "CTR", "Avg Position"]
            st.dataframe(conv_queries, use_container_width=True, hide_index=True)
        else:
            st.info("No conversational-style queries found.")
    else:
        st.info("No Search Console data found for this date range.")

# --- Footer ---
st.markdown("---")
st.caption(
    "Data sourced from Google Analytics 4 Data API and Google Search Console API. "
    "LLM traffic is detected via referrer domains, UTM parameters, and user-agent strings. "
    f"Dashboard last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
