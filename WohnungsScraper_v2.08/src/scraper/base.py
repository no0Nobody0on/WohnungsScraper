"""
WohnungsScraper - Base Scraper Module
Gemeinsame Funktionen für alle Scraper
"""

import os
import sys
import random
import asyncio
from pathlib import Path
from typing import List, Dict, Callable

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from .normalizer import AddressNormalizer


# Konstanten
PAGE_DELAY_MIN = 1.0
PAGE_DELAY_MAX = 2.5

# Stadt-IDs für WG-Gesucht
CITY_IDS = {
    "berlin": 8, "muenchen": 90, "munich": 90, "hamburg": 55,
    "koeln": 73, "cologne": 73, "frankfurt": 41, "stuttgart": 124,
    "duesseldorf": 30, "dortmund": 26, "essen": 33, "leipzig": 77,
    "bremen": 17, "dresden": 27, "hannover": 57, "nuernberg": 96,
    "bonn": 13, "mannheim": 84, "karlsruhe": 69, "wiesbaden": 141,
    "augsburg": 2, "aachen": 1, "braunschweig": 16, "kiel": 70,
    "chemnitz": 19, "halle": 56, "magdeburg": 83, "freiburg": 42,
    "luebeck": 80, "erfurt": 32, "rostock": 109, "mainz": 82,
    "kassel": 68, "saarbruecken": 111, "potsdam": 104, "oldenburg": 99,
}

# Bundesland-Mapping
BUNDESLAND_MAP = {
    "muenchen": "bayern", "munich": "bayern", "nuernberg": "bayern", "augsburg": "bayern",
    "berlin": "berlin", "hamburg": "hamburg",
    "koeln": "nordrhein-westfalen", "duesseldorf": "nordrhein-westfalen", 
    "dortmund": "nordrhein-westfalen", "essen": "nordrhein-westfalen",
    "frankfurt": "hessen", "wiesbaden": "hessen",
    "stuttgart": "baden-wuerttemberg", "mannheim": "baden-wuerttemberg", 
    "hannover": "niedersachsen", "bremen": "bremen",
    "leipzig": "sachsen", "dresden": "sachsen",
    "kiel": "schleswig-holstein", "mainz": "rheinland-pfalz",
}

