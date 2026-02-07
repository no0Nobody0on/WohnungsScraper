"""
WohnungsScraper - Immowelt Scraper
Immowelt ist eine SPA mit DataDome-geschützter Pagination.
Diese Version maximiert die Ergebnisse von der ersten Seite und 
durchsucht mehrere Kategorien.
"""

import re
import random
import asyncio
from typing import List, Dict, Set

from bs4 import BeautifulSoup

from .base import BaseScraper, PAGE_DELAY_MIN, PAGE_DELAY_MAX, AddressNormalizer


class ImmoweltScraper(BaseScraper):
    """Scraper für Immowelt.de - optimiert für SPA mit Bot-Schutz"""
    
    async def collect(self, city: str) -> List[Dict]:
        """Immowelt: Durchsucht mehrere Kategorien um Listings zu sammeln"""
        listings = []
        seen_urls: Set[str] = set()
        city_slug = self.normalize_city(city)
        base_url = "https://www.immowelt.de"
        
        self.log(f"  Stadt-Slug: {city_slug}")
        
        # Verschiedene Kategorien durchsuchen
        categories = [
            (f"{base_url}/suche/{city_slug}/wohnungen/mieten", "Mietwohnungen"),
            (f"{base_url}/suche/{city_slug}/wg-zimmer/mieten", "WG-Zimmer"),
        ]
        
        await self.start_browser()
        page = await self.context.new_page()
        
        try:
            # Startseite für Cookies
            self.log("  Besuche Startseite fuer Cookies...")
            try:
                await page.goto(base_url, wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(2)
                await self._accept_cookies(page)
                await self._human_behavior(page)
            except Exception as e:
                self.log(f"    ! Startseite: {str(e)[:30]}")
            
            total_categories = len(categories)
            
            for cat_idx, (search_url, cat_name) in enumerate(categories, 1):
                if self.should_stop():
                    self.log("  >>> Suche wird gestoppt...")
                    break
                
                self.report_progress(cat_idx, total_categories)
                self.log(f"  Kategorie: {cat_name}")
                
                try:
                    await page.goto(search_url, wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(3)
                    await self._accept_cookies(page)
                except Exception as e:
                    self.log(f"    ! Suchseite: {str(e)[:30]}")
                    continue
                
                # Intensive Scrollen um alle Lazy-Loaded Elemente zu laden
                await self._intensive_scroll(page)
                
                # Extrahiere Listings
                new_count = await self._extract_listings(page, listings, seen_urls, base_url)
                self.log(f"    {new_count} neue Inserate (Total: {len(listings)})")
                
                # Kurze Pause zwischen Kategorien
                await asyncio.sleep(random.uniform(PAGE_DELAY_MIN, PAGE_DELAY_MAX))
            
            self.log(f"  Gesamtergebnis: {len(listings)} Inserate")
            
            # Hinweis zur Limitierung
            if len(listings) < 60:
                self.log("  Hinweis: Immowelt limitiert Ergebnisse (Bot-Schutz)")
                self.log("    Paginierung ist durch DataDome blockiert")
        
        except Exception as e:
            self.log(f"  ! Fehler: {str(e)[:50]}")
        finally:
            try:
                await page.close()
            except:
                pass
        
        return listings
    
    async def _intensive_scroll(self, page):
        """Intensives Scrollen um alle Lazy-Loaded Elemente zu laden"""
        try:
            # Entferne Cookie-Banner
            await self._remove_overlays(page)
            
            # Viewport-Höhe ermitteln
            viewport_height = await page.evaluate('window.innerHeight')
            total_height = await page.evaluate('document.body.scrollHeight')
            
            # Schrittweise scrollen
            current_position = 0
            scroll_step = viewport_height - 100
            
            while current_position < total_height:
                current_position += scroll_step
                await page.evaluate(f'window.scrollTo(0, {current_position})')
                await asyncio.sleep(random.uniform(0.3, 0.6))
                
                # Aktualisiere Total-Höhe (kann sich durch Lazy-Loading ändern)
                total_height = await page.evaluate('document.body.scrollHeight')
                
                # Menschliches Verhalten
                if random.random() < 0.3:
                    await self._human_behavior(page)
            
            # Zurück nach oben
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(0.5)
            
        except:
            pass
    
    async def _extract_listings(self, page, listings: List[Dict], seen_urls: Set[str], base_url: str) -> int:
        """Extrahiert Listings von der aktuellen Seite"""
        html = await page.content()
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
            
            # Duplikate pruefen
            if url_full in seen_urls:
                continue
            seen_urls.add(url_full)
            
            # Text aus Container extrahieren
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
                    'text_norm': AddressNormalizer.normalize(text[:500]),
                    'url': url_full,
                    'website': 'immowelt',
                    'website_name': 'Immowelt.de'
                })
                new_count += 1
        
        return new_count
    
    async def _remove_overlays(self, page):
        """Entfernt Cookie-Banner und andere Overlays"""
        try:
            await page.evaluate('''
                // Entferne Usercentrics
                const uc = document.getElementById('usercentrics-root');
                if (uc) uc.remove();
                
                // Entferne andere bekannte Overlays
                const overlays = document.querySelectorAll('[class*="overlay"], [class*="modal"], [class*="consent"], [class*="cookie"]');
                overlays.forEach(el => {
                    if (el.style.position === 'fixed' || el.style.position === 'absolute') {
                        el.remove();
                    }
                });
            ''')
        except:
            pass
