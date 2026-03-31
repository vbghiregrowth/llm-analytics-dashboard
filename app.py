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
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom Theme CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

/* === ROOT VARS === */
:root {
    --bg-deep: #06080D;
    --bg-card: #0C1017;
    --bg-card-hover: #111822;
    --bg-surface: #141B27;
    --border-dim: #1A2332;
    --border-glow: #10B981;
    --text-primary: #E8ECF1;
    --text-secondary: #7A869A;
    --text-muted: #4A5568;
    --accent-green: #10B981;
    --accent-emerald: #34D399;
    --accent-red: #F87171;
    --accent-amber: #FBBF24;
    --accent-blue: #60A5FA;
    --accent-purple: #A78BFA;
    --gradient-green: linear-gradient(135deg, #10B981 0%, #059669 100%);
    --gradient-red: linear-gradient(135deg, #F87171 0%, #DC2626 100%);
    --gradient-amber: linear-gradient(135deg, #FBBF24 0%, #D97706 100%);
}

/* === GLOBAL === */
.stApp {
    background: var(--bg-deep) !important;
    font-family: 'Outfit', sans-serif !important;
}

.stApp > header { background: transparent !important; }

/* Main content area */
.main .block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
}

/* === SIDEBAR === */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080C14 0%, #0A0F18 50%, #060A12 100%) !important;
    border-right: 1px solid var(--border-dim) !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] label {
    font-family: 'Outfit', sans-serif !important;
    color: var(--text-secondary) !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: 'Outfit', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Sidebar title bar */
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    background: transparent !important;
}

/* === TYPOGRAPHY === */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: 'Outfit', sans-serif !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.03em !important;
}

h1, .stMarkdown h1 {
    font-weight: 800 !important;
    font-size: 2.2rem !important;
}

h2, .stMarkdown h2 {
    font-weight: 700 !important;
    font-size: 1.4rem !important;
    color: var(--text-secondary) !important;
}

p, span, li, .stMarkdown p {
    font-family: 'Outfit', sans-serif !important;
    color: var(--text-secondary) !important;
}

/* === METRIC CARDS === */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 16px !important;
    padding: 20px 24px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative !important;
    overflow: hidden !important;
}

[data-testid="stMetric"]::before {
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    height: 3px !important;
    background: var(--gradient-green) !important;
    opacity: 0.6 !important;
}

[data-testid="stMetric"]:hover {
    border-color: var(--accent-green) !important;
    box-shadow: 0 0 30px rgba(16, 185, 129, 0.08) !important;
    transform: translateY(-2px) !important;
}

[data-testid="stMetricLabel"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    color: var(--text-muted) !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 800 !important;
    font-size: 2rem !important;
    color: var(--text-primary) !important;
    line-height: 1.1 !important;
}

[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
}

/* === DATAFRAMES === */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--border-dim) !important;
}

[data-testid="stDataFrame"] th {
    font-family: 'JetBrains Mono', monospace !important;
    text-transform: uppercase !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.08em !important;
}

/* === PLOTLY CHARTS === */
.stPlotlyChart {
    border-radius: 16px !important;
    overflow: hidden !important;
}

/* === DIVIDERS === */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent 0%, var(--border-dim) 20%, var(--border-dim) 80%, transparent 100%) !important;
    margin: 2rem 0 !important;
}

/* === BUTTONS & INPUTS === */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stDateInput > div > div > input {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Outfit', sans-serif !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div:focus-within {
    border-color: var(--accent-green) !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.12) !important;
}

/* === INFO/WARNING BOXES === */
.stAlert {
    border-radius: 12px !important;
    font-family: 'Outfit', sans-serif !important;
    border: 1px solid var(--border-dim) !important;
}

/* === SPINNER === */
.stSpinner > div {
    border-top-color: var(--accent-green) !important;
}

/* === CHECKBOX === */
.stCheckbox label span {
    color: var(--text-secondary) !important;
    font-family: 'Outfit', sans-serif !important;
}

/* === SCROLLBAR === */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--border-dim); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* === TABS === */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: var(--bg-card) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid var(--border-dim) !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    padding: 8px 20px !important;
}

.stTabs [aria-selected="true"] {
    background: var(--bg-surface) !important;
    color: var(--accent-green) !important;
}

/* === CAPTIONS === */
.stCaption, [data-testid="stCaptionContainer"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.02em !important;
}