# Fingerprint-Spoofing Script
STEALTH_SCRIPT = """
// WEBDRIVER ENTFERNEN
delete Object.getPrototypeOf(navigator).webdriver;
Object.defineProperty(navigator, 'webdriver', { get: () => false, configurable: true });

// Automation-Marker entfernen
delete document.WEBDRIVER_TESTING;
delete window.WEBDRIVER_TESTING;
delete window.callPhantom;
delete window._phantom;
delete window.phantom;
delete window.__nightmare;
delete window.domAutomation;
delete window.domAutomationController;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

// NAVIGATOR PROPERTIES
Object.defineProperty(navigator, 'platform', { get: () => 'Win32', configurable: true });
Object.defineProperty(navigator, 'languages', { get: () => Object.freeze(['de-DE', 'de', 'en-US', 'en']), configurable: true });
Object.defineProperty(navigator, 'language', { get: () => 'de-DE', configurable: true });
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8, configurable: true });
Object.defineProperty(navigator, 'deviceMemory', { get: () => 8, configurable: true });
Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 0, configurable: true });
Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.', configurable: true });
Object.defineProperty(navigator, 'appVersion', { get: () => '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', configurable: true });

// Connection API
if (navigator.connection === undefined) {
    Object.defineProperty(navigator, 'connection', {
        get: () => ({ effectiveType: '4g', rtt: 50, downlink: 10, saveData: false }),
        configurable: true
    });
}

// PLUGINS & MIME TYPES
const createPlugin = (name, description, filename) => {
    const plugin = Object.create(Plugin.prototype);
    Object.defineProperties(plugin, {
        name: { value: name, enumerable: true },
        description: { value: description, enumerable: true },
        filename: { value: filename, enumerable: true },
        length: { value: 1, enumerable: true }
    });
    return plugin;
};

const createMimeType = (type, suffixes, description, plugin) => {
    const mimeType = Object.create(MimeType.prototype);
    Object.defineProperties(mimeType, {
        type: { value: type, enumerable: true },
        suffixes: { value: suffixes, enumerable: true },
        description: { value: description, enumerable: true },
        enabledPlugin: { value: plugin, enumerable: true }
    });
    return mimeType;
};

const pdfPlugin = createPlugin('Chrome PDF Plugin', 'Portable Document Format', 'internal-pdf-viewer');
const pdfViewerPlugin = createPlugin('Chrome PDF Viewer', '', 'mhjfbmdgcfjbbpaeojofohoefgiehjai');
const naclPlugin = createPlugin('Native Client', '', 'internal-nacl-plugin');
const pdfMimeType = createMimeType('application/pdf', 'pdf', 'Portable Document Format', pdfPlugin);
const pdfxMimeType = createMimeType('application/x-pdf', 'pdf', '', pdfPlugin);

const pluginArray = Object.create(PluginArray.prototype);
pluginArray[0] = pdfPlugin;
pluginArray[1] = pdfViewerPlugin;
pluginArray[2] = naclPlugin;
Object.defineProperties(pluginArray, {
    length: { value: 3, enumerable: true },
    item: { value: (i) => pluginArray[i] || null },
    namedItem: { value: (n) => [pdfPlugin, pdfViewerPlugin, naclPlugin].find(p => p.name === n) || null },
    refresh: { value: () => {} }
});

const mimeTypeArray = Object.create(MimeTypeArray.prototype);
mimeTypeArray[0] = pdfMimeType;
mimeTypeArray[1] = pdfxMimeType;
Object.defineProperties(mimeTypeArray, {
    length: { value: 2, enumerable: true },
    item: { value: (i) => mimeTypeArray[i] || null },
    namedItem: { value: (n) => [pdfMimeType, pdfxMimeType].find(m => m.type === n) || null }
});

Object.defineProperty(navigator, 'plugins', { get: () => pluginArray, configurable: true });
Object.defineProperty(navigator, 'mimeTypes', { get: () => mimeTypeArray, configurable: true });

// CHROME OBJECT
window.chrome = {
    app: { isInstalled: false, InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }, RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }, getDetails: () => null, getIsInstalled: () => false, runningState: () => 'cannot_run' },
    csi: () => {},
    loadTimes: () => ({ commitLoadTime: Date.now() / 1000, connectionInfo: 'http/1.1', finishDocumentLoadTime: Date.now() / 1000, finishLoadTime: Date.now() / 1000, firstPaintAfterLoadTime: 0, firstPaintTime: Date.now() / 1000, navigationType: 'Navigate', npnNegotiatedProtocol: 'unknown', requestTime: Date.now() / 1000, startLoadTime: Date.now() / 1000, wasAlternateProtocolAvailable: false, wasFetchedViaSpdy: false, wasNpnNegotiated: false }),
    runtime: { OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install' }, connect: () => {}, sendMessage: () => {} }
};

// WEBGL SPOOFING
const getParameterProxyHandler = {
    apply: function(target, thisArg, args) {
        const param = args[0];
        if (param === 37445) return 'Intel Inc.';
        if (param === 37446) return 'Intel(R) UHD Graphics 630';
        if (param === 7936) return 'WebKit';
        if (param === 7937) return 'WebKit WebGL';
        if (param === 7938) return 'WebGL 1.0 (OpenGL ES 2.0 Chromium)';
        return Reflect.apply(target, thisArg, args);
    }
};

const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = new Proxy(originalGetParameter, getParameterProxyHandler);

if (typeof WebGL2RenderingContext !== 'undefined') {
    const originalGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
    WebGL2RenderingContext.prototype.getParameter = new Proxy(originalGetParameter2, getParameterProxyHandler);
}

// CANVAS SPOOFING
const addCanvasNoise = (imageData) => {
    const data = imageData.data;
    const seed = 12345;
    for (let i = 0; i < data.length; i += 4) {
        const noise = ((seed * (i + 1)) % 3) - 1;
        data[i] = Math.max(0, Math.min(255, data[i] + noise));
    }
    return imageData;
};

const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
CanvasRenderingContext2D.prototype.getImageData = function() {
    const imageData = originalGetImageData.apply(this, arguments);
    return addCanvasNoise(imageData);
};

// WEBRTC LEAK PREVENTION
const originalRTCPeerConnection = window.RTCPeerConnection || window.webkitRTCPeerConnection;
if (originalRTCPeerConnection) {
    window.RTCPeerConnection = function(config) {
        if (config && config.iceServers) config.iceServers = [];
        return new originalRTCPeerConnection(config);
    };
    window.RTCPeerConnection.prototype = originalRTCPeerConnection.prototype;
}

// PERMISSIONS API
const originalQuery = navigator.permissions?.query;
if (originalQuery) {
    navigator.permissions.query = function(parameters) {
        if (parameters.name === 'notifications') return Promise.resolve({ state: 'default', onchange: null });
        if (parameters.name === 'push') return Promise.resolve({ state: 'denied', onchange: null });
        return originalQuery.apply(this, arguments);
    };
}

// SCREEN PROPERTIES
Object.defineProperty(screen, 'width', { get: () => 1920, configurable: true });
Object.defineProperty(screen, 'height', { get: () => 1080, configurable: true });
Object.defineProperty(screen, 'availWidth', { get: () => 1920, configurable: true });
Object.defineProperty(screen, 'availHeight', { get: () => 1040, configurable: true });
Object.defineProperty(screen, 'colorDepth', { get: () => 24, configurable: true });
Object.defineProperty(screen, 'pixelDepth', { get: () => 24, configurable: true });
Object.defineProperty(window, 'outerWidth', { get: () => 1920, configurable: true });
Object.defineProperty(window, 'outerHeight', { get: () => 1080, configurable: true });
Object.defineProperty(window, 'devicePixelRatio', { get: () => 1, configurable: true });

// MEDIA DEVICES
if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
    navigator.mediaDevices.enumerateDevices = function() {
        return Promise.resolve([
            { deviceId: 'default', kind: 'audioinput', label: '', groupId: 'default' },
            { deviceId: 'default', kind: 'audiooutput', label: '', groupId: 'default' },
            { deviceId: 'default', kind: 'videoinput', label: '', groupId: 'default' }
        ]);
    };
}

// BATTERY API
if (navigator.getBattery) {
    navigator.getBattery = function() {
        return Promise.resolve({ charging: true, chargingTime: 0, dischargingTime: Infinity, level: 1, addEventListener: () => {}, removeEventListener: () => {} });
    };
}

console.log('[Stealth] Fingerprint spoofing aktiviert');
"""


