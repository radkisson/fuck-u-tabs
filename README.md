# 🎸 FuckYouUG — Ultimate Guitar Tab Scraper

> *Because stealing from the community and calling it a subscription service deserves a response.*

---

## The deal

**Ultimate Guitar** hosts millions of guitar tabs. Almost none of them were written by Ultimate Guitar.

They were written by musicians — hobbyists, bedroom guitarists, music nerds — who transcribed songs by ear and uploaded them **for free**, for the community, because that's what musicians do. For decades, UG was just a place where that goodwill lived.

Then came the pivot. Paywalls. Subscriptions. A mobile app that locks basic features. And, the cherry on top: **intentionally broken copy-paste** — invisible Unicode characters, split divs, scrambled layouts — so you can't even grab a tab without paying for their PDF export.

They didn't create the content. They didn't pay the people who did. They just built a fence around someone else's garden and started charging admission.

**This tool gives you back what was always yours.**

---

## What it does

- Scrapes any Ultimate Guitar tab page and outputs a clean, properly formatted file
- Bypasses Cloudflare's TLS fingerprinting (no browser, no cookies, no bullshit)
- Exports to **`.txt`** and **`.docx`** simultaneously
- In the `.docx`: chord names in **red bold**, tab notation in grey, section headers bold
- Filenames auto-generated from the URL: `Neil Young - Natural Beauty.txt`
- Files saved in an `output/` folder
- Downloads **Guitar Pro** (`.gp`, `.gp4`, `.gp5`) files — requires a free UG account (see below)

---

## Requirements

- Python 3.10+
- That's it. Everything else is handled automatically.

---

## Installation & Usage

### Windows

Just double-click **`start.bat`**.

It will:
1. Create a Python virtual environment if none exists
2. Install all dependencies silently
3. Drop you into an interactive prompt

```
Paste your Ultimate Guitar link here (or type exit to quit):
> https://tabs.ultimate-guitar.com/tab/neil-young/natural-beauty-chords-88512
```

Your files appear in `output/` immediately.

### Linux / macOS

```bash
chmod +x start.sh
./start.sh
```

Same behavior.

---

## Output

For a URL like `.../tab/neil-young/natural-beauty-chords-88512`, you get:

```
output/
  Neil Young - Natural Beauty.txt
  Neil Young - Natural Beauty.docx
```

The `.docx` uses Courier New throughout (essential for tab alignment), with:
- 🔴 **Chord names** — red bold
- ⬜ Tab notation — grey
- **[Section headers]** — bold

---

## Ethics

This tool does not circumvent any payment system. It does not access premium or paid content. It scrapes publicly accessible tab pages — the same ones you can read for free in your browser — and formats them properly.

The only thing it bypasses is the deliberate sabotage of copy-paste that UG introduced to funnel users toward paid exports.

If you have a UG subscription and feel it's worth it, keep it. This tool is for everyone who thinks that hosting community-written content behind a paywall, while refusing to compensate the people who wrote it, is not a business model worth supporting.

---

## Dependencies

| Package | Purpose |
|---|---|
| `curl_cffi` | HTTP with Chrome TLS impersonation (Cloudflare bypass) |
| `beautifulsoup4` | HTML parsing |
| `python-docx` | `.docx` generation |

---

## Guitar Pro tabs

Guitar Pro tabs (`.gp`, `.gp4`, `.gp5`) are handled separately from text tabs. UG gates the download behind a free account — no paid subscription needed, just a login.

**First run:**

The tool will open a browser window (Microsoft Edge or Chrome) and ask you to sign in to Ultimate Guitar. Once you're logged in, press Enter in the terminal. The session is saved locally and reused automatically on subsequent runs — you won't be asked to log in again unless the session expires.

```
→ Guitar Pro tab detected.
→ Downloading...
→ If a CAPTCHA appears in the browser, solve it.
✓ output/Iron Maiden - 2 Minutes to Midnight.gp5
```

The browser window closes automatically once the file is saved.

---

## Roadmap

Currently targets Ultimate Guitar. If you need support for another tab site, open an issue — I'll look into it. The tool is actively maintained and will be updated as sites change their structure.