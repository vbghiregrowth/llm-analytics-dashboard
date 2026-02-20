"""
Google API authentication helpers for GA4 and Search Console.
"""

import os
from google.auth import default
from google.oauth2 import service_account

GA4_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
GSC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
ALL_SCOPES = GA4_SCOPES + GSC_SCOPES


def get_credentials(scopes=None):
    """
    Load Google credentials from a service account JSON key file.
    Falls back to Application Default Credentials if no key file is found.

    Returns (credentials, error_message) tuple.
    """
    if scopes is None:
        scopes = ALL_SCOPES

    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    if creds_path and os.path.exists(creds_path):
        try:
            credentials = service_account.Credentials.from_service_account_file(
                creds_path, scopes=scopes
            )
            return credentials, None
        except Exception as e:
            return None, f"Failed to load service account key: {e}"

    # Fall back to Application Default Credentials
    try:
        credentials, project = default(scopes=scopes)
        return credentials, None
    except Exception as e:
        return None, (
            "No credentials found. Please either:\n"
            "1. Set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON key path\n"
            "2. Run `gcloud auth application-default login`\n\n"
            f"Error: {e}\n\n"
            "See setup_guide.md for detailed instructions."
        )


def get_ga4_credentials():
    """Get credentials scoped for GA4 Data API."""
    return get_credentials(scopes=GA4_SCOPES)


def get_gsc_credentials():
    """Get credentials scoped for Google Search Console API."""
    return get_credentials(scopes=GSC_SCOPES)
