#!/usr/bin/env python3
"""
Tab Scraper & Formatter
Scrape guitar tabs and output clean text.

Usage:
    python app.py "https://tabs.ultimate-guitar.com/tab/..."
    python app.py "https://..." -o output.txt
    python app.py --clean
"""

import sys
import re
import json
import argparse

try:
    from curl_cffi import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installe les dépendances :")
    print("  pip install curl_cffi beautifulsoup4")
    sys.exit(1)


# ─── Nettoyage texte ───────────────────────────────────────────────────────────

def normalize_whitespace(text: str) -> str:
    for ch in [' ', ' ', ' ']:
        text = text.replace(ch, ' ')
    for ch in ['​', '‌', '‍', '﻿']:
        text = text.replace(ch, '')
    return text


def fix_tab_lines(text: str) -> str:
    lines = text.split('\n')
    result = []
    tab_buffer = {}
    tab_order = ['e', 'B', 'G', 'D', 'A', 'E', 'd', 'b', 'g']

    def flush():
        out = [tab_buffer[s] for s in tab_order if s in tab_buffer]
        tab_buffer.clear()
        return out

    for line in lines:
        stripped = line.rstrip()
        m = re.match(r'^([eEBbGgDdAa])\|(.*)$', stripped)
        if m:
            note = m.group(1)
            if note in tab_buffer:
                result.extend(flush())
            tab_buffer[note] = stripped
        else:
            result.extend(flush())
            result.append(stripped)

    result.extend(flush())
    return '\n'.join(result)


def strip_ug_tags(text: str) -> str:
    """Supprime les balises propriétaires UG : [ch], [tab], [verse], etc."""
    text = re.sub(r'\[ch\](.*?)\[/ch\]', r'\1', text)   # [ch]Em7[/ch] → Em7
    text = re.sub(r'\[tab\](.*?)\[/tab\]', r'\1', text, flags=re.DOTALL)
    # Sections comme [Intro], [Verse 1], [Chorus] — on garde, juste normalise
    return text


def clean_text(raw: str) -> str:
    text = normalize_whitespace(raw)
    text = strip_ug_tags(text)
    text = re.sub(r'^\s*Page\s+\d+/\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    text = re.sub(r'^\s*(\[.+?\])\s*$', r'\1', text, flags=re.MULTILINE)
    text = fix_tab_lines(text)
    return text.strip()


# ─── Scraping ─────────────────────────────────────────────────────────────────

def fetch(url: str) -> str:
    """Récupère le HTML en impersonnant Chrome (contourne Cloudflare/TLS checks)."""
    resp = requests.get(
        url,
        impersonate="chrome124",
        timeout=20,
        headers={
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'DNT': '1',
        },
    )
    if resp.status_code == 403:
        print(f"  403 Forbidden — Cloudflare bloque toujours.", file=sys.stderr)
        print(f"  Essaie le mode --clean : copie-colle le texte de la page.", file=sys.stderr)
        resp.raise_for_status()
    resp.raise_for_status()
    return resp.text


def extract_ug_json(html: str) -> str | None:
    """Extrait le contenu depuis le div js-store d'Ultimate Guitar."""
    soup = BeautifulSoup(html, 'html.parser')
    div = soup.find('div', class_='js-store')
    if not div:
        return None
    try:
        data = json.loads(str(div['data-content']))
        content = (
            data.get('store', {})
                .get('page', {})
                .get('data', {})
                .get('tab_view', {})
                .get('wiki_tab', {})
                .get('content', '')
        )
        return content or None
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def extract_generic(soup: BeautifulSoup) -> str:
    pres = soup.find_all('pre')
    if pres:
        return max(pres, key=lambda p: len(p.get_text())).get_text('\n')

    candidates = soup.find_all(
        ['div', 'section', 'article'],
        class_=re.compile(r'tab|chord|lyric|content|song|sheet', re.I)
    )
    if candidates:
        return max(candidates, key=lambda el: len(el.get_text())).get_text('\n')

    blocks = soup.find_all(['div', 'article', 'main', 'section'])
    if blocks:
        return max(blocks, key=lambda el: len(el.get_text())).get_text('\n')

    return soup.get_text('\n')


def scrape(url: str, dump: bool = False) -> str:
    print(f"→ Scraping : {url}", file=sys.stderr)
    html = fetch(url)

    if dump:
        dump_path = 'ug_debug.html'
        with open(dump_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  → HTML brut sauvegardé dans {dump_path}", file=sys.stderr)

    if 'ultimate-guitar' in url:
        result = extract_ug_json(html)
        if result:
            print("  → Données UG extraites.", file=sys.stderr)
            return clean_text(result)
        print("  → JSON UG non trouvé, fallback générique.", file=sys.stderr)

    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'footer', 'header',
                     'aside', 'iframe', 'noscript', 'button']):
        tag.decompose()

    return clean_text(extract_generic(soup))


# ─── Nom de fichier depuis l'URL ─────────────────────────────────────────────

TAB_TYPES = {'chords', 'tabs', 'tab', 'bass', 'bass-tabs', 'drum', 'drums',
             'ukulele', 'power', 'pro', 'chord-pro', 'video', 'official'}


def filename_from_url(url: str) -> str:
    """
    Extrait artiste + titre depuis une URL UG et retourne un nom de fichier propre.
    Ex: .../tab/neil-young/natural-beauty-chords-88512 → Neil Young - Natural Beauty.txt
    """
    m = re.search(r'/tab/([^/]+)/([^/?#]+)', url)
    if not m:
        return 'tab.txt'

    artist_slug, song_slug = m.group(1), m.group(2)

    # Retire l'ID numérique final
    song_slug = re.sub(r'-\d+$', '', song_slug)

    # Retire les suffixes de type (chords, tabs, etc.)
    parts = song_slug.split('-')
    parts = [p for p in parts if p.lower() not in TAB_TYPES]
    song_slug = '-'.join(parts)

    def slugify(s: str) -> str:
        return s.replace('-', ' ').title()

    artist = slugify(artist_slug)
    song = slugify(song_slug)

    # Sanitize pour le système de fichiers
    safe = re.sub(r'[<>:"/\\|?*]', '', f"{artist} - {song}")
    return f"{safe}.txt"


# ─── Mode nettoyage (stdin) ───────────────────────────────────────────────────

def clean_stdin() -> str:
    print("Colle le texte, puis Ctrl+Z + Entrée :", file=sys.stderr)
    return clean_text(sys.stdin.read())


# ─── CLI ──────────────────────────────────────────────────────────────────────

OUTPUT_DIR = 'output'


def main():
    parser = argparse.ArgumentParser(
        description='Scrape et nettoie des tablatures guitare.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python app.py "https://tabs.ultimate-guitar.com/tab/neil-young/natural-beauty-chords-88512"
  python app.py --clean
"""
    )
    parser.add_argument('url', nargs='?', help='URL de la page (entre guillemets)')
    parser.add_argument('--clean', action='store_true',
                        help='Mode nettoyage : lis depuis stdin (copier-coller)')
    parser.add_argument('--dump', action='store_true',
                        help='Sauvegarde le HTML brut dans ug_debug.html (debug)')
    args = parser.parse_args()

    if args.clean:
        result = clean_stdin()
        print(result)
        return

    if not args.url:
        parser.print_help()
        sys.exit(1)

    result = scrape(args.url, dump=args.dump)

    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = filename_from_url(args.url)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"✓ {path}", file=sys.stderr)


if __name__ == '__main__':
    main()
