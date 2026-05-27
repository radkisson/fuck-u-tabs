#!/usr/bin/env python3
"""
Bulk UG tab downloader — processes a list of URLs from a file.
Usage: python bulk.py urls.txt
"""
import subprocess
import sys
import time
import os

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')

# Support both venv/ and .venv/ layouts
_base = os.path.dirname(os.path.abspath(__file__))
_venv_candidates = [
    os.path.join(_base, 'venv', 'bin', 'python'),
    os.path.join(_base, '.venv', 'bin', 'python'),
    os.path.join(_base, 'venv', 'Scripts', 'python.exe'),   # Windows
    os.path.join(_base, '.venv', 'Scripts', 'python.exe'),  # Windows
]
VENV_PYTHON = next((p for p in _venv_candidates if os.path.exists(p)), sys.executable)

def main():
    if len(sys.argv) < 2:
        print("Usage: python bulk.py <urls_file>")
        print("  urls_file: one URL per line, # comments supported")
        sys.exit(1)

    urls_file = sys.argv[1]
    if not os.path.exists(urls_file):
        print(f"File not found: {urls_file}")
        sys.exit(1)

    with open(urls_file) as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    total = len(urls)
    print(f"Processing {total} URLs...\n")

    success = 0
    failed = []

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{total}] ", end="", flush=True)
        result = subprocess.run(
            [VENV_PYTHON, APP, url],
            capture_output=True, text=True, timeout=150
        )
        stderr = result.stderr.strip()
        if result.returncode == 0 and '✓' in stderr:
            success += 1
            # Just print the success line
            for line in stderr.split('\n'):
                if '✓' in line:
                    print(line)
        else:
            failed.append((url, stderr[:200]))
            print(f"FAILED: {stderr[:100]}")

        # Rate limit: 1-2 second between requests
        if i < total:
            time.sleep(1.5)

    print(f"\nDone: {success}/{total} successful")
    if failed:
        print(f"Failed ({len(failed)}):")
        for url, err in failed:
            print(f"  {url}")
            print(f"    {err}")

if __name__ == '__main__':
    main()
