#!/usr/bin/env python3
"""
Bulk UG tab downloader — processes a list of URLs from a file.

Usage:
    python bulk.py urls.txt
    python bulk.py urls.txt --retry 2 --delay 0.5 --timeout 120 --dump
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import time

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
VENV_PYTHON = sys.executable
OUTPUT_DIR = 'output'
FAILURE_LOG = 'bulk_failed.txt'

# ─── Filename derivation (mirrors app.filename_from_url) ─────────────────────

TAB_TYPES = {'chords', 'tabs', 'tab', 'bass', 'bass-tabs', 'drum', 'drums',
             'ukulele', 'power', 'pro', 'chord-pro', 'video', 'official',
             'guitar-pro'}


def base_from_url(url: str) -> str:
    """Derive the output base name from a UG URL (without extension)."""
    m = re.search(r'/tab/([^/]+)/([^/?#]+)', url)
    if not m:
        return 'tab'

    artist_slug, song_slug = m.group(1), m.group(2)
    song_slug = re.sub(r'-\d+$', '', song_slug)
    parts = [p for p in song_slug.split('-') if p.lower() not in TAB_TYPES]
    song_slug = '-'.join(parts)

    def slugify(s: str) -> str:
        return s.replace('-', ' ').title()

    safe = re.sub(r'[<>:"/\\|?*]', '', f"{slugify(artist_slug)} - {slugify(song_slug)}")
    return safe


def output_exists(base: str) -> bool:
    """Check if any output file matching this base already exists."""
    pattern = os.path.join(OUTPUT_DIR, glob.escape(base) + '.*')
    return bool(glob.glob(pattern))


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Batch download Ultimate Guitar tabs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python bulk.py urls.txt
  python bulk.py urls.txt --retry 2 --delay 0.5
  python bulk.py urls.txt --dump  # debug failing URLs"""
    )
    parser.add_argument('urls_file', help='File with one URL per line (# comments ok)')
    parser.add_argument('--retry', type=int, default=0, metavar='N',
                        help='Retry failed URLs up to N times (default: 0)')
    parser.add_argument('--delay', type=float, default=1.5, metavar='SECONDS',
                        help='Delay between requests (default: 1.5)')
    parser.add_argument('--timeout', type=int, default=60, metavar='SECONDS',
                        help='Per-URL timeout (default: 60)')
    parser.add_argument('--dump', action='store_true',
                        help='Forward --dump to app.py (saves debug HTML)')
    parser.add_argument('--no-resume', action='store_true',
                        help='Re-download even if output files already exist')
    args = parser.parse_args()

    if not os.path.exists(args.urls_file):
        print(f"File not found: {args.urls_file}")
        sys.exit(1)

    with open(args.urls_file) as f:
        urls = [line.strip() for line in f
                if line.strip() and not line.strip().startswith('#')]

    total = len(urls)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Resume: filter out already-downloaded URLs
    skipped = 0
    if not args.no_resume:
        remaining = []
        for url in urls:
            base = base_from_url(url)
            if output_exists(base):
                print(f"SKIP (exists): {base}")
                skipped += 1
            else:
                remaining.append(url)
        urls = remaining

    if skipped:
        print(f"Skipped {skipped} already-downloaded, {len(urls)} remaining\n")
    else:
        print(f"Processing {total} URLs...\n")

    success = 0
    failed = []

    def run_one(url: str) -> tuple[bool, str]:
        """Run app.py on a single URL. Returns (ok, error_message)."""
        cmd = [VENV_PYTHON, APP, url]
        if args.dump:
            cmd.append('--dump')
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=args.timeout)
        except subprocess.TimeoutExpired:
            return False, f"timeout after {args.timeout}s"

        stderr = result.stderr.strip()
        if result.returncode == 0:
            for line in stderr.split('\n'):
                if line.startswith('✓'):
                    print(line)
            return True, ''
        else:
            return False, stderr[:200] if stderr else f"exit code {result.returncode}"

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] ", end="", flush=True)

        ok, err = run_one(url)

        # Retry on failure
        for attempt in range(args.retry):
            if ok:
                break
            print(f"  Retry {attempt + 1}/{args.retry}...", end=" ", flush=True)
            time.sleep(2)
            ok, err = run_one(url)

        if ok:
            success += 1
        else:
            failed.append((url, err))
            print(f"FAILED: {err[:100]}")

        if i < len(urls):
            time.sleep(args.delay)

    total_processed = success + len(failed)
    print(f"\nDone: {success}/{total_processed} successful")
    if skipped:
        print(f"      {skipped} skipped (already existed)")

    if failed:
        print(f"\nFailed ({len(failed)}):")
        for url, err in failed:
            print(f"  {url}")
            print(f"    {err}")

        # Write failure log for later inspection
        with open(FAILURE_LOG, 'w') as f:
            f.write(f"# Bulk run failed URLs — {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            for url, err in failed:
                f.write(f"{url}\n")
        print(f"\nFailure list saved to {FAILURE_LOG}")


if __name__ == '__main__':
    main()
