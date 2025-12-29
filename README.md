# Content & Research Data Exporters

A monorepo containing specialized tools for extracting, archiving, and formatting content from various platforms (AWeber, Buffer/LinkedIn, Blogs) into LLM-friendly formats (Markdown and compressed PDF).

## Why this exists?

As a writer and researcher (publishing as Adam Korga), I generate a lot of content across different platforms. Most of these platforms suffer from "data silos" — they make it easy to put data in, but hard to get it out in a clean, offline, and searchable format.

This repository serves as a bridge between these platforms and a "External Brain" (like a local LLM or a knowledge base). It focuses on:

* **Permanent Archiving**: Downloading media assets locally so they don't disappear when links expire.
* **LLM-Readiness**: Exporting data in formats that models handle best (clean Markdown or consolidated, small PDFs).
* **Efficiency**: Solving the "lazy and impatient" developer's dilemma through semi-automation.

1.  **Practicality over Complexity:** These scripts are built for actual daily use, not for show.
2.  **LLM-Friendly:** Output is optimized for ingestion by Large Language Models (RAG/Review).
3.  **Unified Environment:** All exporters share a common virtual environment and dependencies.

## Repository Structure

```bash
.
├── aweber/               # AWeber newsletter exporter (OAuth2)
├── buffer/               # Buffer/LinkedIn exporter (GraphQL dump parser)
├── blog-crawler/         # Static copy of a script from an Astro project
├── lib/                  # Shared internal library
│   ├── base_utils.py     # DB persistence, HTML cleaning, standardized paths
│   ├── message_model.py  # Common Message Schema (Base class)
│   ├── oauth_session.py  # Generic OAuth2 session handler
│   └── buffer_message.py # Specialized model for social media metrics
├── data/                 # Git-ignored directory for databases and exports
└── requirements.txt      # Global dependencies
```

## Shared Library (`lib/`)

At a certain point in your career, DRY (Don't Repeat Yourself) becomes an involuntary reflex. Yes, this folder is probably a case of overengineering for a bunch of scripts written on the fly, but I just can't help it. :)

The core of this repo is a shared utility library that ensures all exporters behave the same way:

* **BaseMessage**: A standardized schema for any content (ID, Date, Content, Media, Source).
* **Persistence**: Centralized logic to save JSON databases and render Markdown exports.
* **Paths**: Standardized directory structure (`/data/{platform}/media/`).

## Getting Started

### Prerequisites

* Python 3.10+
* GhostScript (`gs`): Required for PDF compression (especially for LinkedIn exports).

### Installation

Entire repo uses single venv for all Python exporters so run this command while beeing in the repository root.

1. Create & Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install Dependencies:

```bash
pip install -r requirements.txt
```

### Available Exporters

**Note**: Each tool has its own README.md in its respective directory with more detailed setup and usage instructions.

1. AWeber Dumper

Uses official OAuth2 API to fetch newsletters.
* Supports ~~draft~~, `scheduled`, and `sent` broadcasts.
* Cleans HTML to readable Markdown.

1. Buffer LinkedIn Dumper

A workaround for the deprecated/paywalled Buffer API.
* Processes manual GraphQL response dumps from Browser Dev Tools.
* **Media Support**: Downloads all images locally.
* **PDF Export**: Generates highly compressed PDFs (e.g., 100MB -> 2.6MB) using GhostScript, perfect for LLM context windows.

1. Blog Crawler

A legacy script imported from an Astro project used for local web archiving.
* **Status**: Provided as-is. This module is not actively developed here. It’s just a static copy of a tool I use elsewhere—I'll probably upload newer versions whenever I remember to do so.

## Performance Tip

When exporting social media history, use the --pdf flag in the Buffer dumper. It creates a single file containing all text and images, which is much easier to manage in an LLM chat than dozens of individual Markdown and image files.

## License

[BookWare](./LICENSE.md)