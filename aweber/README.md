# AWeber Broadcast Exporter

A simple Python tool to export all your AWeber broadcasts (sent, scheduled, and drafts) into a clean, single Markdown file useful for analyzing your own newsletter history. The resulting data file can be easily imported into an LLM (pick your poison ;) ) for review or RAG.

It handles OAuth 2.0 authorization (with auto-refresh), pagination, and extracts preview text (preheaders) hidden in HTML headers.

## Key Features

* **Incremental Sync:** By default, it only fetches new messages since the last run to save API limits.
* **JSON Database:** Stores everything in a structured `aweber_db.json` before rendering to Markdown.
* **Preview Extraction:** Scans HTML for `x-preheader` meta tags or specific CSS classes to find what your subscribers see in their inboxes.
* **Auto-Refresh:** Once authorized, it keeps the session alive using refresh tokens—no need to log in every time.

## Prerequisites

1.  **AWeber Labs Account:** Create a free developer account at [labs.aweber.com](https://labs.aweber.com/).
2.  **App Credentials:** Create an app with `https://localhost` as the **OAuth Redirect URI**. Grab your `Client ID` and `Client Secret`.

## Setup

1.  **Clone & Venv:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configuration:**
    Run `cp .env.dist .env` and update your credentials.

## Usage

### Basic Sync
```bash
python aweber_dumper.py
```

Fetches new sent messages since the last sync and refreshes all drafts and scheduled broadcasts.

## Advanced Options
Full Refresh: `--full` Wipes the local cache and re-downloads everything from scratch. Useful if you changed the script's cleaning logic.

Date Filtering: `--from-date YYYY-MM-DD` / `--to-date YYYY-MM-DD` Fetch messages within a specific timeframe (applied to sent messages).

Skip Markdown: `--skip-summary` Updates the JSON database but doesn't regenerate the .md file.

## Known Issues
Drafts Reliability: AWeber API can be... let's say, eccentric regarding Drafts. Depending on your App Scopes in Labs, the script might skip them with a 401/403 error. I might fix it if I ever find the patience to battle their OAuth scope system again.

## OS Support 
Developed on Linux. Windows users: "Good luck, we're all counting on you."

## Notes
Scopes: Requests account.read, list.read, and email.read.