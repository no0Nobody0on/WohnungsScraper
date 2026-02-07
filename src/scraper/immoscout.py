"""
WohnungsScraper - ImmoScout24 Scraper
MIT Chrome Portable + nodriver für bessere Bot-Umgehung
"""

import os
import sys
import re
import random
import asyncio
from pathlib import Path
from typing import List, Dict
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper, BUNDESLAND_MAP, PAGE_DELAY_MIN, PAGE_DELAY_MAX, AddressNormalizer


class ImmoScoutScraper(BaseScraper):
    """Scraper für ImmobilienScout24.de mit erweiterter Bot-Umgehung"""
    
    def _find_chrome_portable(self) -> str:
        """Sucht nach Chrome Portable im App-Verzeichnis"""
        app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent.parent.parent
        
        chrome_paths = [
            app_dir / "chrome-portable" / "App" / "Chrome-bin" / "chrome.exe",
            app_dir / "chrome-portable" / "chrome.exe",
            app_dir / "GoogleChromePortable" / "App" / "Chrome-bin" / "chrome.exe",
            app_dir / "chrome" / "chrome.exe",
        ]
        
        for path in chrome_paths:
            if path.exists():
                self.log(f"  Chrome Portable gefunden: {path.name}")
                return str(path)
        
        return None
    
    async def collect(self, city: str) -> List[Dict]:
        """ImmoScout24: Mietwohnungen + WG mit mehreren Methoden"""
        listings = []
        city_slug = self.normalize_city(city)
        base_url = "https://www.immobilienscout24.de"
        bundesland = BUNDESLAND_MAP.get(city_slug, "bayern")
        
        self.log(f"  Stadt: {city_slug}, Bundesland: {bundesland}")
        
        # Methode 1: Versuche mit nodriver + Chrome Portable
        chrome_path = self._find_chrome_portable()
        if chrome_path:
            self.log("  Methode 1: nodriver + Chrome Portable...")
            try:
                listings = await self._collect_with_nodriver(city_slug, bundesland, chrome_path)
                if listings:
                    self.log(f"  => nodriver erfolgreich: {len(listings)} Listings")
                    return listings
            except Exception as e:
                self.log(f"  ! nodriver Fehler: {str(e)[:50]}")
        else:
            self.log("  ! Chrome Portable nicht gefunden")
            self.log("    Lege 'chrome-portable' Ordner im App-Verzeichnis an")
        
        # Methode 2: Versuche mit curl_cffi (TLS-Spoofing)
        self.log("  Methode 2: curl_cffi (TLS-Fingerprint)...")
        try:
            listings = await self._collect_with_curl(city_slug, bundesland)
            if listings:
                self.log(f"  => curl_cffi erfolgreich: {len(listings)} Listings")
                return listings
        except Exception as e:
            self.log(f"  ! curl_cffi Fehler: {str(e)[:50]}")
        
        # Methode 3: Fallback mit Playwright
        self.log("  Methode 3: Playwright Fallback...")
        try:
            listings = await self._collect_with_playwright(city_slug, bundesland)
        except Exception as e:
            self.log(f"  ! Playwright Fehler: {str(e)[:50]}")
        
        if not listings:
            self.log("  ! ImmoScout24 blockiert - keine Listings gefunden")
            self.log("    Tipp: Chrome Portable im 'chrome-portable' Ordner ablegen")
        
        return listings
    
    async def _collect_with_nodriver(self, city_slug: str, bundesland: str, chrome_path: str) -> List[Dict]:
        """Sammelt Listings mit nodriver (ohne CDP-Spuren)"""
        listings = []
        base_url = "https://www.immobilienscout24.de"
        
        try:
            import nodriver as nd
        except ImportError:
            self.log("    ! nodriver nicht installiert")
            return listings
        
        browser = None
        try:
            # nodriver mit Chrome Portable starten
            browser = await nd.start(
                browser_executable_path=chrome_path,
                headless=False,  # Sichtbar für bessere Erkennung
                lang="de-DE"
            )
            
            # Erst Startseite besuchen
            self.log("    Besuche Startseite...")
            page = await browser.get(base_url)
            await asyncio.sleep(random.uniform(3, 5))
            
            # Scrolle und bewege Maus
            try:
                await page.scroll_down(300)
                await asyncio.sleep(0.5)
            except:
                pass
            
            categories = [
                (f"/Suche/de/{bundesland}/{city_slug}/wohnung-mieten", "Mietwohnungen"),
                (f"/Suche/de/{bundesland}/{city_slug}/wg-zimmer", "WG-Zimmer"),
            ]
            
            for cat_url, cat_name in categories:
                if self.should_stop():
                    break
                
                self.log(f"    Kategorie: {cat_name}")
                empty_pages = 0
                page_num = 0
                effective_max = self.max_pages if self.max_pages > 0 else 9999  # 0 = unbegrenzt
                
                while page_num < effective_max:
                    if self.should_stop():
                        break
                    
                    page_num += 1
                    display_max = self.max_pages if self.max_pages > 0 else "alle"
                    self.report_progress(page_num, effective_max if self.max_pages > 0 else page_num)
                    self.log(f"      Seite {page_num}/{display_max}...")
                    
                    if page_num == 1:
                        url = f"{base_url}{cat_url}"
                    else:
                        url = f"{base_url}{cat_url}?pagenumber={page_num}"
                    
                    try:
                        page = await browser.get(url)
                        await asyncio.sleep(random.uniform(3, 5))
                        
                        # Menschliches Verhalten
                        try:
                            await page.scroll_down(random.randint(200, 400))
                            await asyncio.sleep(0.5)
                        except:
                            pass
                        
                        html = await page.get_content()
                        
                        if "Ich bin kein Roboter" in html or len(html) < 10000:
                            self.log(f"        ! Bot-Erkennung")
                            empty_pages += 1
                            if empty_pages >= 2:
                                break
                            continue
                        
                        # Parse Listings
                        new_count = self._parse_listings(html, listings, base_url)
                        self.log(f"        {new_count} neue (Total: {len(listings)})")
                        
                        if new_count == 0:
                            empty_pages += 1
                            if empty_pages >= 2:
                                break
                        else:
                            empty_pages = 0
                        
                    except Exception as e:
                        self.log(f"        ! Fehler: {str(e)[:30]}")
                        empty_pages += 1
                        if empty_pages >= 2:
                            break
                    
                    await asyncio.sleep(random.uniform(PAGE_DELAY_MIN, PAGE_DELAY_MAX))
        
        finally:
            if browser:
                try:
                    browser.stop()
                except:
                    pass
        
        return listings
    
    async def _collect_with_curl(self, city_slug: str, bundesland: str) -> List[Dict]:
        """Sammelt Listings mit curl_cffi (TLS-Fingerprint-Spoofing)"""
        listings = []
        base_url = "https://www.immobilienscout24.de"
        
        try:
            from curl_cffi import requests as cffi_requests
        except ImportError:
            self.log("    ! curl_cffi nicht installiert")
            return listings
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Session mit Cookies
        session = cffi_requests.Session(impersonate="chrome120")
        
        # Erst Startseite für Cookies
        try:
            session.get(base_url, headers=headers, timeout=30)
            await asyncio.sleep(1)
        except:
            pass
        
        categories = [
            (f"/Suche/de/{bundesland}/{city_slug}/wohnung-mieten", "Mietwohnungen"),
            (f"/Suche/de/{bundesland}/{city_slug}/wg-zimmer", "WG-Zimmer"),
        ]
        
        for cat_url, cat_name in categories:
            if self.should_stop():
                break
            
            self.log(f"    Kategorie: {cat_name}")
            empty_pages = 0
            page_num = 0
            effective_max = self.max_pages if self.max_pages > 0 else 9999  # 0 = unbegrenzt
            
            while page_num < effective_max:
                if self.should_stop():
                    break
                
                page_num += 1
                self.report_progress(page_num, effective_max if self.max_pages > 0 else page_num)
                
                if page_num == 1:
                    url = f"{base_url}{cat_url}"
                else:
                    url = f"{base_url}{cat_url}?pagenumber={page_num}"
                
                try:
                    response = session.get(url, headers=headers, timeout=30)
                    
                    if response.status_code != 200:
                        empty_pages += 1
                        if empty_pages >= 2:
                            break
                        continue
                    
                    html = response.text
                    
                    if "Ich bin kein Roboter" in html or len(html) < 10000:
                        empty_pages += 1
                        if empty_pages >= 2:
                            break
                        continue
                    
                    new_count = self._parse_listings(html, listings, base_url)
                    
                    if new_count == 0:
                        empty_pages += 1
                        if empty_pages >= 2:
                            break
                    else:
                        empty_pages = 0
                    
                except Exception as e:
                    empty_pages += 1
                    if empty_pages >= 2:
                        break
                
                await asyncio.sleep(random.uniform(PAGE_DELAY_MIN, PAGE_DELAY_MAX))
        
        return listings
    
    async def _collect_with_playwright(self, city_slug: str, bundesland: str) -> List[Dict]:
        """Fallback mit Playwright"""
        listings = []
        base_url = "https://www.immobilienscout24.de"
        
        await self.start_browser()
        page = await self.context.new_page()
        
        try:
            # Startseite besuchen
            try:
                await page.goto(base_url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(random.uniform(3, 5))
                await self._accept_cookies(page)
                await self._human_behavior_intense(page)
            except Exception as e:
                self.log(f"    ! Startseite: {str(e)[:30]}")
            
            categories = [
                (f"/Suche/de/{bundesland}/{city_slug}/wohnung-mieten", "Mietwohnungen"),
                (f"/Suche/de/{bundesland}/{city_slug}/wg-zimmer", "WG-Zimmer"),
            ]
            
            for cat_url, cat_name in categories:
                if self.should_stop():
                    break
                
                empty_pages = 0
                page_num = 0
                effective_max = self.max_pages if self.max_pages > 0 else 9999  # 0 = unbegrenzt
                
                while page_num < effective_max:
                    if self.should_stop():
                        break
                    
                    page_num += 1
                    self.report_progress(page_num, effective_max if self.max_pages > 0 else page_num)
                    
                    if page_num == 1:
                        url = f"{base_url}{cat_url}"
                    else:
                        url = f"{base_url}{cat_url}?pagenumber={page_num}"
                    
                    try:
                        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                        await self._human_behavior_intense(page)
                        
                        html = await page.content()
                        
                        if "Ich bin kein Roboter" in html or len(html) < 10000:
                            empty_pages += 1
                            if empty_pages >= 2:
                                break
                            continue
                        
                        new_count = self._parse_listings(html, listings, base_url)
                        
                        if new_count == 0:
                            empty_pages += 1
                            if empty_pages >= 2:
                                break
                        else:
                            empty_pages = 0
                        
                    except Exception as e:
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
    
    def _parse_listings(self, html: str, listings: List[Dict], base_url: str) -> int:
        """Parst HTML und extrahiert Listings"""
        soup = BeautifulSoup(html, 'html.parser')
        expose_links = soup.find_all('a', href=re.compile(r'/expose/\d+'))
        
        if not expose_links:
            return 0
        
        seen_urls = set()
        new_count = 0
        
        for link in expose_links:
            href = link.get('href', '')
            if '/expose/' not in href:
                continue
            
            url_full = urljoin(base_url, href)
            
            if url_full in seen_urls:
                continue
            seen_urls.add(url_full)
            
            if any(l['url'] == url_full for l in listings):
                continue
            
            # Text aus Container extrahieren
            text = ""
            container = link
            for _ in range(5):
                container = container.find_parent()
                if container:
                    text = container.get_text(separator=' ', strip=True)
                    if len(text) > 50:
                        break
            
            if not text:
                text = link.get_text(separator=' ', strip=True)
            
            listings.append({
                'text': text[:500],
                'text_norm': AddressNormalizer.normalize(text[:500]),
                'url': url_full,
                'website': 'immoscout24',
                'website_name': 'ImmobilienScout24.de'
            })
            new_count += 1
        
        return new_count
