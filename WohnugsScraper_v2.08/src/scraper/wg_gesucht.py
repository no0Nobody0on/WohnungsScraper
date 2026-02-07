"""
WohnungsScraper - WG-Gesucht Scraper
"""

import re
import random
import asyncio
from typing import List, Dict
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper, CITY_IDS, PAGE_DELAY_MIN, PAGE_DELAY_MAX, AddressNormalizer


class WGGesuchtScraper(BaseScraper):
    """Scraper für WG-Gesucht.de"""
    
    async def collect(self, city: str) -> List[Dict]:
        """WG-Gesucht: WG-Zimmer + 1-Zimmer + Wohnungen"""
        listings = []
        city_norm = self.normalize_city(city)
        city_id = CITY_IDS.get(city_norm, 0)
        
        if city_id == 0:
            self.log(f"  ! Stadt '{city}' nicht unterstuetzt")
            return listings
        
        base_url = "https://www.wg-gesucht.de"
        
        await self.start_browser()
        page = await self.context.new_page()
        
        try:
            self.log("  Besuche Startseite fuer Cookies...")
            try:
                await page.goto(base_url, wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(2)
                await self._accept_cookies(page)
                await self._human_behavior(page)
            except Exception as e:
                self.log(f"    ! Startseite: {str(e)[:30]}")
            
            empty_pages = 0
            page_num = 0
            effective_max = self.max_pages if self.max_pages > 0 else 9999  # 0 = unbegrenzt
            
            while page_num < effective_max:
                if self.should_stop():
                    self.log("  >>> Suche wird gestoppt...")
                    break
                
                page_num += 1
                display_max = self.max_pages if self.max_pages > 0 else "alle"
                self.report_progress(page_num, effective_max if self.max_pages > 0 else page_num)
                self.log(f"  Seite {page_num}/{display_max}...")
                
                url = f"{base_url}/wg-zimmer-und-1-zimmer-wohnungen-und-wohnungen-in-{city_norm}.{city_id}.0+1+2.1.{page_num - 1}.html"
                self.log(f"    URL: {url[:60]}...")
                
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=25000)
                    await self._human_behavior(page)
                    
                    html = await page.content()
                    
                    if len(html) < 5000:
                        self.log(f"    ! Moeglicherweise blockiert")
                        empty_pages += 1
                        if empty_pages >= 2:
                            break
                        continue
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    items = soup.find_all('div', class_='offer_list_item')
                    
                    if not items:
                        self.log(f"    Keine Inserate auf dieser Seite")
                        empty_pages += 1
                        if empty_pages >= 2:
                            break
                        continue
                    
                    new_count = 0
                    for item in items:
                        text = item.get_text(separator=' ', strip=True)
                        link = item.find('a', href=True)
                        if link:
                            url_full = urljoin(base_url, link['href'])
                            if not any(l['url'] == url_full for l in listings):
                                listings.append({
                                    'text': text,
                                    'text_norm': AddressNormalizer.normalize(text),
                                    'url': url_full,
                                    'website': 'wg-gesucht',
                                    'website_name': 'WG-Gesucht.de'
                                })
                                new_count += 1
                    
                    self.log(f"    {new_count} neue Inserate (Total: {len(listings)})")
                    
                    if new_count == 0:
                        empty_pages += 1
                        if empty_pages >= 2:
                            break
                    else:
                        empty_pages = 0
                    
                except Exception as e:
                    self.log(f"    ! Fehler: {str(e)[:30]}")
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
