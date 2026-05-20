# ICRA 2026 Program Browser

An interactive GitHub Pages app for browsing and filtering the ICRA 2026 conference program — 2952 papers plus keynotes, panels, and workshops.

## Features

- **Day filter** — hard filter per conference day
- **Session type filter** — Regular, Invited, Interactive, Award, Keynote, Workshop, Tutorial, Panel…
- **Keyword filter** (soft) — select IEEE RAS keywords; matching papers float to the top
- **Author search** — find all papers by a colleague
- **Text search** — substring search across titles and abstracts
- **Semantic search** (soft) — describe what you're looking for; re-ranks by meaning similarity using an in-browser ONNX model (~25 MB, cached after first load)
- **Bookmarks** — star papers; bookmarks persist in your browser's localStorage
- **Export PDF** — print your bookmarked papers as a clean PDF via the browser print dialog

## How it works

### Data pipeline

```
ras.papercept.net (HTML)       scrape.py      →  docs/data/papers.json
                                embed.py       →  docs/data/embeddings.bin
                                               →  docs/data/embeddings_meta.json

2026.ieee-icra.org (HTML/JS)   scrape_events.py → docs/data/events.json
```

**`scrape.py`** fetches the 6 PaperCept content list pages (one per day) and parses them with a state machine over `<tr>` elements. Each `sHdr` row starts a session; each `pHdr` row starts a paper; plain `<tr>` rows hold authors; `<div id="Ab{N}">` holds keywords and abstract. Output: 2952 papers for Tue/Wed/Thu (Sun/Mon/Fri are workshop-only days with a different HTML layout).

**`embed.py`** encodes `title + ". " + abstract` for every paper using `sentence-transformers/all-MiniLM-L6-v2` with `normalize_embeddings=True`, then writes the result as a raw Float32 binary file (~4.3 MB for 2952 × 384). Normalized vectors mean dot product = cosine similarity, so the browser can score queries cheaply.

**`scrape_events.py`** produces three event types:
- **Keynotes** — 24 talks across 6 sessions (Tue/Wed/Thu); hardcoded (names, affiliations, titles, abstracts).
- **Panels** — 6 panels; hardcoded with panelist lists where available.
- **Workshops & tutorials** — 74 entries scraped from the TablePress table on the ICRA 2026 site (requests + BeautifulSoup).

All three share the same JSON schema as papers so the frontend filter/search/render logic handles everything uniformly.

### Frontend

A single-page app in plain HTML + Vanilla JS (no build step, no framework).

- **`app.js`** is an ES module. On load it fetches `papers.json` then `events.json` and merges them.
- **Keyword / semantic filters** are *soft* — they compute a score and re-rank results without hiding anything.
- **Day / author / text filters** are *hard* — they exclude non-matching items entirely.
- **Semantic search** uses [Transformers.js](https://github.com/xenova/transformers.js) (CDN) to run `all-MiniLM-L6-v2` in the browser as an ONNX model, encodes the query, and dots it against the pre-computed `embeddings.bin`. The model (~25 MB) is cached in the browser after first use.
- **Bookmarks** are stored in `localStorage` and survive page reloads. The PDF export populates a hidden `#print-view` div with bookmarked cards and calls `window.print()`.

## Setup

### 1 — Install Python deps (requires [uv](https://docs.astral.sh/uv/))

```bash
cd scrape
uv sync
```

### 2 — Scrape the conference program (papers)

```bash
uv run python scrape.py
# → writes docs/data/papers.json  (2952 papers)
```

### 3 — Scrape keynotes, panels, and workshops

```bash
uv run python scrape_events.py
# → writes docs/data/events.json  (104 events)
```

### 4 — Compute semantic embeddings (optional but recommended)

Downloads `all-MiniLM-L6-v2` (~90 MB) on first run; result is ~5 MB binary.

```bash
uv run python embed.py
# → writes docs/data/embeddings.bin + docs/data/embeddings_meta.json
```

### 5 — Preview locally

```bash
cd docs
python -m http.server 8000
# Open http://localhost:8000
```

> **Note:** The app must be served over HTTP(S), not opened as a `file://` URL —  
> ES module imports and `fetch()` require an HTTP server.

### 6 — Deploy to GitHub Pages

1. Push the repo to GitHub.
2. Go to **Settings → Pages → Source** and set the source to the `docs/` folder.
3. The site will be live at `https://<user>.github.io/<repo>/`.

## Project structure

```
ras-digest/
├── scrape/
│   ├── pyproject.toml       # uv project (requests, beautifulsoup4, lxml,
│   │                        #   sentence-transformers, numpy, crawl4ai)
│   ├── scrape.py            # PaperCept HTML → docs/data/papers.json
│   ├── embed.py             # papers.json → docs/data/embeddings.bin
│   └── scrape_events.py     # ICRA 2026 site → docs/data/events.json
└── docs/                    # GitHub Pages root
    ├── index.html
    ├── app.js
    ├── style.css
    └── data/
        ├── papers.json           (generated)
        ├── events.json           (generated)
        ├── embeddings.bin        (generated, optional)
        └── embeddings_meta.json  (generated, optional)
```
