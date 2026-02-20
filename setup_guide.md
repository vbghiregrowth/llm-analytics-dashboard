# Google API Setup Guide

Follow these steps to set up API access for GA4 and Google Search Console.

## 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** > **New Project**
3. Name it (e.g., "LLM Analytics Dashboard") and click **Create**
4. Make sure the new project is selected

## 2. Enable Required APIs

1. Go to **APIs & Services** > **Library**
2. Search for and enable:
   - **Google Analytics Data API** (for GA4)
   - **Google Search Console API** (listed as "Google Search Console API")

## 3. Create a Service Account

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Name it (e.g., "llm-analytics-reader"), click **Create and Continue**
4. Skip the optional role assignment, click **Done**
5. Click on the newly created service account
6. Go to **Keys** tab > **Add Key** > **Create new key** > **JSON**
7. Save the downloaded JSON file as `service-account-key.json` in the project root

## 4. Grant GA4 Access to the Service Account

1. Go to [Google Analytics](https://analytics.google.com/)
2. Navigate to **Admin** > **Property** > **Property Access Management**
3. Click **+** > **Add users**
4. Enter the service account email (from the JSON key, looks like `name@project.iam.gserviceaccount.com`)
5. Set role to **Viewer**
6. Click **Add**

## 5. Find Your GA4 Property ID

1. In Google Analytics, go to **Admin** > **Property** > **Property Details**
2. Copy the **Property ID** (numeric, e.g., `123456789`)

## 6. Grant Search Console Access

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Select your property
3. Go to **Settings** > **Users and permissions** > **Add user**
4. Enter the service account email
5. Set permission to **Full** (needed for API access)

## 7. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Fill in:
   - `GA4_PROPERTY_ID` — your numeric property ID
   - `GSC_SITE_URL` — your site URL (e.g., `https://example.com` or `sc-domain:example.com`)
   - `GOOGLE_APPLICATION_CREDENTIALS` — path to your JSON key file

## 8. Optional: Custom User-Agent Dimension in GA4

To track LLM bot user-agents, you need a custom dimension:

1. In GA4, go to **Admin** > **Property** > **Custom definitions**
2. Click **Create custom dimension**
3. Set:
   - Dimension name: `User Agent`
   - Scope: **Event**
   - Event parameter: `user_agent`
4. You'll also need to send the user-agent as an event parameter via GTM or gtag.js:
   ```javascript
   gtag('event', 'page_view', {
     'user_agent': navigator.userAgent
   });
   ```

Note: The user-agent dimension is optional. The dashboard will still work using referrer and UTM detection without it.

## 9. Run the Dashboard

```bash
pip install -r requirements.txt
streamlit run app.py
```
