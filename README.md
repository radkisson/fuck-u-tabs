# 🎸 fuck-u-tabs

> Scrape, clean and export Ultimate Guitar tabs to `.txt` and `.docx` — with proper formatting.

Fork of [FuckYouUG](https://github.com/SeBL4RD/FuckYouUG) with bug fixes applied.

---

## What it does

- Scrapes any Ultimate Guitar tab page and saves a clean, properly formatted file
- Bypasses Cloudflare's TLS fingerprinting — no browser needed for regular tabs
- Exports to **`.txt`** and **`.docx`** simultaneously
- `.docx` output: chord names in **red bold**, tab lines in grey, section headers bold
- Filenames auto-generated from the page: `Neil Young - Natural Beauty.txt`
- All files saved in an `output/` folder
- Downloads **Guitar Pro** (`.gp`, `.gp4`, `.gp5`) files via a headless browser — requires a free UG account
- **Bulk mode**: process a whole list of URLs from a file in one go
- **Version check mode**: list alternate UG tab/chord versions for the same song before downloading

---

## Requirements

- Python 3.10+
- Everything else is installed automatically by the startup scripts.

---

## Quick start

### Windows

Double-click **`start.bat`**. It will:
1. Create a virtual environment if one doesn't exist
2. Install all dependencies
3. Drop you into an interactive prompt

```
Paste your Ultimate Guitar link here (or type exit to quit):
> https://tabs.ultimate-guitar.com/tab/neil-young/natural-beauty-chords-88512
```

### Linux / macOS

```bash
chmod +x start.sh
./start.sh
```

### Manual (any OS)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

python app.py "https://tabs.ultimate-guitar.com/tab/..."
```

---

## Output

For `.../tab/neil-young/natural-beauty-chords-88512`:

```
output/
  Neil Young - Natural Beauty.txt
  Neil Young - Natural Beauty.docx
```

The `.docx` uses Courier New throughout (essential for tab alignment):
- 🔴 **Chord names** — red bold
- ▪ Tab lines — grey monospace
- **[Verse]**, **[Chorus]**, etc. — bold

---

## Bulk mode

Put one URL per line in a text file (lines starting with `#` are treated as comments):

```
# My setlist
https://tabs.ultimate-guitar.com/tab/...
https://tabs.ultimate-guitar.com/tab/...
```

Then run:

```bash
python bulk.py my_urls.txt
```

A 1.5-second delay is applied between requests to avoid rate limiting. GP tabs that require an interactive login are skipped automatically in bulk mode.

---

## Guitar Pro tabs

GP tabs (`.gp`, `.gp4`, `.gp5`) require a **free** UG account — no paid subscription.

On first run, a browser window opens and asks you to sign in. Once logged in, press Enter in the terminal. The session is saved in `session/` and reused on subsequent runs.

```
→ Guitar Pro tab detected.
→ Downloading...
→ If a CAPTCHA appears in the browser, solve it.
✓ output/Iron Maiden - 2 Minutes to Midnight.gp5
```

---

## Other options

```
python app.py --clean       # Read raw tab text from stdin, print cleaned output
python app.py --dump <url>  # Save raw HTML to ug_debug.html for debugging
python app.py --list-versions "<url>"  # List available versions for the same song
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `curl_cffi` | HTTP with Chrome TLS impersonation (Cloudflare bypass) |
| `beautifulsoup4` | HTML parsing |
| `python-docx` | `.docx` export |
| `playwright` | Headless browser for Guitar Pro downloads |

---

## Ethics

This tool scrapes publicly accessible tab pages — the same ones visible for free in your browser. It does not bypass any paywall or access paid content.

The only thing it works around is the deliberate copy-paste sabotage (invisible Unicode characters, scrambled layouts) that UG added to push users toward paid PDF exports.

---

## Roadmap

Currently targets Ultimate Guitar. Open an issue if you need support for another tab site.