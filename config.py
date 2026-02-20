"""
LLM source definitions and constants for traffic detection.
"""

# Known LLM sources with their detection signals
LLM_SOURCES = {
    "ChatGPT": {
        "referrer_domains": ["chat.openai.com", "chatgpt.com"],
        "user_agents": ["ChatGPT-User", "GPTBot"],
        "utm_sources": ["chatgpt", "openai"],
        "color": "#10A37F",
    },
    "Claude": {
        "referrer_domains": ["claude.ai"],
        "user_agents": ["ClaudeBot", "Claude-Web"],
        "utm_sources": ["claude", "anthropic"],
        "color": "#D97706",
    },
    "Perplexity": {
        "referrer_domains": ["perplexity.ai", "www.perplexity.ai"],
        "user_agents": ["PerplexityBot"],
        "utm_sources": ["perplexity"],
        "color": "#1E40AF",
    },
    "Gemini": {
        "referrer_domains": ["gemini.google.com"],
        "user_agents": ["Google-Extended"],
        "utm_sources": ["gemini"],
        "color": "#4285F4",
    },
    "Copilot": {
        "referrer_domains": ["copilot.microsoft.com", "www.bing.com/chat"],
        "user_agents": ["BingBot"],
        "utm_sources": ["copilot", "bing_chat"],
        "color": "#9333EA",
    },
    "You.com": {
        "referrer_domains": ["you.com", "www.you.com"],
        "user_agents": ["YouBot"],
        "utm_sources": ["you", "youcom"],
        "color": "#EC4899",
    },
    "Cohere": {
        "referrer_domains": [],
        "user_agents": ["cohere-ai"],
        "utm_sources": ["cohere"],
        "color": "#F59E0B",
    },
    "Meta AI": {
        "referrer_domains": ["meta.ai", "www.meta.ai"],
        "user_agents": ["Meta-ExternalAgent"],
        "utm_sources": ["meta_ai"],
        "color": "#0668E1",
    },
    "Grok": {
        "referrer_domains": ["grok.x.ai", "x.com"],
        "user_agents": [],
        "utm_sources": ["grok"],
        "color": "#000000",
    },
}

# Flatten lookups for fast matching
ALL_REFERRER_DOMAINS = {}
for name, src in LLM_SOURCES.items():
    for domain in src["referrer_domains"]:
        ALL_REFERRER_DOMAINS[domain.lower()] = name

ALL_USER_AGENTS = {}
for name, src in LLM_SOURCES.items():
    for ua in src["user_agents"]:
        ALL_USER_AGENTS[ua.lower()] = name

ALL_UTM_SOURCES = {}
for name, src in LLM_SOURCES.items():
    for utm in src["utm_sources"]:
        ALL_UTM_SOURCES[utm.lower()] = name

# Color map for charts
LLM_COLOR_MAP = {name: src["color"] for name, src in LLM_SOURCES.items()}
LLM_COLOR_MAP["Unknown LLM"] = "#6B7280"
LLM_COLOR_MAP["Other"] = "#9CA3AF"

# GA4 dimensions and metrics used in queries
GA4_DIMENSIONS = {
    "source": "sessionSource",
    "medium": "sessionMedium",
    "landing_page": "landingPage",
    "date": "date",
    "page_path": "pagePath",
    "campaign": "sessionCampaign",
}

GA4_METRICS = {
    "sessions": "sessions",
    "users": "totalUsers",
    "new_users": "newUsers",
    "pageviews": "screenPageViews",
    "bounce_rate": "bounceRate",
    "avg_session_duration": "averageSessionDuration",
    "engagement_rate": "engagementRate",
}

# Date range presets
DATE_RANGES = {
    "Last 7 days": 7,
    "Last 14 days": 14,
    "Last 30 days": 30,
    "Last 90 days": 90,
}