class BaseScraper:
    """Basis-Klasse für alle Scraper mit gemeinsamen Funktionen"""
    
    def __init__(self, log_callback: Callable = None, max_pages: int = 5, 
                 match_mode: str = "exact", stop_flag: Callable = None, 
                 progress_callback: Callable = None):
        self.log = log_callback or print
        self.max_pages = max_pages
        self.match_mode = match_mode
        self.stop_flag = stop_flag
        self.progress_callback = progress_callback
        self.browser = None
        self.context = None
        self.playwright = None
    
    def should_stop(self) -> bool:
        """Prüft ob die Suche gestoppt werden soll"""
        if self.stop_flag and callable(self.stop_flag):
            return self.stop_flag()
        return False
    
    def report_progress(self, page: int, max_page: int):
        """Meldet Seitenfortschritt"""
        if self.progress_callback and callable(self.progress_callback):
            self.progress_callback(page, max_page)
    
    def _find_chrome_portable(self) -> str:
        """Sucht nach Chrome Portable im App-Verzeichnis"""
        app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent.parent.parent
        
        # Chrome Portable Pfade
        chrome_paths = [
            app_dir / "chrome-portable" / "App" / "Chrome-bin" / "chrome.exe",
            app_dir / "chrome-portable" / "chrome.exe",
            app_dir / "GoogleChromePortable" / "App" / "Chrome-bin" / "chrome.exe",
        ]
        
        for path in chrome_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def _find_browser(self) -> str:
        """Sucht nach einem Browser (Chrome Portable > Playwright > System Chrome)"""
        app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent.parent.parent
        
        possible_paths = []
        
        # 1. Chrome Portable im App-Verzeichnis
        chrome_portable = self._find_chrome_portable()
        if chrome_portable:
            return chrome_portable
        
        # 2. Playwright-Browser
        for browsers_dir in [app_dir / "playwright-browsers", app_dir]:
            if browsers_dir.exists():
                for exe in browsers_dir.rglob("chrome.exe"):
                    possible_paths.append(exe)
                for exe in browsers_dir.rglob("chrome-headless-shell.exe"):
                    possible_paths.append(exe)
        
        # 3. MS-Playwright im LOCALAPPDATA
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            ms_pw = Path(local_app_data) / "ms-playwright"
            if ms_pw.exists():
                for exe in ms_pw.rglob("chrome.exe"):
                    possible_paths.append(exe)
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    async def start_browser(self):
        """Startet den Playwright-Browser mit Stealth-Einstellungen"""
        if self.browser:
            return
        
        self.log("# Browser wird gestartet...")
        self.playwright = await async_playwright().start()
        
        browser_exe = self._find_browser()
        if browser_exe:
            self.log(f"# Browser: {Path(browser_exe).name}")
        
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-size=1920,1080',
            '--start-maximized',
        ]
        
        # Browser immer versteckt (headless)
        use_headless = True
        
        if browser_exe:
            self.browser = await self.playwright.chromium.launch(
                headless=use_headless, 
                executable_path=browser_exe,
                args=browser_args
            )
        else:
            self.browser = await self.playwright.chromium.launch(
                headless=use_headless,
                args=browser_args
            )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            locale='de-DE',
            timezone_id='Europe/Berlin',
            java_script_enabled=True,
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
        )
        
        await self.context.add_init_script(STEALTH_SCRIPT)
    
    async def stop_browser(self):
        """Stoppt den Browser"""
        if self.context:
            try:
                await self.context.close()
            except:
                pass
            self.context = None
        
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
            self.browser = None
        
        if self.playwright:
            try:
                await self.playwright.stop()
            except:
                pass
            self.playwright = None
    
    async def _accept_cookies(self, page) -> bool:
        """Versucht Cookie-Banner zu akzeptieren"""
        cookie_selectors = [
            # Usercentrics (Immowelt, etc.)
            '#usercentrics-root button[data-testid="uc-accept-all-button"]',
            '[data-testid="uc-accept-all-button"]',
            '#uc-btn-accept-banner',
            'button[data-testid*="accept"]',
            # Standard-Selektoren
            'button[id*="accept"]', 'button[class*="accept"]',
            'button[id*="consent"]', 'button[class*="consent"]',
            'button[id*="agree"]', 'button[class*="agree"]',
            'button:has-text("Akzeptieren")', 'button:has-text("Alle akzeptieren")',
            'button:has-text("Accept")', 'button:has-text("Accept all")',
            'button:has-text("Zustimmen")', 'button:has-text("Einverstanden")',
            'a:has-text("Akzeptieren")', 'a:has-text("Zustimmen")',
            '#cmpbntyestxt', '#acceptAllButton', '.cmpboxbtnyes',
            'button.sp_choice_type_11', 'button[title*="accept"]',
            '#onetrust-accept-btn-handler', '.onetrust-accept-btn',
            '#didomi-notice-agree-button', '.didomi-accept-button',
            '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
        ]
        
        for selector in cookie_selectors:
            try:
                btn = await page.wait_for_selector(selector, timeout=1000)
                if btn:
                    await btn.click(force=True)
                    self.log("    Cookie-Banner akzeptiert")
                    await asyncio.sleep(0.5)
                    return True
            except:
                continue
        
        # Fallback: Entferne Usercentrics-Overlay via JavaScript
        try:
            await page.evaluate('''
                const uc = document.getElementById('usercentrics-root');
                if (uc) uc.remove();
            ''')
        except:
            pass
        
        return False
    
    async def _human_behavior(self, page):
        """Simuliert grundlegendes menschliches Verhalten"""
        try:
            await page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600)
            )
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            await page.evaluate(f"window.scrollBy(0, {random.randint(100, 300)})")
            await asyncio.sleep(random.uniform(0.2, 0.5))
        except:
            pass
    
    async def _human_behavior_intense(self, page):
        """Simuliert intensiveres menschliches Verhalten"""
        try:
            for _ in range(random.randint(2, 4)):
                await page.mouse.move(
                    random.randint(100, 1200),
                    random.randint(100, 800)
                )
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            scroll_amount = random.randint(200, 500)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            await page.evaluate(f"window.scrollBy(0, {random.randint(100, 300)})")
            await asyncio.sleep(random.uniform(0.3, 0.7))
            
        except:
            pass
    
    @staticmethod
    def normalize_city(city: str) -> str:
        """Normalisiert Stadtnamen für URLs"""
        return city.lower().replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe').replace('ß', 'ss').replace(' ', '-')
