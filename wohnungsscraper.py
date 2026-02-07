"""
WohnungsScraper - Portable Desktop-Anwendung
Fuer Windows ohne Installation - Komplett portable Version
Version 2.0.8 - Modulare Struktur + Chrome Portable Support
© no0Nobody0on

Modulare Struktur:
- src/database/  -> Datenbank-Handler
- src/scraper/   -> Web-Scraper (modular pro Website)
- src/api/       -> PyWebview API
- src/ui/        -> HTML, CSS, JS Templates
- data/          -> SQLite Datenbank
- chrome-portable/ -> Chrome Portable (optional, für ImmoScout24)
"""

import os
import sys
from pathlib import Path

# Pfade fuer frozen/normale Ausfuehrung
if getattr(sys, 'frozen', False):
    # PyInstaller: _MEIPASS fuer gebundelte Dateien, executable.parent fuer externe
    BUNDLE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(sys.executable).parent
else:
    # Normale Ausfuehrung: alles im gleichen Ordner
    BUNDLE_DIR = Path(__file__).parent
    APP_DIR = Path(__file__).parent

# Browser-Pfad setzen
_BROWSER_PATH = APP_DIR / "playwright-browsers"
if _BROWSER_PATH.exists():
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(_BROWSER_PATH)

import webview

from src.api.api import API


def load_html_content() -> str:
    """Laedt HTML-Template und fuegt CSS/JS inline ein"""
    # UI-Dateien sind im Bundle (MEIPASS bei frozen)
    ui_dir = BUNDLE_DIR / "src" / "ui"
    
    # CSS laden
    css_path = ui_dir / "static" / "css" / "styles.css"
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # JS laden
    js_path = ui_dir / "static" / "js" / "app.js"
    with open(js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    # HTML Template laden
    html_path = ui_dir / "templates" / "index.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Platzhalter ersetzen
    html_content = html_content.replace('{{CSS_CONTENT}}', css_content)
    html_content = html_content.replace('{{JS_CONTENT}}', js_content)
    
    return html_content


def main():
    # Datenbank-Pfad (im App-Ordner, nicht im Bundle)
    data_dir = APP_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    db_path = data_dir / "wohnungsscraper_data.db"
    
    # API initialisieren
    api = API(db_path)
    
    # HTML laden
    html_content = load_html_content()
    
    # Fenster erstellen
    window = webview.create_window(
        'WohnungsScraper v5.07',
        html=html_content,
        js_api=api,
        width=1400,
        height=950,
        min_size=(1200, 850),
        resizable=True,
        frameless=True,
        easy_drag=True
    )
    
    webview.start(debug=False)


if __name__ == '__main__':
    main()
