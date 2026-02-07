"""
WohnungsScraper - Kleinanzeigen Scraper
Filtert nur Miet-Anzeigen (keine Kaufangebote, keine Gesuche)
"""

import re
import random
import asyncio
from typing import List, Dict
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper, PAGE_DELAY_MIN, PAGE_DELAY_MAX, AddressNormalizer


# Kleinanzeigen Location-IDs
KLEINANZEIGEN_LOCATION_IDS = {
    "muenchen": "6411", "munich": "6411",
    "berlin": "3331", "hamburg": "9409",
    "koeln": "4315", "cologne": "4315",
    "frankfurt": "6581", "stuttgart": "12067",
    "duesseldorf": "3779", "dortmund": "3684",
    "essen": "4272", "leipzig": "8223",
    "bremen": "3563", "dresden": "3741",
    "hannover": "5143", "nuernberg": "9174",
    "duisburg": "3795", "bochum": "3394",
    "wuppertal": "12994", "bielefeld": "3337",
    "bonn": "3444", "muenster": "9120",
    "karlsruhe": "6049", "mannheim": "8409",
    "augsburg": "3171", "wiesbaden": "12874",
    "freiburg": "4631", "kiel": "6194",
    "mainz": "8378",
}

# Begriffe die auf KEINE Miet-Anzeige hinweisen
EXCLUDE_KEYWORDS = [
    'suche', 'suchen', 'gesucht', 'sucht',
    'kaufen', 'verkauf', 'verkaufe', 'zu verkaufen',
    'wohnungstausch', 'tausch', 'tausche',
    'nachmieter gesucht',  # Das ist OK, ist eine Mietanzeige
]

# Begriffe die auf eine Miet-Anzeige hinweisen
INCLUDE_KEYWORDS = [
    'miete', 'mieten', 'vermiete', 'vermieten', 'vermietung',
    'zur miete', 'zu vermieten', 'ab sofort',
    'kaltmiete', 'warmmiete', 'nebenkosten',
    'kaution', 'provision', 'provisionsfrei',
    'zimmer', 'wohnung', 'apartment', 'wg',
    '€', 'euro', 'eur',
]


