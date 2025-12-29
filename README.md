# Adam Korga's Queue Exporters

A collection of simple, API-based data exporters used for research and content archival. These tools are designed to extract my data from various platforms into clean, LLM-ready formats (mostly Markdown).

## Core Principles

1.  **Practicality over Complexity:** These scripts are built for actual daily use, not for show.
2.  **LLM-Friendly:** Output is optimized for ingestion by Large Language Models (RAG/Review).
3.  **Unified Environment:** All exporters share a common virtual environment and dependencies.

## Setup & Initialization

All exporters use a shared set of requirements. Initialize the environment from the repository root:

1.  **Create & Activate Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Available Exporters

| Tool | Language | Description | Documentation |
| :--- | :--- |  :--- | :--- |
| **AWeber Exporter** | Python | Extracts newsletter broadcasts (sent, scheduled) with preview text and full content. | [aweber/README.md](./aweber/README.md) |
| **Buffer Exporter** | Python | Parses Buffer's GraphQL files to get full list of published and planned posts (used and tested with LinkedIn but it can be easily adapted to other social medias) | [aweber/README.md](./buffer/README.md) |
| **Blog Crawler** | Node.js | Snapshot of my Astro-based crawler for link checking and PDF archival. | [blog-crawler/README.md](./blog-crawler/README.md) |

## Setup

1.  **Python Tools:** Use the `venv` and `requirements.txt` in the root.
2.  **Node.js Tools:** These are mostly standalone snapshots. See their respective READMEs for local setup (usually involving `npm install puppeteer`).

## Shared Configuration

Most exporters rely on environment variables. Copy the template (if provided in specific folders) or create a `.env` file in the root if the script requires global credentials.

## License

See [LICENSE.md](LICENSE.md) for details.