# Buffer LinkedIn Dumper

A specialized tool to export LinkedIn posts (both sent and scheduled) from Buffer to Markdown and compressed PDF formats.

## The "Why"

Buffer used to provide a decent API for developers, but like many platforms, they've since deprecated it for new apps or hidden data exports behind hefty paywalls. While LinkedIn offers a native data export, it's painfully slow (waiting days for a ZIP file is not my idea of fun) and it still requires separate handling for media assets.

I built this workaround because I'm both lazy and impatient (and that's just a beginning of the list of my virtues!) 

Currently, it requires a bit of manual work with Browser Dev Tools to grab the raw data, but it's still faster than waiting for official exports. I might automate the login/fetch process with a headless browser once the manual repetition becomes more annoying than the effort of coding the automation (the "laziness cycle").

## Prerequisites

* **Python 3.10+**
* **Dependencies:** All required Python dependencie will be installed via setup process described in reporitory root README
* **System Tool:** GhostScript (`gs`) is required for PDF compression.
  - Tested on version `9.55.0`.
  - Without it, PDF files might be massive (e.g., 100MB vs 2.5MB).

## Data Collection Guide

Since we aren't using an official API, we intercept the GraphQL requests Buffer uses for its own web interface.

1.  Login to your [Buffer Publish](https://publish.buffer.com/) dashboard.
2.  Open Browser Developer Tools (F12 or Cmd+Option+I) and switch to the Network tab.
3.  Filter the network requests by the string: `?_o=GetPostList`.

### For Published Posts (Sent):

1.  Navigate to the "Sent" tab in Buffer.
2.  Look for the `GetPostList` request.
3.  Right-click the request -> Copy -> Copy Response.
4.  Save it as `linkedIn-response.sent.1.json` in the `buffer/raw_data_dumps` directory.
5.  Note on Lazy Loading: Buffer only loads 20 posts at a time. Scroll to the bottom of the page to trigger the next fetch. Each scroll will generate a new GetPostList request. Copy these responses as `.sent.2.json`, `.sent.3.json`, etc.
6.  If you are doing an incremental update later, you only need to grab the first page (`.sent.1.json`).

### For Scheduled Posts (Queue):

1.  Navigate to the "Queue" tab.
2.  Repeat the process above, saving the files as `linkedIn-response.queue.1.json`, etc. (if you're using this you won't be probable able to schedule more than 10 posts anyway)

## Usage

Run the script from the root of the repository or the buffer folder:

```bash
python3 buffer/buffer_dumper.py [FLAGS]
```

### Flags

* `--pdf`: Generates a consolidated, compressed PDF of your archive. This is the recommended format for feeding data into LLMs, as Markdown requires managing dozens of separate image files.
* `--full`: Rebuilds the local database from scratch (backups existing `db.json`).

## How it works
1. **JSON Database**: Merges all your JSON fragments into a single `linkedin_db.json`.
2. **Media Archiving**: Automatically downloads all images from Buffer/S3 to a local data/linkedin/media folder to ensure your archive remains permanent even if the original links expire.
3. **Markdown Export**: Generates a clean LLM-friendly Markdown file.
4. **PDF Generation**: Uses fpdf2 to create a document with embedded images and NotoSans support for special characters.
5. **Compression**: Uses GhostScript with the `/screen` setting to shrink the resulting PDF (tested: 101MB -> 2.6MB). Yeah, image resolution is… well, let’s say they could compete with Nokia 7650 but hey, it’s just for summary not printing a publication.

## Troubleshooting
* **Missing Glyphs**: You might see warnings about missing emoji glyphs in the console during PDF generation. The text remains fully readable for LLMs; only the visual representation of emojis in the PDF is affected.
* **GhostScript Errors**: Ensure gs is in your system PATH.
