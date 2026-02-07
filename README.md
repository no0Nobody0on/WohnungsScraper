WohnungsScraper v2.08
Ein tragbares Windows-Programm zur Überwachung von Immobilienportalen auf illegale Untervermietung.

📋 Inhaltsverzeichnis
Überblick
Funktionen
Installation
Automatisch (Installer)
Manuell (Build)
Was wird installiert?
Benutzung
Technische Details
Bekannte Einschränkungen
Implementierung
Überblick
WohnungsScraper durchsucht deutsche Immobilienportale nach Wohnungsanzeigen und vergleicht diese mit einer von Ihnen verwalteten Adressliste. Das Ziel ist es, potenzielle illegale Untervermietungen zu erkennen.

Unterstützte Portale
Portal	Status	Hinweis
WG-Gesucht.de	✅ Funktioniert	Vollständig unterstützt
Immowelt.de	✅ Funktioniert	Nutzt ScrapeOps für Bot-Schutz-Umgehung
Kleinanzeigen.de	✅ Funktioniert	Nur Miet-Anzeigen, PLZ+Straße Abgleich
ImmobilienScout24.de	❌ Blockiert	Starker Bot-Schutz (Imperva)
Funktionen
Adressverwaltung : Adressen hinzufügen, bearbeiten, löschen, importieren/exportieren
Flexible Suche : Schnellsuche (25 Seiten) oder Vollsuche (alle Seiten)
Zwei Suchmodi :
Genau : PLZ + Straße + Hausnummer müssen übereinstimmen
Erweitert : Nur PLZ + Straße müssen übereinstimmen
Berichterstellung : Treffer als Textdatei exportieren
Archiv : Vergangene Suchen einsehen
Tragbar : Keine Installation nötig, läuft direkt vom USB-Stick
Installation
Automatische Installation (Empfohlen)
install_wohnungsscraper.batherunterladen
Die Datei in den gewünschten Ordner verschieben (zB Desktop)
Auf die Datei
Warten bis die Installation abgeschlossen ist (ca. 5-10 Minuten)
Der Installer erledigt automatisch:

Python installieren (falls nicht vorhanden)
Quellcode von GitHub herunterladen
Alle Abhängigkeiten installieren
EXE-Datei erstellen
Aufräumen (nur fertiges Programm bleibt)
Manuelle Installation (Aufbau)
Falls der Installer nicht funktioniert, können Sie das Programm manuell erstellen:

Voraussetzungen
Windows 10/11 (64-Bit)
Python 3.10+ - Download
⚠️Bei der Installation „Add Python to PATH“ aktivieren!
Internetverbindung für Downloads
Schritte
Repository herunterladen :

ZIP herunterladen
In einen Ordner entpacken
build_windows.batausführen :

Direkt aufbuild_windows.bat
Warten bis der Build abgeschlossen ist (5-10 Minuten)
Fertig :

Die EXE befindet sich im dist\WohnungsScraperOrdner
Diesen Ordner können Sie beliebig verschieben
Was wird installiert?
Während des Builds ( build_windows.bat)
Der Build-Prozess führt folgende Schritte aus:

1. Python-Pakete installieren
pip install pywebview playwright beautifulsoup4 pyinstaller nodriver curl_cffi requests
Paket	Zweck
pywebview	Grafische Benutzeroberfläche (GUI)
playwright	Browser-Automatisierung für Scraping
beautifulsoup4	HTML-Parsing
pyinstaller	Erstellt die portable EXE
nodriver	Alternative Browser-Steuerung
curl_cffi	HTTP-Anfragen mit Browser-Fingerprint
requests	HTTP-Anfragen für ScrapeOps
2. Playwright Browser installieren
playwright install chromium
Lädt einen Chromium-Browser herunter (~150 MB)
Wird für das Scraping der Webseiten benötigt
3. Chrome Portable herunterladen (optional)
Laden Sie Google Chrome Portable herunter
Verbessert die Browser-Fingerabdruck-Tarnung
Wird für ImmoScout24 benötigt (funktioniert aber trotzdem nicht wegen Imperva)
4. EXE mit PyInstaller erstellen
pyinstaller --onedir --windowed --name WohnungsScraper ...
Packt Python + alle Abhängigkeiten in einen Ordner
ErstelltWohnungsScraper.exe
Finale Ordnerstruktur
Nach erfolgreicher Installation:

