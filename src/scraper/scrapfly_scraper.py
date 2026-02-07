"""
WohnungsScraper - Scrapfly Integration
Optionales Modul für Anti-Bot-Bypass via Scrapfly
"""

import asyncio
import os
from typing import List, Dict, Optional, Callable
from bs4 import BeautifulSoup

try:
    from scrapfly import ScrapflyClient, ScrapeConfig
    SCRAPFLY_AVAILABLE = True
except ImportError:
    SCRAPFLY_AVAILABLE = False


class ScrapflyScraper:
    """Scraper mit Scrapfly Anti-Bot-Bypass für blockierte Websites"""
    
    def __init__(self, api_key: str = None, log_callback: Callable = None):
        self.api_key = api_key or os.environ.get('SCRAPFLY_API_KEY')
        self.log = log_callback or print
        self.client = None
        
        if not SCRAPFLY_AVAILABLE:
            self.log("  ! Scrapfly SDK nicht installiert")
            self.log("    pip install scrapfly-sdk[all]")
        elif not self.api_key:
            self.log("  ! Scrapfly API-Key nicht konfiguriert")
            self.log("    Setze SCRAPFLY_API_KEY Umgebungsvariable")
            self.log("    oder übergebe api_key Parameter")
        else:
            self.client = ScrapflyClient(key=self.api_key)
            self.log("  [OK] Scrapfly initialisiert")
    
    def is_available(self) -> bool:
        """Prüft ob Scrapfly nutzbar ist"""
        return self.client is not None
    
    async def scrape_immowelt(self, city: str, max_pages: int = 5) -> List[Dict]:
        """Scrapt Immowelt mit Scrapfly Anti-Bot-Bypass"""
        if not self.is_available():
            return []
        
        listings = []
        seen_urls = set()
        city_slug = self._normalize_city(city)
        base_url = "https://www.immowelt.de"
        
        self.log(f"  Scrapfly: Immowelt für {city}")
        
        for page_num in range(1, max_pages + 1):
            self.log(f"    Seite {page_num}/{max_pages}...")
            
            # Immowelt URL mit Pagination
            if page_num == 1:
                url = f"{base_url}/suche/{city_slug}/wohnungen/mieten"
            else:
                # Versuche die classified-search URL (die normalerweise blockiert ist)
                url = f"{base_url}/classified-search?distributionTypes=Rent&estateTypes=Apartment&locations={city_slug.upper()}&page={page_num}"
            
            try:
                result = await self.client.async_scrape(ScrapeConfig(
                    url=url,
                    asp=True,  # Anti-Scraping Protection
                    render_js=True,
                    country="DE",
                    proxy_pool="public_residential_pool",
                    timeout=60000,
                ))
                
                html = result.scrape_result['content']
                status = result.scrape_result['status_code']
                
                if status != 200:
                    self.log(f"      ! Status {status}")
                    continue
                
                # Parse Listings
                new_count = self._parse_listings(html, listings, seen_urls, base_url, 'immowelt')
                self.log(f"      {new_count} neue Listings (Total: {len(listings)})")
                
                if new_count == 0:
                    break
                    
            except Exception as e:
                self.log(f"      ! Fehler: {str(e)[:50]}")
                break
        
        return listings
    
    async def scrape_immoscout(self, city: str, max_pages: int = 5) -> List[Dict]:
        """Scrapt ImmoScout24 mit Scrapfly Anti-Bot-Bypass"""
        if not self.is_available():
            return []
        
        listings = []
        seen_urls = set()
        city_slug = self._normalize_city(city)
        base_url = "https://www.immobilienscout24.de"
        bundesland = self._get_bundesland(city_slug)
        
        self.log(f"  Scrapfly: ImmoScout24 für {city}")
        
        for page_num in range(1, max_pages + 1):
            self.log(f"    Seite {page_num}/{max_pages}...")
            
            # ImmoScout URL mit Pagination
            if page_num == 1:
                url = f"{base_url}/Suche/de/{bundesland}/{city_slug}/wohnung-mieten"
            else:
                url = f"{base_url}/Suche/de/{bundesland}/{city_slug}/wohnung-mieten?pagenumber={page_num}"
            
            try:
                result = await self.client.async_scrape(ScrapeConfig(
                    url=url,
                    asp=True,  # Anti-Scraping Protection
                    render_js=True,
                    country="DE",
                    proxy_pool="public_residential_pool",
                    timeout=60000,
                ))
                
                html = result.scrape_result['content']
                status = result.scrape_result['status_code']
                
                if status != 200:
                    self.log(f"      ! Status {status}")
                    continue
                
                # Prüfe auf Bot-Erkennung
                if 'Ich bin kein Roboter' in html or len(html) < 10000:
                    self.log(f"      ! Bot-Erkennung trotz Scrapfly")
                    break
                
                # Parse Listings
                new_count = self._parse_listings(html, listings, seen_urls, base_url, 'immoscout24')
                self.log(f"      {new_count} neue Listings (Total: {len(listings)})")
                
                if new_count == 0:
                    break
                    
            except Exception as e:
                self.log(f"      ! Fehler: {str(e)[:50]}")
                break
        
        return listings
    
    def _parse_listings(self, html: str, listings: List[Dict], seen_urls: set, 
                       base_url: str, website: str) -> int:
        """Parst HTML und extrahiert Listings"""
        soup = BeautifulSoup(html, 'html.parser')
        new_count = 0
        
        # Finde alle Expose-Links
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if '/expose/' not in href:
                continue
            
            # URL normalisieren
            if href.startswith('http'):
                url_full = href.split('?')[0]
            elif href.startswith('/'):
                url_full = base_url + href.split('?')[0]
            else:
                continue
            
            if url_full in seen_urls:
                continue
            seen_urls.add(url_full)
            
            # Text extrahieren
            text = ""
            container = a
            for _ in range(10):
                container = container.find_parent()
                if not container:
                    break
                text = container.get_text(separator=' ', strip=True)
                if 100 < len(text) < 3000:
                    break
            
            if not text or len(text) < 50:
                text = a.get_text(separator=' ', strip=True)
            
            if text and len(text) > 20:
                listings.append({
                    'text': text[:500],
                    'text_norm': self._normalize_text(text[:500]),
                    'url': url_full,
                    'website': website,
                    'website_name': 'Immowelt.de' if website == 'immowelt' else 'ImmobilienScout24.de'
                })
                new_count += 1
        
        return new_count
    
    @staticmethod
    def _normalize_city(city: str) -> str:
        """Normalisiert Stadtnamen"""
        return city.lower().replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe').replace('ß', 'ss').replace(' ', '-')
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalisiert Text für Adressabgleich"""
        import re
        text = text.lower()
        text = text.replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe').replace('ß', 'ss')
        text = text.replace('str.', 'strasse').replace('straße', 'strasse')
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def _get_bundesland(city_slug: str) -> str:
        """Gibt das Bundesland für eine Stadt zurück"""
        bundesland_map = {
            "muenchen": "bayern", "nuernberg": "bayern", "augsburg": "bayern",
            "berlin": "berlin", "hamburg": "hamburg",
            "koeln": "nordrhein-westfalen", "duesseldorf": "nordrhein-westfalen",
            "frankfurt": "hessen", "stuttgart": "baden-wuerttemberg",
            "hannover": "niedersachsen", "bremen": "bremen",
            "leipzig": "sachsen", "dresden": "sachsen",
        }
        return bundesland_map.get(city_slug, "bayern")


# Standalone Test
if __name__ == "__main__":
    import sys
    
    async def test():
        api_key = sys.argv[1] if len(sys.argv) > 1 else None
        
        if not api_key:
            print("Nutzung: python3 scrapfly_scraper.py DEIN_API_KEY")
            return
        
        scraper = ScrapflyScraper(api_key=api_key)
        
        if scraper.is_available():
            print("\n--- Immowelt Test ---")
            immowelt_listings = await scraper.scrape_immowelt("muenchen", max_pages=2)
            print(f"Immowelt: {len(immowelt_listings)} Listings")
            
            print("\n--- ImmoScout24 Test ---")
            immoscout_listings = await scraper.scrape_immoscout("muenchen", max_pages=2)
            print(f"ImmoScout24: {len(immoscout_listings)} Listings")
    
    asyncio.run(test())