/* === EXPANDER === */
.streamlit-expanderHeader {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    background: var(--bg-card) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)


# --- Plotly Theme ---
_DEFAULT_XAXIS = dict(
    gridcolor="#1A2332",
    gridwidth=1,
    zerolinecolor="#1A2332",
    tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#4A5568"),
    title_font=dict(family="Outfit, sans-serif", size=12, color="#7A869A"),
)

_DEFAULT_YAXIS = dict(
    gridcolor="#1A2332",
    gridwidth=1,
    zerolinecolor="#1A2332",
    tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#4A5568"),
    title_font=dict(family="Outfit, sans-serif", size=12, color="#7A869A"),
)

_DEFAULT_LEGEND = dict(
    font=dict(family="Outfit, sans-serif", size=11, color="#7A869A"),
    bgcolor="rgba(0,0,0,0)",
)

# Base layout — does NOT include xaxis/yaxis/legend so charts can override them
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Outfit, sans-serif", color="#7A869A", size=12),
    hoverlabel=dict(
        bgcolor="#141B27",
        bordercolor="#1A2332",
        font=dict(family="JetBrains Mono, monospace", size=11, color="#E8ECF1"),
    ),
    margin=dict(t=30, b=30, l=30, r=30),
)

# Full layout with defaults — for charts that don't customize axes/legend
PLOTLY_LAYOUT_FULL = dict(
    **PLOTLY_LAYOUT,
    xaxis=_DEFAULT_XAXIS,
    yaxis=_DEFAULT_YAXIS,
    legend=_DEFAULT_LEGEND,
)

# Refined LLM colors for charts
CHART_COLORS = {
    "ChatGPT": "#10B981",
    "Claude": "#F59E0B",
    "Perplexity": "#60A5FA",
    "Gemini": "#818CF8",
    "Copilot": "#A78BFA",
    "You.com": "#F472B6",
    "Cohere": "#FBBF24",
    "Meta AI": "#38BDF8",
    "Grok": "#E5E7EB",
    "Unknown LLM": "#4A5568",
    "Other": "#374151",
}


def hex_to_rgba(hex_color: str, alpha: float = 0.08) -> str:
    """Convert a hex color to an rgba string for Plotly compatibility."""
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, {alpha})"


def apply_plotly_theme(fig, height=350):
    """Apply consistent dark theme to any plotly figure."""
    fig.update_layout(**PLOTLY_LAYOUT_FULL, height=height)
    return fig


# --- Sidebar ---
st.sidebar.markdown("""
<div style="padding: 8px 0 16px 0;">
    <div style="font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 1.4rem; color: #E8ECF1; letter-spacing: -0.03em; line-height: 1.2;">
        LLM Traffic<br>
        <span style="background: linear-gradient(135deg, #10B981, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Analytics</span>
    </div>
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #4A5568; margin-top: 6px; letter-spacing: 0.05em;">GA4 + SEARCH CONSOLE</div>
</div>
""", unsafe_allow_html=True)

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

