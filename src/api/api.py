"""
WohnungsScraper - API Module
PyWebview API Endpoints
"""

import os
import threading
import asyncio
import webbrowser
from datetime import datetime
from pathlib import Path

import webview

from ..database.db import Database
from ..scraper.scraper import BatchScraper


class API:
    def __init__(self, db_path: Path):
        self.db = Database(db_path)
        self.search_running = False
        self.search_logs = []
        self.search_progress = {
            "current_site": 0, 
            "total_sites": 0, 
            "website": "", 
            "page": 0, 
            "max_page": 0, 
            "percent": 0, 
            "action": "", 
            "matches": 0, 
            "listings": 0
        }
        self.current_matches = []
        self.start_time = None
        self.selected_websites = None
        self._scraper = None
        self._max_pages = 10
        self._total_pages_work = 0
        self._completed_pages = 0
    
    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.search_logs.insert(0, entry)
        if len(self.search_logs) > 500:
            self.search_logs = self.search_logs[:500]
        print(entry)
    
    def _is_stopped(self) -> bool:
        """Callback fuer Scraper um zu pruefen ob gestoppt werden soll"""
        return not self.search_running
    
    def _update_page_progress(self, page: int, max_page: int):
        """Callback fuer Scraper um Seitenfortschritt zu melden"""
        self._completed_pages += 1
        # 95% fuer Scraping, 5% fuer Abgleich
        percent = int((self._completed_pages / self._total_pages_work) * 95)
        self.search_progress.update({
            "page": page,
            "max_page": max_page,
            "percent": min(percent, 95),
            "action": f"Seite {page}/{max_page}"
        })
    
    # Address Methods
    def get_addresses(self):
        return self.db.get_addresses()
    
    def get_address(self, id):
        return self.db.get_address(id)
    
    def add_address(self, street, house_number, postal_code, city, notes=""):
        return self.db.add_address(street, house_number, postal_code, city, notes)
    
    def update_address(self, id, street, house_number, postal_code, city, notes=""):
        return self.db.update_address(id, street, house_number, postal_code, city, notes)
    
    def delete_address(self, id):
        return self.db.delete_address(id)
    
    # Report Methods
    def get_reports(self):
        return self.db.get_reports()
    
    def delete_report(self, id):
        return self.db.delete_report(id)
    
    def export_report(self, report_id):
        """Exportiert einen Bericht als TXT-Datei"""
        reports = self.db.get_reports()
        report = next((r for r in reports if r['id'] == report_id), None)
        
        if not report:
            return {"success": False, "error": "Bericht nicht gefunden"}
        
        matches = report.get('matches', [])
        date_str = datetime.fromisoformat(report['started_at']).strftime("%d.%m.%Y %H:%M")
        
        lines = []
        lines.append("=" * 60)
        lines.append("          WOHNUNGSSCRAPER - SUCHBERICHT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Datum: {date_str}")
        lines.append(f"Adressen geprueft: {report['addresses_checked']}")
        lines.append(f"Treffer gefunden: {len(matches)}")
        lines.append(f"Suchmodus: {'Schnellsuche' if report['search_mode'] == 'quick' else 'Vollsuche'}")
        lines.append("")
        lines.append("=" * 60)
        lines.append("               GEFUNDENE INSERATE")
        lines.append("=" * 60)
        lines.append("")
        
        for i, m in enumerate(matches, 1):
            lines.append("-" * 50)
            lines.append(f"Treffer #{i}")
            lines.append("-" * 50)
            lines.append(f"Adresse: {m.get('address_display', '-')}")
            lines.append(f"Website: {m.get('website_name', m.get('website', '-'))}")
            lines.append(f"Typ: {'EXAKTER TREFFER' if m.get('match_type') == 'exact' else 'Erweiterter Treffer'}")
            lines.append(f"Titel: {m.get('listing_title', '-')}")
            lines.append(f"URL: {m.get('listing_url', '-')}")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("                    ENDE")
        lines.append("=" * 60)
        
        text = "\n".join(lines)
        
        try:
            # Nutze pywebview's create_file_dialog statt tkinter
            window = webview.active_window()
            if window:
                # SAVE_DIALOG = 10 in pywebview
                result = window.create_file_dialog(
                    webview.SAVE_DIALOG,
                    save_filename=f"WohnungsScraper_Bericht_{date_str.replace(':', '-').replace('.', '-').replace(' ', '_')}.txt",
                    file_types=('Textdatei (*.txt)', 'Alle Dateien (*.*)')
                )
                
                if result:
                    filename = result if isinstance(result, str) else result[0]
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(text)
                    return {"success": True, "filename": filename}
                else:
                    return {"success": False, "error": "Abgebrochen"}
            else:
                # Fallback: Speichere im Dokumente-Ordner
                docs_folder = Path.home() / "Documents"
                filename = docs_folder / f"WohnungsScraper_Bericht_{date_str.replace(':', '-').replace('.', '-').replace(' ', '_')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                return {"success": True, "filename": str(filename)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Stats
    def get_stats(self):
        return self.db.get_stats()
    
    # Window Controls
    def open_url(self, url):
        """Oeffnet eine URL im Standard-Browser"""
        try:
            webbrowser.open(url)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def minimize_window(self):
        """Minimiert das Fenster"""
        for window in webview.windows:
            window.minimize()
        return {"success": True}
    
    def close_window(self):
        """Schliesst das Fenster"""
        for window in webview.windows:
            window.destroy()
        return {"success": True}
    
    # Search Methods
    def get_search_status(self):
        elapsed = ""
        if self.start_time:
            delta = datetime.now() - self.start_time
            mins = int(delta.total_seconds() // 60)
            secs = int(delta.total_seconds() % 60)
            elapsed = f"{mins:02d}:{secs:02d}"
        
        return {
            "running": self.search_running,
            "progress": self.search_progress,
            "logs": self.search_logs[:100],
            "matches": len(self.current_matches),
            "elapsed": elapsed
        }
    
    def start_search(self, mode="quick", match_mode="exact", websites=None):
        if self.search_running:
            return {"error": "Suche laeuft bereits"}
        
        if websites is None:
            websites = {"wgGesucht": True, "immoscout": False, "immowelt": True, "kleinanzeigen": True}
        
        self.search_running = True
        self.search_logs = []
        self.current_matches = []
        self.start_time = datetime.now()
        self._completed_pages = 0
        self.search_progress = {
            "current_site": 0, 
            "total_sites": 0, 
            "website": "Initialisiere...", 
            "page": 0, 
            "max_page": 0, 
            "percent": 0, 
            "action": "Starte...", 
            "matches": 0, 
            "listings": 0
        }
        self.selected_websites = websites
        
        thread = threading.Thread(target=self._run_search, args=(mode, match_mode))
        thread.daemon = True
        thread.start()
        
        return {"status": "started"}
    
    def stop_search(self):
        self.search_running = False
        self.log(">>> SUCHE WIRD GESTOPPT...")
        return {"status": "stopping"}
    
    def _run_search(self, mode, match_mode):
        asyncio.run(self._async_search(mode, match_mode))
    
    async def _async_search(self, mode, match_mode):
        scraper = None
        websites = self.selected_websites or {"wgGesucht": True, "immoscout": False, "immowelt": True, "kleinanzeigen": True}
        
        try:
            addresses = self.db.get_addresses()
            if not addresses:
                self.log("!!! FEHLER: Keine Adressen vorhanden!")
                self.search_running = False
                return
            
            city = addresses[0]['city']
            
            # Schnellsuche: 25 Seiten, Vollsuche: 0 = unbegrenzt (alle Seiten)
            self._max_pages = 25 if mode == "quick" else 0
            
            # Zaehle aktive Websites
            active_sites = []
            site_keys = []
            if websites.get('wgGesucht'): 
                active_sites.append("WG-Gesucht.de")
                site_keys.append('wgGesucht')
            if websites.get('immowelt'): 
                active_sites.append("Immowelt.de")
                site_keys.append('immowelt')
            if websites.get('kleinanzeigen'): 
                active_sites.append("Kleinanzeigen.de")
                site_keys.append('kleinanzeigen')
            if websites.get('immoscout'): 
                active_sites.append("ImmobilienScout24.de")
                site_keys.append('immoscout')
            
            total_sites = len(active_sites)
            
            # Berechne Gesamtarbeit (Seiten pro Website)
            # WG-Gesucht: 1x max_pages
            # ImmoScout: 2x max_pages (2 Kategorien)
            # Immowelt: 1x max_pages
            # Kleinanzeigen: 2x max_pages (2 Kategorien)
            self._total_pages_work = 0
            if websites.get('wgGesucht'): self._total_pages_work += self._max_pages
            if websites.get('immoscout'): self._total_pages_work += self._max_pages * 2
            if websites.get('immowelt'): self._total_pages_work += self._max_pages
            if websites.get('kleinanzeigen'): self._total_pages_work += self._max_pages * 2
            
            self._completed_pages = 0
            
            self.search_progress.update({
                "total_sites": total_sites,
                "max_page": self._max_pages
            })
            
            self.log("========================================")
            self.log("     WOHNUNGSSCRAPER - BATCH-SUCHE")
            self.log("========================================")
            self.log(f"")
            self.log(f"# Stadt: {city}")
            self.log(f"# Modus: {'Schnellsuche (25 Seiten)' if mode == 'quick' else 'Vollsuche (alle Seiten)'}")
            self.log(f"# Genauigkeit: {'Exakt (PLZ+Str.+Nr.)' if match_mode == 'exact' else 'Erweitert (PLZ+Str.)'}")
            self.log(f"# Adressen: {len(addresses)}")
            self.log(f"# Aktive Websites: {total_sites}")
            for site in active_sites:
                self.log(f"   - {site}")
            self.log(f"# Geschaetzte Seiten: {self._total_pages_work}")
            self.log("")
            
            if websites.get('kleinanzeigen'):
                self.log("# HINWEIS: Kleinanzeigen-Treffer enthalten oft")
                self.log("#          unvollstaendige Adressen - bitte")
                self.log("#          manuell anhand der Fotos pruefen!")
                self.log("")
            
            report_id = self.db.create_report(len(addresses), active_sites, mode)
            
            # ScrapeOps API-Key (für Immowelt DataDome-Bypass)
            scrapeops_key = os.environ.get('SCRAPEOPS_API_KEY', '65149469-56f3-4b4b-b428-d24ef6206644')
            
            # Scraper mit Stop-Flag und Progress-Callback erstellen
            scraper = BatchScraper(
                log_callback=self.log, 
                max_pages=self._max_pages, 
                match_mode=match_mode,
                stop_flag=self._is_stopped,
                progress_callback=self._update_page_progress,
                scrapeops_api_key=scrapeops_key
            )
            self._scraper = scraper
            
            all_listings = []
            current_site_num = 0
            
            self.log("========== PHASE 1: LISTINGS SAMMELN ==========")
            self.log("")
            
            # WG-Gesucht
            if self.search_running and websites.get('wgGesucht'):
                current_site_num += 1
                self.log(">>> WG-GESUCHT.DE")
                self.search_progress.update({
                    "current_site": current_site_num, 
                    "website": f"WG-Gesucht.de ({current_site_num}/{total_sites})", 
                    "action": "Sammle Listings...",
                    "page": 0
                })
                try:
                    listings = await scraper.collect_wg_gesucht(city)
                    all_listings.extend(listings)
                    self.log(f"  => {len(listings)} Listings gesammelt")
                except Exception as e:
                    self.log(f"  ! Fehler: {str(e)[:50]}")
                self.search_progress["listings"] = len(all_listings)
                self.log("")
            
            # Immowelt (mit ScrapeOps DataDome-Bypass)
            if self.search_running and websites.get('immowelt'):
                current_site_num += 1
                self.log(">>> IMMOWELT.DE (ScrapeOps DataDome-Bypass)")
                self.search_progress.update({
                    "current_site": current_site_num, 
                    "website": f"Immowelt.de ({current_site_num}/{total_sites})", 
                    "action": "Sammle Listings...",
                    "page": 0
                })
                try:
                    # use_proxy_service=True aktiviert ScrapeOps
                    listings = await scraper.collect_immowelt(city, use_proxy_service=True)
                    all_listings.extend(listings)
                    self.log(f"  => {len(listings)} Listings gesammelt")
                except Exception as e:
                    self.log(f"  ! Fehler: {str(e)[:50]}")
                self.search_progress["listings"] = len(all_listings)
                self.log("")
            
            # Kleinanzeigen (mit PLZ-Suche)
            if self.search_running and websites.get('kleinanzeigen'):
                current_site_num += 1
                self.log(">>> KLEINANZEIGEN.DE (nur PLZ-Vergleich)")
                self.search_progress.update({
                    "current_site": current_site_num, 
                    "website": f"Kleinanzeigen.de ({current_site_num}/{total_sites})", 
                    "action": "Sammle Listings...",
                    "page": 0
                })
                try:
                    listings = await scraper.collect_kleinanzeigen(city)
                    all_listings.extend(listings)
                    self.log(f"  => {len(listings)} Listings gesammelt")
                    self.log(f"  ! Diese Treffer muessen manuell geprueft werden!")
                except Exception as e:
                    self.log(f"  ! Fehler: {str(e)[:50]}")
                self.search_progress["listings"] = len(all_listings)
                self.log("")
            
            # ImmoScout (zuletzt, da oft blockiert)
            if self.search_running and websites.get('immoscout'):
                current_site_num += 1
                self.log(">>> IMMOBILIENSCOUT24.DE")
                self.log("    (Bot-Schutz aktiv - moeglicherweise blockiert)")
                self.search_progress.update({
                    "current_site": current_site_num, 
                    "website": f"ImmobilienScout24.de ({current_site_num}/{total_sites})", 
                    "action": "Sammle Listings...",
                    "page": 0
                })
                try:
                    listings = await scraper.collect_immoscout(city)
                    all_listings.extend(listings)
                    if len(listings) == 0:
                        self.log(f"  => 0 Listings (Website blockiert Scraping)")
                    else:
                        self.log(f"  => {len(listings)} Listings gesammelt")
                except Exception as e:
                    self.log(f"  ! Fehler: {str(e)[:50]}")
                self.search_progress["listings"] = len(all_listings)
                self.log("")
            
            # Phase 2: Abgleich (nur wenn nicht gestoppt)
            if self.search_running:
                self.log("========== PHASE 2: ADRESS-ABGLEICH ==========")
                self.log("")
                self.search_progress.update({
                    "percent": 96, 
                    "website": "Adress-Abgleich",
                    "action": f"Vergleiche {len(all_listings)} Listings mit {len(addresses)} Adressen..."
                })
                
                matches = scraper.match_listings(all_listings, addresses)
                
                self.log(f"# Listings insgesamt: {len(all_listings)}")
                self.log(f"# Treffer gefunden: {len(matches)}")
                self.log("")
                
                if matches:
                    self.log("========== GEFUNDENE TREFFER ==========")
                    self.log("")
                    for m in matches:
                        self.db.add_match(
                            report_id, m['address_id'], m['address_display'],
                            m['website'], m['website_name'], m['url'], m['title'], m['match_type']
                        )
                        self.current_matches.append(m)
                        match_label = "EXAKT" if m['match_type'] == 'exact' else "ERWEITERT"
                        self.log(f"  [{match_label}] {m['address_display']}")
                        self.log(f"           -> {m['website_name']}")
                        self.log(f"           -> {m['url'][:60]}...")
                        self.log("")
                    
                    self.search_progress["matches"] = len(matches)
                
                self.db.complete_report(report_id, len(matches), "completed")
                
                self.log("========================================")
                self.log("          SUCHE ABGESCHLOSSEN")
                self.log("========================================")
                self.log(f"# Ergebnis: {len(matches)} Treffer")
            else:
                # Gestoppt
                self.db.complete_report(report_id, len(self.current_matches), "stopped")
                self.log("========================================")
                self.log("          SUCHE GESTOPPT")
                self.log("========================================")
            
        except Exception as e:
            self.log(f"!!! FEHLER: {str(e)}")
        finally:
            if scraper:
                try:
                    await scraper.stop_browser()
                    self.log("# Browser geschlossen")
                except:
                    pass
            self._scraper = None
            self.search_running = False
            self.search_progress["percent"] = 100
            self.search_progress["action"] = "Fertig"
            self.search_progress["website"] = "Abgeschlossen"
