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
            return result  # Brut : tags [ch] et [tab] préservés pour le docx
        print("  → JSON UG non trouvé, fallback générique.", file=sys.stderr)

    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'footer', 'header',
                     'aside', 'iframe', 'noscript', 'button']):
        tag.decompose()

    return extract_generic(soup)


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


# ─── Export DOCX ─────────────────────────────────────────────────────────────

# Regex pour reconnaître un token accord : Em7, Cmaj9, D5, Cadd9, G/B, etc.
_CHORD_RE = re.compile(
    r'^[A-G][#b]?(?:maj|min|sus|aug|dim|add|M|m)?\d*(?:\/[A-G][#b]?)?$'
)


def _is_chord_line(line: str) -> bool:
    """True si la ligne ne contient que des noms d'accords (et marqueurs x2, *)."""
    cleaned = re.sub(r'\*|x\d+', '', line)
    tokens = cleaned.strip().split()
    return bool(tokens) and all(_CHORD_RE.match(t) for t in tokens)


def _is_tab_line(line: str) -> bool:
    """True si la ligne est une notation tablature (e|--, B|--, d|--, etc.)."""
    return bool(re.match(r'^\s*[eEBbGgDdAa]\|', line))


def write_docx(raw: str, path: str, title: str) -> bool:
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Cm
    except ImportError:
        print("  python-docx non installé : pip install python-docx", file=sys.stderr)
        return False

    RED  = RGBColor(0xC4, 0x1E, 0x3A)
    GREY = RGBColor(0x99, 0x99, 0x99)
    FONT = 'Courier New'
    SIZE = Pt(9)

    doc = Document()

    # Marges 1 cm partout
    for section in doc.sections:
        section.top_margin    = Cm(1)
        section.bottom_margin = Cm(1)
        section.left_margin   = Cm(1)
        section.right_margin  = Cm(1)

    # Style Normal : monospace, zéro espacement inter-paragraphe
    normal = doc.styles['Normal']
    normal.font.name = FONT
    normal.font.size = SIZE
    normal.paragraph_format.space_after  = Pt(0)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.line_spacing = Pt(11)

    doc.add_heading(title, level=1)

    def _para(space_before=0):
        p = doc.add_paragraph()
        p.paragraph_format.space_after  = Pt(0)
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.line_spacing = Pt(11)
        return p

    def _run(p, text, bold=False, color=None):
        r = p.add_run(text)
        r.font.name = FONT
        r.font.size = SIZE
        if bold:
            r.bold = True
        if color:
            r.font.color.rgb = color
        return r

    # Normalise les fins de ligne Windows + consolide les blancs
    text = normalize_whitespace(raw)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)

    segments = re.split(r'(\[tab\].*?\[/tab\])', text, flags=re.DOTALL)

    for segment in segments:
        if segment.startswith('[tab]') and segment.endswith('[/tab]'):
            inner = segment[5:-6]
            for line in inner.split('\n'):
                line = line.rstrip()
                stripped = line.strip()
                if not stripped:
                    continue

                # Ligne de tablature réelle (e|--, B|--, etc.) → gris
                if _is_tab_line(line):
                    clean = re.sub(r'\[ch\](.*?)\[/ch\]', r'\1', line)
                    _run(_para(), clean, color=GREY)
                # Ligne avec [ch] tags → accords en rouge, reste normal
                elif '[ch]' in line:
                    p = _para()
                    for part in re.split(r'(\[ch\].*?\[/ch\])', line):
                        m = re.match(r'\[ch\](.*?)\[/ch\]', part)
                        if m:
                            _run(p, m.group(1), bold=True, color=RED)
                        else:
                            _run(p, part)
                # Ligne d'accords sans tags → rouge
                elif _is_chord_line(stripped):
                    _run(_para(), line, bold=True, color=RED)
                # Paroles ou commentaire → normal
                else:
                    _run(_para(), line)

        else:
            blank_count = 0
            for line in segment.split('\n'):
                line = line.rstrip()
                stripped = line.strip()

                if not stripped:
                    blank_count += 1
                    if blank_count == 1:
                        _para()  # Une seule ligne vide par groupe de blancs
                    continue
                blank_count = 0

                # En-tête de section : [Intro], [Verse 1], etc.
                if re.match(r'^\[[^\[\]/]+\]$', stripped):
                    _run(_para(space_before=5), stripped, bold=True)
                    continue

                # Ligne avec [ch] tags inline
                if '[ch]' in line:
                    p = _para()
                    for part in re.split(r'(\[ch\].*?\[/ch\])', line):
                        m = re.match(r'\[ch\](.*?)\[/ch\]', part)
                        if m:
                            _run(p, m.group(1), bold=True, color=RED)
                        else:
                            _run(p, part)
                    continue

                # Ligne d'accords pure
                if _is_chord_line(stripped):
                    _run(_para(), line, bold=True, color=RED)
                    continue

                # Texte normal
                _run(_para(), line)

    doc.save(path)
    return True


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

    raw = scrape(args.url, dump=args.dump)

    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base = re.sub(r'\.txt$', '', filename_from_url(args.url))
    base_path = os.path.join(OUTPUT_DIR, base)

    txt_path = base_path + '.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(clean_text(raw))
    print(f"✓ {txt_path}", file=sys.stderr)

    docx_path = base_path + '.docx'
    if write_docx(raw, docx_path, base):
        print(f"✓ {docx_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
