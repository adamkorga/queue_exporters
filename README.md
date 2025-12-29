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

| Tool | Description | Documentation |
| :--- | :--- | :--- |
| **AWeber Exporter** | Extracts newsletter broadcasts (sent, scheduled) with preview text and full content. | [aweber/README.md](./aweber/README.md) |
| *More coming soon* | *Scripts for other platforms are currently being migrated.* | |

---

## Shared Configuration

Most exporters rely on environment variables. Copy the template (if provided in specific folders) or create a `.env` file in the root if the script requires global credentials.

## License

See [LICENSE.md](LICENSE.md) for details.