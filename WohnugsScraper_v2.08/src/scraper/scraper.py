"""
WohnungsScraper - Batch Scraper Module
Modulare Struktur mit separaten Scrapern pro Website
Optional: Scrapfly oder ScrapeOps für Anti-Bot-Bypass
"""

import os
import re
from typing import List, Dict, Callable, Optional

from .base import BaseScraper, AddressNormalizer
from .wg_gesucht import WGGesuchtScraper
from .immoscout import ImmoScoutScraper
from .immowelt import ImmoweltScraper
from .kleinanzeigen import KleinanzeigenScraper

# Optional: Scrapfly für blockierte Websites
try:
    from .scrapfly_scraper import ScrapflyScraper, SCRAPFLY_AVAILABLE
except ImportError:
    SCRAPFLY_AVAILABLE = False
    ScrapflyScraper = None

# Optional: ScrapeOps für blockierte Websites
try:
    from .scrapeops_scraper import ScrapeOpsScraper, SCRAPEOPS_AVAILABLE
except ImportError:
    SCRAPEOPS_AVAILABLE = False
    ScrapeOpsScraper = None


class BatchScraper(BaseScraper):
    """Haupt-Scraper der alle Website-Scraper koordiniert"""
    
    def __init__(self, log_callback: Callable = None, max_pages: int = 5, 
                 match_mode: str = "exact", stop_flag: Callable = None,
                 progress_callback: Callable = None, 
                 scrapfly_api_key: str = None,
                 scrapeops_api_key: str = None):
        super().__init__(log_callback, max_pages, match_mode, stop_flag, progress_callback)
        
        # Initialisiere einzelne Scraper
        self.wg_gesucht = WGGesuchtScraper(log_callback, max_pages, match_mode, stop_flag, progress_callback)
        self.immoscout = ImmoScoutScraper(log_callback, max_pages, match_mode, stop_flag, progress_callback)
        self.immowelt = ImmoweltScraper(log_callback, max_pages, match_mode, stop_flag, progress_callback)
        self.kleinanzeigen = KleinanzeigenScraper(log_callback, max_pages, match_mode, stop_flag, progress_callback)
        
        # Optional: Scrapfly für blockierte Websites
        self.scrapfly = None
        self.scrapfly_api_key = scrapfly_api_key or os.environ.get('SCRAPFLY_API_KEY')
        
        if SCRAPFLY_AVAILABLE and self.scrapfly_api_key:
            self.scrapfly = ScrapflyScraper(api_key=self.scrapfly_api_key, log_callback=log_callback)
            if self.scrapfly.is_available():
                self.log("# Scrapfly Anti-Bot-Bypass aktiviert")
        
        # Optional: ScrapeOps für blockierte Websites
        self.scrapeops = None
        self.scrapeops_api_key = scrapeops_api_key or os.environ.get('SCRAPEOPS_API_KEY')
        
        if SCRAPEOPS_AVAILABLE and self.scrapeops_api_key:
            self.scrapeops = ScrapeOpsScraper(api_key=self.scrapeops_api_key, log_callback=log_callback)
            if self.scrapeops.is_available():
                self.log("# ScrapeOps Anti-Bot-Bypass aktiviert")
    
    def has_scrapfly(self) -> bool:
        """Prüft ob Scrapfly verfügbar ist"""
        return self.scrapfly is not None and self.scrapfly.is_available()
    
    def has_scrapeops(self) -> bool:
        """Prüft ob ScrapeOps verfügbar ist"""
        return self.scrapeops is not None and self.scrapeops.is_available()
    
    def has_proxy_service(self) -> bool:
        """Prüft ob irgendein Proxy-Service verfügbar ist"""
        return self.has_scrapfly() or self.has_scrapeops()
    
    async def collect_wg_gesucht(self, city: str) -> List[Dict]:
        """WG-Gesucht Scraping"""
        return await self.wg_gesucht.collect(city)
    
    async def collect_immoscout(self, city: str, use_proxy_service: bool = False) -> List[Dict]:
        """ImmoScout24 Scraping - mit optionalem Proxy-Service Fallback"""
        if use_proxy_service:
            if self.has_scrapeops():
                self.log("# ImmoScout24: Verwende ScrapeOps")
                return await self.scrapeops.scrape_immoscout(city, self.max_pages)
            elif self.has_scrapfly():
                self.log("# ImmoScout24: Verwende Scrapfly Anti-Bot-Bypass")
                return await self.scrapfly.scrape_immoscout(city, self.max_pages)
        return await self.immoscout.collect(city)
    
    async def collect_immowelt(self, city: str, use_proxy_service: bool = False) -> List[Dict]:
        """Immowelt Scraping - mit optionalem Proxy-Service Fallback"""
        if use_proxy_service:
            if self.has_scrapeops():
                self.log("# Immowelt: Verwende ScrapeOps DataDome-Bypass")
                return await self.scrapeops.scrape_immowelt(city, self.max_pages)
            elif self.has_scrapfly():
                self.log("# Immowelt: Verwende Scrapfly Anti-Bot-Bypass")
                return await self.scrapfly.scrape_immowelt(city, self.max_pages)
        return await self.immowelt.collect(city)
    
    async def collect_kleinanzeigen(self, city: str) -> List[Dict]:
        """Kleinanzeigen Scraping"""
        return await self.kleinanzeigen.collect(city)
    
    def match_listings(self, listings: List[Dict], addresses: List[Dict]) -> List[Dict]:
        """Vergleicht Listings mit Adressen
        
        Exakte Suche: PLZ + Straße + Hausnummer müssen alle übereinstimmen
        Erweiterte Suche: PLZ + Straße müssen übereinstimmen (ohne Hausnummer)
        """
        matches = []
        
        for addr in addresses:
            street_variants = AddressNormalizer.get_street_variants(addr['street'])
            house_variants = AddressNormalizer.get_house_variants(addr['house_number'])
            plz = addr.get('postal_code', '')
            
            address_display = f"{addr['street']} {addr['house_number']}, {plz} {addr['city']}"
            
            for listing in listings:
                text_norm = listing['text_norm']
                text_raw = listing['text']
                
                # 1. PLZ suchen (PFLICHT für beide Modi)
                plz_found = plz and plz in text_raw
                if not plz_found:
                    continue
                
                # 2. Straße suchen (PFLICHT für beide Modi)
                street_found = False
                for sv in street_variants:
                    if sv in text_norm:
                        street_found = True
                        break
                
                if not street_found:
                    continue
                
                # 3. Hausnummer suchen (nur für exakte Suche PFLICHT)
                house_found = False
                for hv in house_variants:
                    pattern = r'\b' + re.escape(hv) + r'\b'
                    if re.search(pattern, text_norm):
                        house_found = True
                        break
                
                # Match-Typ bestimmen
                if plz_found and street_found and house_found:
                    match_type = "exact"
                elif plz_found and street_found:
                    match_type = "extended"
                else:
                    continue  # Sollte nicht erreicht werden
                
                # Filter nach Match-Mode
                # Exakte Suche: Nur wenn PLZ + Straße + Hausnummer
                if self.match_mode == "exact" and match_type != "exact":
                    continue
                
                # Erweiterte Suche: PLZ + Straße reicht (mit oder ohne Hausnummer)
                # (match_type "extended" oder "exact" sind beide OK)
                
                # Duplikate vermeiden
                if not any(m['url'] == listing['url'] and m['address_id'] == addr['id'] for m in matches):
                    matches.append({
                        'address_id': addr['id'],
                        'address_display': address_display,
                        'url': listing['url'],
                        'title': listing['text'][:120],
                        'website': listing['website'],
                        'website_name': listing['website_name'],
                        'match_type': match_type
                    })
        
        return matches
    
    async def stop_all(self):
        """Stoppt alle Browser-Instanzen"""
        await self.stop_browser()
        await self.wg_gesucht.stop_browser()
        await self.immoscout.stop_browser()
        await self.immowelt.stop_browser()
        await self.kleinanzeigen.stop_browser()