class KleinanzeigenScraper(BaseScraper):
    """Scraper für Kleinanzeigen.de - nur Miet-Anzeigen"""
    
    def _is_rental_listing(self, text: str) -> bool:
        """Prüft ob es sich um eine Miet-Anzeige handelt"""
        text_lower = text.lower()
        
        # Ausschluss-Check: Ist es eine Suchanzeige oder Kaufanzeige?
        for keyword in EXCLUDE_KEYWORDS:
            # "Nachmieter gesucht" ist OK
            if keyword in text_lower and 'nachmieter' not in text_lower:
                # Aber nur wenn es am Anfang steht (Titel)
                if text_lower.find(keyword) < 100:
                    return False
        
        # Enthält Preis-Indikator (€ oder Zahl mit "miete")?
        has_price = bool(re.search(r'\d+\s*€|\d+\s*euro|€\s*\d+', text_lower))
        has_rent_keyword = any(kw in text_lower for kw in ['miete', 'vermiete', 'vermiet'])
        
        # Mindestens Preis ODER Miet-Keyword muss vorhanden sein
        if has_price or has_rent_keyword:
            return True
        
        # Fallback: Hat es typische Wohnungs-Keywords?
        wohnung_keywords = ['zimmer', 'wohnung', 'apartment', 'qm', 'm²', 'quadratmeter']
        if any(kw in text_lower for kw in wohnung_keywords):
            return True
        
        return False
    
    async def collect(self, city: str) -> List[Dict]:
        """Kleinanzeigen: Nur Mietwohnungen und WG-Zimmer (gefiltert)"""
        listings = []
        city_slug = self.normalize_city(city)
        base_url = "https://www.kleinanzeigen.de"
        
        location_id = KLEINANZEIGEN_LOCATION_IDS.get(city_slug, "")
        location_suffix = f"l{location_id}" if location_id else ""
        
        self.log(f"  Stadt: {city_slug}, Location-ID: {location_id or 'unbekannt'}")
        
        # Verbesserte Kategorie-URLs mit strikteren Filtern
        categories = [
            # Mietwohnungen: Nur Angebote, kein Tausch
            (f"/s-wohnung-mieten/{city_slug}/anzeige:angebote/c203{location_suffix}", "Mietwohnungen"),
            # WG-Zimmer: Nur Angebote
            (f"/s-wg-zimmer-gesucht/{city_slug}/anzeige:angebote/c199{location_suffix}", "WG-Zimmer Angebote"),
        ]
        
        await self.start_browser()
        page = await self.context.new_page()
        
        try:
            self.log("  Besuche Startseite fuer Cookies...")
            try:
                await page.goto(base_url, wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(2)
                await self._accept_cookies(page)
            except Exception as e:
                self.log(f"    ! Startseite: {str(e)[:30]}")
            
            for cat_url, cat_name in categories:
                if self.should_stop():
                    self.log("  >>> Suche wird gestoppt...")
                    break
                
                self.log(f"  Kategorie: {cat_name}")
                empty_pages = 0
                page_num = 0
                effective_max = self.max_pages if self.max_pages > 0 else 9999
                
                while page_num < effective_max:
                    if self.should_stop():
                        self.log("  >>> Suche wird gestoppt...")
                        break
                    
                    page_num += 1
                    display_max = self.max_pages if self.max_pages > 0 else "alle"
                    self.report_progress(page_num, effective_max if self.max_pages > 0 else page_num)
                    self.log(f"    Seite {page_num}/{display_max}...")
                    
                    if page_num == 1:
                        url = f"{base_url}{cat_url}"
                    else:
                        url = f"{base_url}{cat_url}/seite:{page_num}"
                    
                    try:
                        await page.goto(url, wait_until='domcontentloaded', timeout=25000)
                        await self._human_behavior(page)
                        
                        html = await page.content()
                        
                        if len(html) < 5000 or "Cookies" in html[:1000]:
                            self.log(f"      ! Moeglicherweise blockiert")
                            empty_pages += 1
                            if empty_pages >= 2:
                                break
                            continue
                        
                        soup = BeautifulSoup(html, 'html.parser')
                        items = soup.find_all('article', class_='aditem')
                        
                        if not items:
                            items = soup.find_all('li', class_=re.compile(r'ad-listitem'))
                        
                        if not items:
                            self.log(f"      Keine Inserate gefunden")
                            empty_pages += 1
                            if empty_pages >= 2:
                                break
                            continue
                        
                        new_count = 0
                        filtered_count = 0
                        
                        for item in items:
                            text = item.get_text(separator=' ', strip=True)
                            link = item.find('a', href=True)
                            
                            if link:
                                href = link.get('href', '')
                                if '/s-anzeige/' in href:
                                    # Filter: Ist es eine echte Miet-Anzeige?
                                    if not self._is_rental_listing(text):
                                        filtered_count += 1
                                        continue
                                    
                                    url_full = urljoin(base_url, href)
                                    if not any(l['url'] == url_full for l in listings):
                                        listings.append({
                                            'text': text,
                                            'text_norm': AddressNormalizer.normalize(text),
                                            'url': url_full,
                                            'website': 'kleinanzeigen',
                                            'website_name': 'Kleinanzeigen.de'
                                        })
                                        new_count += 1
                        
                        if filtered_count > 0:
                            self.log(f"      {new_count} Miet-Anzeigen, {filtered_count} gefiltert (Total: {len(listings)})")
                        else:
                            self.log(f"      {new_count} neue Inserate (Total: {len(listings)})")
                        
                        if new_count == 0:
                            empty_pages += 1
                            if empty_pages >= 2:
                                break
                        else:
                            empty_pages = 0
                        
                    except Exception as e:
                        self.log(f"      ! Fehler: {str(e)[:30]}")
                        empty_pages += 1
                        if empty_pages >= 2:
                            break
                    
                    await asyncio.sleep(random.uniform(PAGE_DELAY_MIN, PAGE_DELAY_MAX))
        
        finally:
            try:
                await page.close()
            except:
                pass
        
        return listings
