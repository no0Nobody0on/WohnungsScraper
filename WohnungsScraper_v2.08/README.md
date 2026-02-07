# WohnungsScraper

Portable Desktop-Anwendung zur Erkennung illegaler Untervermietung auf deutschen Immobilienportalen.

## Version 5.07

### Features
- **4 Websites**: WG-Gesucht, ImmobilienScout24, Immowelt, Kleinanzeigen
- **2 Suchmodi**: Exakte Suche (Straße + Hausnummer), Erweiterte Suche (Straße + PLZ)
- **2 Suchtiefen**: Schnellsuche (10 Seiten), Vollsuche (50 Seiten)
- **Adressverwaltung**: Hinzufügen, Bearbeiten, Löschen
- **Archiv**: Frühere Suchberichte mit Treffern
- **Export**: Berichte als TXT-Datei

### Neu in v5.07
- **Modulare Code-Struktur** - Separates Modul pro Website
- **Chrome Portable Support** - Für bessere ImmoScout24 Erkennung
- **3 Scraping-Methoden für ImmoScout24**:
  1. nodriver + Chrome Portable (beste Umgehung)
  2. curl_cffi (TLS-Fingerprint)
  3. Playwright Fallback

### Installation

1. Lade die `.exe` von GitHub Releases herunter
2. Optional: Für ImmoScout24 - lege einen `chrome-portable` Ordner an mit Chrome Portable

### Chrome Portable einrichten (für ImmoScout24)

ImmoScout24 verwendet sehr starke Bot-Erkennung. Für beste Ergebnisse:

1. Lade [Chrome Portable](https://portableapps.com/apps/internet/google_chrome_portable) herunter
2. Erstelle einen `chrome-portable` Ordner neben der `.exe`
3. Entpacke Chrome Portable dort hinein
4. Struktur sollte sein: `chrome-portable/App/Chrome-bin/chrome.exe`

### Projektstruktur

```
WohnungsScraper/
├── wohnungsscraper.py      # Haupteinstiegspunkt
├── build_windows.bat       # Build-Script
├── chrome-portable/        # Chrome Portable (optional)
│   └── App/Chrome-bin/chrome.exe
├── data/
│   └── wohnungsscraper_data.db
└── src/
    ├── api/api.py          # PyWebview API
    ├── database/db.py      # SQLite Handler
    ├── scraper/
    │   ├── base.py         # Basis-Klasse + Stealth
    │   ├── wg_gesucht.py   # WG-Gesucht Scraper
    │   ├── immoscout.py    # ImmoScout24 Scraper
    │   ├── immowelt.py     # Immowelt Scraper
    │   ├── kleinanzeigen.py # Kleinanzeigen Scraper
    │   ├── normalizer.py   # Adress-Normalisierung
    │   └── scraper.py      # Haupt-Koordinator
    └── ui/
        ├── static/
        │   ├── css/styles.css
        │   └── js/app.js
        └── templates/index.html
```

### Build

```batch
build_windows.bat
```

### Links

- **Repository**: https://github.com/no0Nobody0on/WohnungsScraper
- **Issues**: https://github.com/no0Nobody0on/WohnungsScraper/issues

### Lizenz

© no0Nobody0on - Alle Rechte vorbehalten
