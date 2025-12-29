# Blog Crawler & PDF Exporter (Node.js)

**Disclaimer:** This is a "code-only" snapshot. It is NOT part of the global Python environment. 

_Note: This script lives in a Node.js ecosystem. Don't try to run it with the Python venv from the root._

This tool is a sub-system of my [AstroWind](https://github.com/onwidget/astrowind) blog setup. It is placed here for archival and reference purposes only. I don't maintain it here; I just copy-paste the latest working version from my main blog repo whenever I feel like it.

## Why it's here
I use this crawler for:
1.  **Regression Testing:** Finding broken links on my production site.
2.  **Archival Analysis:** Exporting my entire blog to PDF so I can review my old content through an LLM. I don't remember what I had for dinner yesterday so don't expect me to remember what I wrote 3 months ago – this is my external memory.

## Integration Details
Setting this up from scratch is a pain and is out of scope for this README. If you know what you are doing, these are the core parts:

### Dependencies
```json
{ 
  "devDependencies": { 
    "puppeteer": "^24.34.0",
    "pdf-lib": "^1.17.1"
  }
}
```

### Script command

```bash
node tools/exporter/generate-pdf.js
```

You can add it in your project's `package.json` as:

```json
"scripts": {
    "export:pdf": "node tools/exporter/generate-pdf.js"
  }
```

### OS level dependencies

Script uses `Ghostscript` executed as external shell (tested on Linux) for compressing resulting PDF. You can probably make it work on other OSes but you're on your own there.

_Note: This script lives in a Node.js ecosystem. Don't try to run it with the Python venv from the root._

