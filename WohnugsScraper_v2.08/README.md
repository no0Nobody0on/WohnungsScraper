# WohnungsScraper v2.08

Ein portables Windows-Programm zur Überwachung von Immobilienportalen auf illegale Untervermietung.

---

## 📋 Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Funktionen](#funktionen)
3. [Installation](#installation)
   - [Automatisch (Installer)](#automatische-installation-empfohlen)
   - [Manuell (Build)](#manuelle-installation-build)
4. [Was wird installiert?](#was-wird-installiert)
5. [Benutzung](#benutzung)
6. [Technische Details](#technische-details)
7. [Bekannte Einschränkungen](#bekannte-einschränkungen)
8. [Fehlerbehebung](#fehlerbehebung)

---

## Überblick

**WohnungsScraper** durchsucht deutsche Immobilienportale nach Wohnungsanzeigen und vergleicht diese mit einer von Ihnen verwalteten Adressliste. Das Ziel ist es, potenzielle illegale Untervermietungen zu erkennen.

### Unterstützte Portale

| Portal | Status | Hinweis |
|--------|--------|---------|
| WG-Gesucht.de | ✅ Funktioniert | Vollständig unterstützt |
| Immowelt.de | ✅ Funktioniert | Nutzt ScrapeOps für Bot-Schutz-Umgehung |
| Kleinanzeigen.de | ✅ Funktioniert | Nur Miet-Anzeigen, PLZ+Straße Abgleich |
| ImmobilienScout24.de | ❌ Blockiert | Starker Bot-Schutz (Imperva) |

---

## Funktionen

- **Adressverwaltung**: Adressen hinzufügen, bearbeiten, löschen, importieren/exportieren
- **Flexible Suche**: Schnellsuche (25 Seiten) oder Vollsuche (alle Seiten)
- **Zwei Suchmodi**:
  - **Exakt**: PLZ + Straße + Hausnummer müssen übereinstimmen
  - **Erweitert**: Nur PLZ + Straße müssen übereinstimmen
- **Berichterstellung**: Treffer als Textdatei exportieren
- **Archiv**: Vergangene Suchen einsehen
- **Portable**: Keine Installation nötig, läuft direkt von USB-Stick

---

## Installation

### Automatische Installation (Empfohlen)

1. **`install_wohnungsscraper.bat`** herunterladen
2. Die Datei in den gewünschten Ordner verschieben (z.B. Desktop)
3. **Doppelklick** auf die Datei
4. Warten bis die Installation abgeschlossen ist (ca. 5-10 Minuten)

Der Installer erledigt automatisch:
- Python installieren (falls nicht vorhanden)
- Quellcode von GitHub herunterladen
- Alle Abhängigkeiten installieren
- EXE-Datei erstellen
- Aufräumen (nur fertiges Programm bleibt)

### Manuelle Installation (Build)

Falls der Installer nicht funktioniert, können Sie das Programm manuell bauen:

#### Voraussetzungen

- **Windows 10/11** (64-bit)
- **Python 3.10+** - [Download](https://www.python.org/downloads/)
  - ⚠️ Bei Installation "Add Python to PATH" aktivieren!
- **Internetverbindung** für Downloads

#### Schritte

1. **Repository herunterladen**:
   - [ZIP herunterladen](https://github.com/no0Nobody0on/WohnungsScraper/archive/refs/heads/main.zip)
   - In einen Ordner entpacken

2. **`build_windows.bat` ausführen**:
   - Doppelklick auf `build_windows.bat`
   - Warten bis der Build abgeschlossen ist (5-10 Minuten)

3. **Fertig**:
   - Die EXE befindet sich im `dist\WohnungsScraper` Ordner
   - Diesen Ordner können Sie beliebig verschieben

---

## Was wird installiert?

### Während des Builds (`build_windows.bat`)

Der Build-Prozess führt folgende Schritte aus:

#### 1. Python-Pakete installieren
```
pip install pywebview playwright beautifulsoup4 pyinstaller nodriver curl_cffi requests
```

| Paket | Zweck |
|-------|-------|
| `pywebview` | Grafische Benutzeroberfläche (GUI) |
| `playwright` | Browser-Automatisierung für Scraping |
| `beautifulsoup4` | HTML-Parsing |
| `pyinstaller` | Erstellt die portable EXE |
| `nodriver` | Alternative Browser-Steuerung |
| `curl_cffi` | HTTP-Anfragen mit Browser-Fingerprint |
| `requests` | HTTP-Anfragen für ScrapeOps |

#### 2. Playwright Browser installieren
```
playwright install chromium
```
- Lädt einen Chromium-Browser herunter (~150 MB)
- Wird für das Scraping der Webseiten benötigt

#### 3. Chrome Portable herunterladen (Optional)
- Lädt Google Chrome Portable herunter
- Verbessert die Browser-Fingerabdruck-Tarnung
- Wird für ImmoScout24 benötigt (funktioniert aber trotzdem nicht wegen Imperva)

#### 4. EXE erstellen mit PyInstaller
```
pyinstaller --onedir --windowed --name WohnungsScraper ...
```
- Packt Python + alle Abhängigkeiten in einen Ordner
- Erstellt `WohnungsScraper.exe`

### Finale Ordnerstruktur

Nach erfolgreicher Installation:

```
WohnungsScraper/
├── WohnungsScraper.exe      # Hauptprogramm (starten!)
├── data/                    # Datenbank-Ordner
│   └── wohnungsscraper.db   # SQLite-Datenbank (wird beim ersten Start erstellt)
├── _internal/               # Python-Laufzeitumgebung + Abhängigkeiten
│   ├── playwright-browsers/ # Chromium Browser für Scraping
│   └── ...                  # Weitere Python-Module
└── chrome-portable/         # Google Chrome Portable (optional)
```

### Speicherplatz

- **Download**: ~50 MB (ZIP)
- **Nach Build**: ~500-700 MB (inkl. Browser)
- **Davon Chromium**: ~400 MB

---

## Benutzung

### Programm starten

1. **`WohnungsScraper.exe`** doppelklicken
2. Ein Fenster mit der Benutzeroberfläche öffnet sich

### Adressen verwalten

1. **Tab "Adressen"** auswählen
2. **Adresse hinzufügen**:
   - Straße (z.B. "Maximilianstraße")
   - Hausnummer (z.B. "15" oder "15a")
   - PLZ (z.B. "80539")
   - Stadt (z.B. "München")
3. Auf **"Hinzufügen"** klicken

### Suche starten

1. **Tab "Suche"** auswählen
2. **Webseiten auswählen** (Checkboxen)
3. **Suchmodus wählen**:
   - Schnell (25 Seiten) - für schnelle Übersicht
   - Vollsuche (alle Seiten) - für gründliche Suche
4. **Genauigkeit wählen**:
   - Exakt (PLZ + Straße + Hausnummer)
   - Erweitert (PLZ + Straße)
5. Auf **"Suche starten"** klicken
6. Warten bis die Suche abgeschlossen ist

### Ergebnisse

- **Treffer** werden in der Liste angezeigt
- **Klick auf einen Treffer** öffnet die Anzeige im Browser
- **"Bericht exportieren"** speichert alle Treffer als Textdatei

---

## Technische Details

### ScrapeOps Integration

Für **Immowelt** wird ein externer Dienst (ScrapeOps) verwendet, um den DataDome Bot-Schutz zu umgehen:

- **API-Key** ist im Programm eingebaut
- **Kostenlose Limits**: 1.000 Anfragen/Monat
- **Was passiert**: Anfragen werden über ScrapeOps-Server geleitet, die den Bot-Schutz umgehen

### Browser-Fingerprint-Spoofing

Das Programm tarnt sich als normaler Browser durch:

- WebDriver-Erkennung entfernen
- Navigator-Properties anpassen
- Chrome-Objekt simulieren
- WebGL/Canvas-Spoofing
- Und weitere Techniken...

### Datenbank

- **SQLite** Datenbank im `data` Ordner
- Speichert: Adressen, Berichte, Treffer
- Kann gesichert werden durch Kopieren der `.db` Datei

---

## Bekannte Einschränkungen

### ImmobilienScout24 (Blockiert)

- **Status**: ❌ Funktioniert nicht
- **Grund**: Imperva Bot-Schutz erkennt alle Scraping-Versuche
- **Getestete Lösungen**: Alle fehlgeschlagen
- **Mögliche Lösung**: Offizielle Partner-API (benötigt Registrierung)

### Kleinanzeigen

- **Hinweis**: Nur PLZ + Straße Abgleich möglich
- **Grund**: Anzeigen enthalten selten vollständige Adressen
- **Empfehlung**: Treffer manuell überprüfen

### ScrapeOps Limits

- **1.000 Anfragen/Monat** kostenlos
- Bei Überschreitung: Immowelt funktioniert nur noch eingeschränkt

---

## Fehlerbehebung

### "Python nicht gefunden"

1. Python von [python.org](https://www.python.org/downloads/) installieren
2. **Wichtig**: "Add Python to PATH" aktivieren!
3. Computer neu starten
4. Installer erneut ausführen

### "Tcl data directory not found"

- Dieser Fehler sollte in Version 2.08 nicht mehr auftreten
- Falls doch: `build_windows.bat` manuell ausführen

### "Chrome Portable Download fehlgeschlagen"

- Kein kritischer Fehler
- Das Programm funktioniert auch ohne Chrome Portable
- Nur für ImmoScout24 relevant (welches ohnehin blockiert ist)

### Antivirus-Warnung

- PyInstaller-EXEs werden manchmal fälschlich als Virus erkannt
- **Lösung**: Ausnahme im Antivirus hinzufügen
- Der Quellcode ist vollständig einsehbar und sicher

### Suche findet keine Treffer

1. Prüfen ob Adressen korrekt eingegeben sind
2. "Erweiterte Suche" statt "Exakte Suche" verwenden
3. Andere Webseiten probieren

---

## Lizenz & Credits

**Version**: 2.08  
**Copyright**: © no0Nobody0on  
**Lizenz**: Privat

### Verwendete Open-Source-Bibliotheken

- [pywebview](https://pywebview.flowrl.com/)
- [Playwright](https://playwright.dev/)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- [PyInstaller](https://pyinstaller.org/)

---

## Changelog

### v2.08 (2025-02-06)
- Schnellsuche: 25 Seiten (vorher 10)
- Vollsuche: Alle Seiten unbegrenzt (vorher 50)
- Exakte Suche: PLZ + Straße + Hausnummer
- Erweiterte Suche: PLZ + Straße
- Kleinanzeigen: Nur Miet-Anzeigen (Filter)
- ScrapeOps Integration für Immowelt
- tkinter entfernt (verursachte Fehler)
- Installer verbessert

### v2.07
- Modulare Code-Struktur
- Chrome Portable Support
- Verbessertes Fingerprint-Spoofing
