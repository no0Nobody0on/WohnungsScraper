"""
WohnungsScraper - ScrapeOps Integration
Anti-Bot-Bypass via ScrapeOps Proxy Aggregator
Unterstützt DataDome (Immowelt) und andere Bot-Schutz-Systeme
"""

import asyncio
import os
import re
from typing import List, Dict, Callable
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

SCRAPEOPS_AVAILABLE = True


class ScrapeOpsScraper:
    """Scraper mit ScrapeOps Anti-Bot-Bypass für blockierte Websites"""
    
    BASE_URL = "https://proxy.scrapeops.io/v1/"
    
    def __init__(self, api_key: str = None, log_callback: Callable = None):
        self.api_key = api_key or os.environ.get('SCRAPEOPS_API_KEY')
        self.log = log_callback or print
        
        if not self.api_key:
            self.log("  ! ScrapeOps API-Key nicht konfiguriert")
            self.log("    Registrieren: https://scrapeops.io/")
            self.log("    Setze SCRAPEOPS_API_KEY Umgebungsvariable")
        else:
            self.log("  ✓ ScrapeOps initialisiert")
    
    def is_available(self) -> bool:
        """Prüft ob ScrapeOps nutzbar ist"""
        return bool(self.api_key)
    
    def _make_request(self, url: str, bypass: str = None, render_js: bool = True, 
                      country: str = "de") -> str:
        """Macht eine Anfrage über ScrapeOps Proxy"""
        params = {
            'api_key': self.api_key,
            'url': url,
            'render_js': 'true' if render_js else 'false',
            'country': country,
        }
        
        if bypass:
            params['bypass'] = bypass
        
        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=120
            )
            
            if response.status_code == 200:
                return response.text
            else:
                self.log(f"      ! HTTP {response.status_code}")
                return ""
        except Exception as e:
            self.log(f"      ! Request-Fehler: {str(e)[:40]}")
            return ""
    
    async def scrape_immowelt(self, city: str, max_pages: int = 5) -> List[Dict]:
        """Scrapt Immowelt mit ScrapeOps DataDome-Bypass"""
        if not self.is_available():
            return []
        
        listings = []
        seen_urls = set()
        city_slug = self._normalize_city(city)
        base_url = "https://www.immowelt.de"
        
        self.log(f"  ScrapeOps: Immowelt für {city} (DataDome-Bypass)")
        
        page_num = 0
        effective_max = max_pages if max_pages > 0 else 9999  # 0 = unbegrenzt
        
        while page_num < effective_max:
            page_num += 1
            display_max = max_pages if max_pages > 0 else "alle"
            self.log(f"    Seite {page_num}/{display_max}...")
            
            # Immowelt URLs
            if page_num == 1:
                url = f"{base_url}/suche/{city_slug}/wohnungen/mieten"
            else:
                # Die classified-search URL ist normalerweise durch DataDome blockiert
                url = f"{base_url}/classified-search?distributionTypes=Rent&estateTypes=Apartment&locations=AD08DE6345&page={page_num}"
            
            # Anfrage mit DataDome-Bypass
            html = self._make_request(url, bypass="datadome", render_js=True)
            
            if not html or len(html) < 5000:
                self.log(f"      ! Keine oder kurze Antwort")
                if page_num > 1:
                    break
                continue
            
            # Prüfe auf DataDome-Block
            if 'datadome' in html.lower() and 'captcha' in html.lower():
                self.log(f"      ! DataDome-Block trotz Bypass")
                break
            
            # Parse Listings
            new_count = self._parse_listings(html, listings, seen_urls, base_url, 'immowelt')
            self.log(f"      {new_count} neue Listings (Total: {len(listings)})")
            
            if new_count == 0 and page_num > 1:
                break
            
            # Kurze Pause zwischen Anfragen
            await asyncio.sleep(1)
        
        return listings
    
    async def scrape_immoscout(self, city: str, max_pages: int = 5) -> List[Dict]:
        """Scrapt ImmoScout24 mit ScrapeOps (Imperva-Umgehung)"""
        if not self.is_available():
            return []
        
        listings = []
        seen_urls = set()
        city_slug = self._normalize_city(city)
        base_url = "https://www.immobilienscout24.de"
        bundesland = self._get_bundesland(city_slug)
        
        self.log(f"  ScrapeOps: ImmoScout24 für {city}")
        
        page_num = 0
        effective_max = max_pages if max_pages > 0 else 9999  # 0 = unbegrenzt
        
        while page_num < effective_max:
            page_num += 1
            display_max = max_pages if max_pages > 0 else "alle"
            self.log(f"    Seite {page_num}/{display_max}...")
            
            # ImmoScout URLs
            if page_num == 1:
                url = f"{base_url}/Suche/de/{bundesland}/{city_slug}/wohnung-mieten"
            else:
                url = f"{base_url}/Suche/de/{bundesland}/{city_slug}/wohnung-mieten?pagenumber={page_num}"
            
            # Anfrage (kein spezieller Bypass, ScrapeOps versucht automatisch)
            html = self._make_request(url, render_js=True)
            
            if not html or len(html) < 5000:
                self.log(f"      ! Keine oder kurze Antwort")
                if page_num > 1:
                    break
                continue
            
            # Prüfe auf Bot-Erkennung
            if 'Ich bin kein Roboter' in html or 'captcha' in html.lower():
                self.log(f"      ! Bot-Erkennung aktiv")
                break
            
            # Parse Listings
            new_count = self._parse_listings(html, listings, seen_urls, base_url, 'immoscout24')
            self.log(f"      {new_count} neue Listings (Total: {len(listings)})")
            
            if new_count == 0 and page_num > 1:
                break
            
            # Kurze Pause zwischen Anfragen
            await asyncio.sleep(1)
        
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
            print("=" * 70)
            print("SCRAPEOPS ANTI-BOT BYPASS TEST")
            print("=" * 70)
            print()
            print("ScrapeOps bietet:")
            print("  - 1.000 kostenlose API-Aufrufe")
            print("  - DataDome-Bypass (bypass=datadome)")
            print("  - Automatische Proxy-Rotation")
            print("  - JavaScript-Rendering")
            print()
            print("Registrierung:")
            print("  1. https://scrapeops.io/ besuchen")
            print("  2. Kostenlosen Account erstellen")
            print("  3. API-Key aus Dashboard kopieren")
            print()
            print("Nutzung:")
            print(f"  python3 {sys.argv[0]} DEIN_API_KEY")
            return
        
        scraper = ScrapeOpsScraper(api_key=api_key)
        
        if scraper.is_available():
            print("\n--- Immowelt Test (DataDome-Bypass) ---")
            immowelt_listings = await scraper.scrape_immowelt("muenchen", max_pages=2)
            print(f"Immowelt: {len(immowelt_listings)} Listings")
            
            if immowelt_listings:
                print("\nBeispiele:")
                for l in immowelt_listings[:3]:
                    print(f"  - {l['url']}")
            
            print("\n--- ImmoScout24 Test ---")
            immoscout_listings = await scraper.scrape_immoscout("muenchen", max_pages=2)
            print(f"ImmoScout24: {len(immoscout_listings)} Listings")
            
            if immoscout_listings:
                print("\nBeispiele:")
                for l in immoscout_listings[:3]:
                    print(f"  - {l['url']}")
    
    asyncio.run(test())