# Source badges in sidebar
source_chips = " ".join(
    f'<span style="display:inline-block; background:#141B27; border:1px solid #1A2332; '
    f'border-radius:6px; padding:2px 8px; margin:2px; font-family:JetBrains Mono,monospace; '
    f'font-size:0.6rem; color:{src["color"]};">{name}</span>'
    for name, src in LLM_SOURCES.items()
)
st.sidebar.markdown(f'<div style="margin-top:4px;">{source_chips}</div>', unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="margin-top:16px; font-family:'JetBrains Mono',monospace; font-size:0.6rem; color:#4A5568;">
    GA4 Data API + Search Console API
</div>
""", unsafe_allow_html=True)


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


# --- Section Header Component ---
def section_header(title, subtitle=None, icon=None):
    icon_html = f'<span style="margin-right: 10px; font-size: 1.1rem;">{icon}</span>' if icon else ''
    sub_html = f'<div style="font-family:JetBrains Mono,monospace; font-size:0.7rem; color:#4A5568; margin-top:4px; letter-spacing:0.05em; text-transform:uppercase;">{subtitle}</div>' if subtitle else ''
    st.markdown(f"""
    <div style="margin: 2rem 0 1.2rem 0;">
        <div style="font-family:'Outfit',sans-serif; font-weight:800; font-size:1.5rem; color:#E8ECF1; letter-spacing:-0.03em;">
            {icon_html}{title}
        </div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


# --- Logo + Main Dashboard ---
import base64
_logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
with open(_logo_path, "rb") as _f:
    _logo_b64 = base64.b64encode(_f.read()).decode()

st.markdown(f"""
<div style="margin-bottom: 0.5rem;">
    <img src="data:image/png;base64,{_logo_b64}" alt="HireGrowth" style="height:36px; filter:invert(1); margin-bottom:16px;" />
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#10B981; letter-spacing:0.15em; text-transform:uppercase; font-weight:600; margin-bottom:8px;">DASHBOARD</div>
    <div style="font-family:'Outfit',sans-serif; font-weight:900; font-size:2.8rem; color:#E8ECF1; letter-spacing:-0.04em; line-height:1.05;">
        LLM Traffic<br>Analytics
    </div>
</div>
""", unsafe_allow_html=True)
st.caption(f"Showing data for the {date_range_label.lower()}")

if not ga4_property_id:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0C1017, #141B27); border: 1px solid #1A2332; border-radius: 16px; padding: 48px; text-align: center; margin: 3rem 0;">
        <div style="font-size: 3rem; margin-bottom: 16px;">&#x1f50d;</div>
        <div style="font-family:'Outfit',sans-serif; font-weight:700; font-size:1.3rem; color:#E8ECF1; margin-bottom:8px;">Connect Your Analytics</div>
        <div style="font-family:'Outfit',sans-serif; font-size:0.95rem; color:#7A869A; max-width:400px; margin:0 auto;">
            Enter your GA4 Property ID in the sidebar to start tracking LLM-referred traffic to your site.
        </div>
    </div>
    """, unsafe_allow_html=True)
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
section_header("Overview", "KEY METRICS THIS PERIOD")

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

# --- LLM Traffic Growth Indicator ---
trend_df = get_llm_trend(traffic_df)
if not trend_df.empty and len(trend_df) >= 4:
    daily_totals = trend_df.sum(axis=1).sort_index()
    midpoint = len(daily_totals) // 2
    first_half = daily_totals.iloc[:midpoint].sum()
    second_half = daily_totals.iloc[midpoint:].sum()

    if first_half > 0:
        growth_pct = ((second_half - first_half) / first_half) * 100
    elif second_half > 0:
        growth_pct = 100.0
    else:
        growth_pct = 0.0

    if growth_pct > 5:
        status_label = "Growing"
        status_color = "#10B981"
        glow_color = "rgba(16, 185, 129, 0.15)"
        bar_gradient = "linear-gradient(135deg, #10B981, #34D399)"
        arrow_icon = "&#x2197;"  # ↗
    elif growth_pct < -5:
        status_label = "Declining"
        status_color = "#F87171"
        glow_color = "rgba(248, 113, 113, 0.15)"
        bar_gradient = "linear-gradient(135deg, #F87171, #DC2626)"
        arrow_icon = "&#x2198;"  # ↘
    else:
        status_label = "Stable"
        status_color = "#FBBF24"
        glow_color = "rgba(251, 191, 36, 0.15)"
        bar_gradient = "linear-gradient(135deg, #FBBF24, #D97706)"
        arrow_icon = "&#x2192;"  # →

    # Per-source growth
    source_growth = []
    for c in trend_df.columns:
        src_daily = trend_df[c].sort_index()
        src_first = src_daily.iloc[:midpoint].sum()
        src_second = src_daily.iloc[midpoint:].sum()
        if src_first > 0:
            sg = ((src_second - src_first) / src_first) * 100
        elif src_second > 0:
            sg = 100.0
        else:
            sg = 0.0
        source_growth.append({"source": c, "first_half": src_first, "second_half": src_second, "growth": sg})

    st.markdown("")
    section_header("Is LLM Traffic Growing?", "PERIOD-OVER-PERIOD COMPARISON")

    growth_col1, growth_col2 = st.columns([1, 2])

    with growth_col1:
        sign = "+" if growth_pct >= 0 else ""
        st.metric("LLM Traffic Growth", f"{sign}{growth_pct:.1f}%", status_label)
        st.metric("First Half Sessions", f"{first_half:,.0f}")
        st.metric("Second Half Sessions", f"{second_half:,.0f}")

    with growth_col2:
        sg_df = pd.DataFrame(source_growth).sort_values("second_half", ascending=False)
        fig_growth = go.Figure()
        fig_growth.add_trace(go.Bar(
            name="First Half",
            x=sg_df["source"],
            y=sg_df["first_half"],
            marker=dict(color="#1A2332", line=dict(color="#2D3748", width=1)),
            text=sg_df["first_half"].apply(lambda x: f"{x:,.0f}"),
            textposition="outside",
            textfont=dict(family="JetBrains Mono, monospace", size=10, color="#4A5568"),
        ))
        fig_growth.add_trace(go.Bar(
            name="Second Half",
            x=sg_df["source"],
            y=sg_df["second_half"],
            marker=dict(
                color=[CHART_COLORS.get(s, "#10B981") for s in sg_df["source"]],
                line=dict(color="rgba(255,255,255,0.1)", width=1),
            ),
            text=sg_df["second_half"].apply(lambda x: f"{x:,.0f}"),
            textposition="outside",
            textfont=dict(family="JetBrains Mono, monospace", size=10, color="#7A869A"),
        ))
        fig_growth.update_layout(
            **PLOTLY_LAYOUT,
            barmode="group",
            height=260,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1,
                font=dict(family="Outfit, sans-serif", size=11, color="#7A869A"),
                bgcolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_growth, use_container_width=True)

        # Per-source growth chips
        chips_html = '<div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:4px;">'
        for _, row in sg_df.iterrows():
            g = row["growth"]
            src_color = CHART_COLORS.get(row["source"], "#10B981")
            if g > 5:
                arrow = "&#x2197;"
            elif g < -5:
                arrow = "&#x2198;"
            else:
                arrow = "&#x2192;"
            s = "+" if g >= 0 else ""
            chips_html += (
                f'<span style="display:inline-flex; align-items:center; gap:4px; '
                f'background:{src_color}12; border:1px solid {src_color}30; '
                f'border-radius:8px; padding:5px 12px; '
                f'font-family:JetBrains Mono,monospace; font-size:0.7rem; color:{src_color}; font-weight:600;">'
                f'{row["source"]} {arrow} {s}{g:.0f}%</span>'
            )
        chips_html += '</div>'
        st.markdown(chips_html, unsafe_allow_html=True)

    # --- Why is it growing/declining? Insights ---
    st.markdown("")
    section_header("Why?", "AUTO-GENERATED INSIGHTS")

    insights = []
    sg_df_sorted = sg_df.sort_values("growth", ascending=False)

    biggest_gainer = sg_df_sorted.iloc[0]
    biggest_loser = sg_df_sorted.iloc[-1]
    session_delta = second_half - first_half

    if biggest_gainer["growth"] > 5:
        gain_delta = biggest_gainer["second_half"] - biggest_gainer["first_half"]
        if session_delta != 0:
            contribution = abs(gain_delta / session_delta) * 100
        else:
            contribution = 0
        insights.append({
            "icon": "&#x1f680;",
            "title": f"{biggest_gainer['source']} is the biggest growth driver",
            "detail": f"Up {biggest_gainer['growth']:+.0f}% ({biggest_gainer['first_half']:,.0f} &rarr; {biggest_gainer['second_half']:,.0f} sessions), "
                      f"accounting for ~{contribution:.0f}% of the overall change.",
            "type": "positive",
        })

    if biggest_loser["growth"] < -5:
        insights.append({
            "icon": "&#x26A0;",
            "title": f"{biggest_loser['source']} is pulling traffic down",
            "detail": f"Down {biggest_loser['growth']:+.0f}% ({biggest_loser['first_half']:,.0f} &rarr; {biggest_loser['second_half']:,.0f} sessions).",
            "type": "negative",
        })

    new_sources = sg_df_sorted[(sg_df_sorted["first_half"] == 0) & (sg_df_sorted["second_half"] > 0)]
    lost_sources = sg_df_sorted[(sg_df_sorted["second_half"] == 0) & (sg_df_sorted["first_half"] > 0)]

    if not new_sources.empty:
        names = ", ".join(new_sources["source"].tolist())
        total_new = new_sources["second_half"].sum()
        insights.append({
            "icon": "&#x2728;",
            "title": f"New LLM source{'s' if len(new_sources) > 1 else ''} detected: {names}",
            "detail": f"{'These sources were' if len(new_sources) > 1 else 'This source was'} not sending traffic before but contributed {total_new:,.0f} sessions in the recent half.",
            "type": "positive",
        })

    if not lost_sources.empty:
        names = ", ".join(lost_sources["source"].tolist())
        total_lost = lost_sources["first_half"].sum()
        insights.append({
            "icon": "&#x1F534;",
            "title": f"Lost traffic from: {names}",
            "detail": f"{'These sources' if len(lost_sources) > 1 else 'This source'} sent {total_lost:,.0f} sessions before but dropped to zero.",
            "type": "negative",
        })

    # Engagement shift
    llm_only = traffic_df[traffic_df["is_llm"]].copy()
    if "engagement_rate" in llm_only.columns and "date" in llm_only.columns and not llm_only.empty:
        llm_only["date"] = pd.to_datetime(llm_only["date"])
        sorted_dates = llm_only["date"].sort_values()
        if len(sorted_dates) >= 4:
            mid_date = sorted_dates.iloc[len(sorted_dates) // 2]
            eng_first = llm_only[llm_only["date"] < mid_date]["engagement_rate"].mean()
            eng_second = llm_only[llm_only["date"] >= mid_date]["engagement_rate"].mean()
            dur_first = llm_only[llm_only["date"] < mid_date]["avg_session_duration"].mean() if "avg_session_duration" in llm_only.columns else None
            dur_second = llm_only[llm_only["date"] >= mid_date]["avg_session_duration"].mean() if "avg_session_duration" in llm_only.columns else None

            if eng_first > 0:
                eng_change = ((eng_second - eng_first) / eng_first) * 100
                if abs(eng_change) > 10:
                    direction = "improved" if eng_change > 0 else "declined"
                    insights.append({
                        "icon": "&#x1F3AF;" if eng_change > 0 else "&#x1F4C9;",
                        "title": f"Engagement rate has {direction}",
                        "detail": f"Average engagement rate went from {eng_first:.1%} to {eng_second:.1%} ({eng_change:+.0f}%). "
                                  + ("LLM visitors are finding your content more relevant." if eng_change > 0 else "LLM visitors may be bouncing more &mdash; check if landing page content matches what LLMs are citing."),
                        "type": "positive" if eng_change > 0 else "negative",
                    })

            if dur_first and dur_first > 0 and dur_second:
                dur_change = ((dur_second - dur_first) / dur_first) * 100
                if abs(dur_change) > 15:
                    direction = "longer" if dur_change > 0 else "shorter"
                    insights.append({
                        "icon": "&#x23F1;",
                        "title": f"Session duration is getting {direction}",
                        "detail": f"Average session duration changed from {dur_first:.0f}s to {dur_second:.0f}s ({dur_change:+.0f}%).",
                        "type": "neutral",
                    })

    # Concentration risk
    if len(sg_df) > 1:
        top_source_share = sg_df_sorted.iloc[0]["second_half"] / sg_df["second_half"].sum() * 100 if sg_df["second_half"].sum() > 0 else 0
        if top_source_share > 75:
            insights.append({
                "icon": "&#x26A1;",
                "title": f"{sg_df_sorted.iloc[0]['source']} accounts for {top_source_share:.0f}% of all LLM traffic",
                "detail": "Heavy reliance on a single LLM source. If this platform changes how it cites or links, your traffic could drop significantly.",
                "type": "warning",
            })

    # Render insights
    if insights:
        for ins in insights:
            if ins["type"] == "positive":
                accent = "#10B981"
            elif ins["type"] == "negative":
                accent = "#F87171"
            elif ins["type"] == "warning":
                accent = "#FBBF24"
            else:
                accent = "#7A869A"

            st.markdown(f"""
            <div style="
                background: var(--bg-card);
                border: 1px solid var(--border-dim);
                border-left: 3px solid {accent};
                border-radius: 0 12px 12px 0;
                padding: 16px 20px;
                margin-bottom: 10px;
                transition: all 0.2s ease;
            ">
                <div style="display:flex; align-items:flex-start; gap:12px;">
                    <span style="font-size:1.2rem; flex-shrink:0; margin-top:1px;">{ins['icon']}</span>
                    <div>
                        <div style="font-family:'Outfit',sans-serif; font-weight:700; font-size:0.95rem; color:#E8ECF1;">{ins['title']}</div>
                        <div style="font-family:'Outfit',sans-serif; font-size:0.82rem; color:#7A869A; margin-top:4px; line-height:1.5;">{ins['detail']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Not enough variation in the data to generate specific insights. Try a wider date range.")

    st.markdown("")

# --- Traffic Split Pie Chart + Trend Line ---
section_header("Traffic Breakdown", "COMPOSITION & DAILY TREND")

overview_col1, overview_col2 = st.columns(2)

with overview_col1:
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
        color_discrete_map={"LLM Traffic": "#10B981", "Other Traffic": "#1A2332"},
        hole=0.55,
    )
    fig_pie.update_traces(
        textinfo="percent+value",
        textfont=dict(family="JetBrains Mono, monospace", size=11, color="#E8ECF1"),
        marker=dict(line=dict(color="#0C1017", width=2)),
    )
    fig_pie.update_layout(
        **PLOTLY_LAYOUT,
        height=380,
        showlegend=True,
        annotations=[dict(
            text=f"<b>{llm_pct:.1f}%</b><br><span style='font-size:10px;color:#4A5568'>LLM</span>",
            x=0.5, y=0.5, font=dict(size=22, color="#10B981", family="Outfit, sans-serif"),
            showarrow=False,
        )],
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with overview_col2:
    if not trend_df.empty:
        fig_trend = go.Figure()
        for col_name in trend_df.columns:
            fig_trend.add_trace(go.Scatter(
                x=trend_df.index,
                y=trend_df[col_name],
                name=col_name,
                mode="lines",
                line=dict(
                    color=CHART_COLORS.get(col_name, "#10B981"),
                    width=2.5,
                    shape="spline",
                ),
                fill="tonexty" if col_name != trend_df.columns[0] else "tozeroy",
                fillcolor=hex_to_rgba(CHART_COLORS.get(col_name, "#10B981"), 0.08),
            ))
        fig_trend.update_layout(
            **PLOTLY_LAYOUT,
            height=380,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(family="Outfit, sans-serif", size=11, color="#7A869A"),
                bgcolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No LLM traffic detected in this date range.")

# --- LLM Sources Breakdown ---
section_header("LLM Sources", "BREAKDOWN BY PLATFORM")

llm_agg = aggregate_llm_traffic(traffic_df, ["sessions", "users", "pageviews"])

if not llm_agg.empty:
    src_col1, src_col2 = st.columns([1, 1])

    with src_col1:
        agg_reset = llm_agg.reset_index()
        fig_bar = go.Figure(go.Bar(
            x=agg_reset["sessions"],
            y=agg_reset["llm_source"],
            orientation="h",
            marker=dict(
                color=[CHART_COLORS.get(s, "#10B981") for s in agg_reset["llm_source"]],
                line=dict(color="rgba(255,255,255,0.05)", width=1),
            ),
            text=agg_reset["sessions"].apply(lambda x: f"{x:,.0f}"),
            textposition="outside",
            textfont=dict(family="JetBrains Mono, monospace", size=11, color="#7A869A"),
        ))
        fig_bar.update_layout(
            **PLOTLY_LAYOUT,
            height=max(250, len(agg_reset) * 50),
            showlegend=False,
            yaxis=dict(
                autorange="reversed",
                gridcolor="rgba(0,0,0,0)",
                tickfont=dict(family="Outfit, sans-serif", size=12, color="#E8ECF1"),
            ),
            xaxis=dict(gridcolor="#1A2332", tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#4A5568")),
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
    st.markdown("")
    st.markdown('<div style="font-family:Outfit,sans-serif; font-weight:700; font-size:1.1rem; color:#E8ECF1; margin-bottom:8px;">Engagement by Source</div>', unsafe_allow_html=True)
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
    st.markdown("""
    <div style="background:var(--bg-card); border:1px solid var(--border-dim); border-radius:16px; padding:40px; text-align:center;">
        <div style="font-size:2rem; margin-bottom:12px;">&#x1F50D;</div>
        <div style="font-family:'Outfit',sans-serif; font-weight:600; color:#E8ECF1; margin-bottom:6px;">No LLM Traffic Detected</div>
        <div style="font-family:'Outfit',sans-serif; font-size:0.85rem; color:#7A869A;">
            LLM bots/users may not have visited yet, UTM parameters aren't set up, or the date range is too narrow.
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Landing Pages ---
section_header("Top Landing Pages", "PAGES RECEIVING LLM TRAFFIC")

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
                    color_continuous_scale=[[0, "#0C1017"], [0.5, "#065F46"], [1, "#10B981"]],
                    aspect="auto",
                )
                fig_heat.update_layout(**PLOTLY_LAYOUT, height=400)
                fig_heat.update_traces(
                    textfont=dict(family="JetBrains Mono, monospace", size=10),
                )
                st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("No LLM-referred landing pages found.")

# --- Search Console Queries ---
section_header("Search Console", "QUERY PERFORMANCE DATA")

if not gsc_site_url:
    st.markdown("""
    <div style="background:var(--bg-card); border:1px dashed var(--border-dim); border-radius:16px; padding:32px; text-align:center;">
        <div style="font-family:'Outfit',sans-serif; font-size:0.9rem; color:#7A869A;">
            Enter your Search Console site URL in the sidebar to see query data.
        </div>
    </div>
    """, unsafe_allow_html=True)
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
            st.markdown('<div style="font-family:Outfit,sans-serif; font-weight:700; font-size:1.1rem; color:#E8ECF1; margin-bottom:8px;">Top Search Queries</div>', unsafe_allow_html=True)
            top_queries = gsc_queries_df.sort_values("clicks", ascending=False).head(30).copy()
            top_queries["ctr"] = top_queries["ctr"].apply(lambda x: f"{x:.1%}")
            top_queries["position"] = top_queries["position"].apply(lambda x: f"{x:.1f}")
            top_queries.columns = ["Query", "Clicks", "Impressions", "CTR", "Avg Position"]
            st.dataframe(top_queries, use_container_width=True, hide_index=True)

        with gsc_col2:
            st.markdown('<div style="font-family:Outfit,sans-serif; font-weight:700; font-size:1.1rem; color:#E8ECF1; margin-bottom:8px;">Click Distribution</div>', unsafe_allow_html=True)
            top_10 = gsc_queries_df.sort_values("clicks", ascending=False).head(10)
            fig_q = go.Figure(go.Bar(
                x=top_10["clicks"],
                y=top_10["query"],
                orientation="h",
                marker=dict(
                    color="#10B981",
                    line=dict(color="rgba(255,255,255,0.05)", width=1),
                ),
                text=top_10["clicks"].apply(lambda x: f"{x:,.0f}"),
                textposition="outside",
                textfont=dict(family="JetBrains Mono, monospace", size=10, color="#7A869A"),
            ))
            fig_q.update_layout(
                **PLOTLY_LAYOUT,
                height=400,
                yaxis=dict(
                    autorange="reversed",
                    gridcolor="rgba(0,0,0,0)",
                    tickfont=dict(family="Outfit, sans-serif", size=11, color="#E8ECF1"),
                ),
            )
            st.plotly_chart(fig_q, use_container_width=True)

        # Cross-reference
        st.markdown("")
        st.markdown('<div style="font-family:Outfit,sans-serif; font-weight:700; font-size:1.1rem; color:#E8ECF1; margin-bottom:8px;">Pages with Both LLM &amp; Search Traffic</div>', unsafe_allow_html=True)
        if not landing_df.empty and "landing_page" in landing_df.columns:
            llm_pages = set(
                landing_df[landing_df["is_llm"]]["landing_page"].unique()
            )
            if not gsc_pages_df.empty:
                gsc_page_set = set(gsc_pages_df["page"].unique())
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
                        "These pages receive both organic search traffic and LLM referral traffic \u2014 "
                        "they're likely being cited by LLMs in response to user queries."
                    )
                else:
                    st.info("No overlapping pages found between LLM referrals and search traffic.")

        # Conversational query patterns
        st.markdown("")
        st.markdown('<div style="font-family:Outfit,sans-serif; font-weight:700; font-size:1.1rem; color:#E8ECF1; margin-bottom:4px;">Conversational Queries</div>', unsafe_allow_html=True)
        st.caption(
            "Queries matching conversational patterns often used when interacting with LLMs"
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
st.markdown("")
st.markdown(f"""
<div style="
    margin-top: 3rem;
    padding: 20px 0;
    border-top: 1px solid #1A2332;
    display: flex;
    justify-content: space-between;
    align-items: center;
">
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#4A5568; letter-spacing:0.03em;">
        GA4 Data API &middot; Search Console API &middot; LLM detection via referrer, UTM, user-agent
    </div>
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#4A5568;">
        {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
</div>
""", unsafe_allow_html=True)