WohnungsScraper/
├── WohnungsScraper.exe      # Hauptprogramm (starten!)
├── data/                    # Datenbank-Ordner
│   └── wohnungsscraper.db   # SQLite-Datenbank (wird beim ersten Start erstellt)
├── _internal/               # Python-Laufzeitumgebung + Abhängigkeiten
│   ├── playwright-browsers/ # Chromium Browser für Scraping
│   └── ...                  # Weitere Python-Module
└── chrome-portable/         # Google Chrome Portable (optional)
Platz
Download : ~50 MB (ZIP)
Nach Build : ~500-700 MB (inkl. Browser)
Davon Chromium : ~400 MB
Benutzung
Programm starten
WohnungsScraper.exeDoppelklicken
Ein Fenster mit der Benutzeroberfläche öffnet sich
Adressen verwalten
Registerkarte "Adressen" auswählen
Adresse hinzufügen :
Straße (zB „Maximilianstraße“)
Hausnummer (zB „15“ oder „15a“)
PLZ (zB "80539")
Stadt (zB "München")
Auf "Hinzufügen" klicken
Suche starten
Tab "Suche" auswählen
Webseiten auswählen (Checkboxen)
Suchmodus wählen :
Schnell (25 Seiten) - für schnelle Übersicht
Vollsuche (alle Seiten) - für gründliche Suche
Genauigkeit wählen :
Exakt (PLZ + Straße + Hausnummer)
Erweitert (PLZ + Straße)
Auf "Suche starten" klicken
Warten bis die Suche abgeschlossen ist
Ergebnisse
Treffer werden in der Liste angezeigt
Klick auf einen Treffer öffnet die Anzeige im Browser
„Bericht exportieren“ speichert alle Treffer als Textdatei
Technische Details
ScrapeOps-Integration
Für Immowelt wird ein externer Dienst (ScrapeOps) verwendet, um den DataDome Bot-Schutz zu umgehen:

API-Key ist im Programm eingebaut
Kostenlose Limits : 1.000 Anfragen/Monat
Was passiert : Anfragen werden über ScrapeOps-Server geleitet, die den Bot-Schutz umgehen
Browser-Fingerabdruck-Spoofing
Das Programm tarnt sich als normaler Browser durch:

WebDriver-Erkennung entfernen
Navigator-Eigenschaften anpassen
Chrome-Objekt simulieren
WebGL/Canvas-Spoofing
Und weitere Techniken...
Datenbank
SQLite- Datenbank im dataOrdner
Gespeichert: Adressen, Berichte, Treffer
.dbKann durch Kopieren der Datei gesichert werden
Bekannte Einschränkungen
ImmobilienScout24 (Blockiert)
Status : ❌ Funktioniert nicht
Grund : Imperva Bot-Schutz erkennt alle Scraping-Versuche
Getestete Lösungen : Alle fehlgeschlagen
Mögliche Lösung : Offizielle Partner-API (Registrierung erforderlich)
Kleinanzeigen
Hinweis : Nur PLZ + Straßenabgleich möglich
Grund : Anzeigen enthalten selten vollständige Adressen
Empfehlung : Treffer manuell überprüfen
ScrapeOps-Grenzen
1.000 Anfragen/Monat kostenlos
Bei Überschreitung: Immowelt funktioniert nur noch eingeschränkt
Implementierung
"Python nicht gefunden"
Python von python.org installieren
Wichtig : „Python zu PATH hinzufügen“ aktivieren!
Computer neu starten
Installer erneut ausgeführt
"Tcl-Datenverzeichnis nicht gefunden"
Dieser Fehler sollte in Version 2.08 nicht mehr auftreten
Falls doch: build_windows.batmanuell ausführen
„Chrome Portable Download fehlgeschlagen“
Kein kritischer Fehler
Das Programm funktioniert auch ohne Chrome Portable
Nur für ImmoScout24 relevant (welches ohnehin blockiert ist)
Antivirus-Warnung
PyInstaller-EXEs werden manchmal fälschlich als Virus erkannt
Lösung : Ausnahme im Antivirus hinzufügen
Der Quellcode ist vollständig einsehbar und sicher
Suche findet keine Treffer
Überprüfen Sie, ob die Adressen korrekt eingegeben sind
„Erweiterte Suche“ statt „Exakte Suche“ verwenden
Andere Webseiten versuchen
Lizenz & Credits
Version : 2.08
Copyright : © no0Nobody0on
Lizenz : Privat

Verwendete Open-Source-Bibliotheken
pywebview
Dramatiker
Wunderschöne Suppe
PyInstaller
Änderungsprotokoll
Version 2.08 (06.02.2025)
Schnellsuche: 25 Seiten (vorher 10)
Vollsuche: Alle Seiten unbegrenzt (vorher 50)
Exakte Suche: PLZ + Straße + Hausnummer
Erweiterte Suche: PLZ + Straße
Kleinanzeigen: Nur Miet-Anzeigen (Filter)
ScrapeOps-Integration für Immowelt
tkinter entfernt (verursachter Fehler)
Installer verbessert
Version 2.07
Modulare Code-Struktur
Chrome Portable-Unterstützung
Verbessertes Fingerabdruck-Spoofing
