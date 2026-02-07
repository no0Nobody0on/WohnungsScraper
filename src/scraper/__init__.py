from .scraper import BatchScraper
from .normalizer import AddressNormalizer
from .base import BaseScraper
from .wg_gesucht import WGGesuchtScraper
from .immoscout import ImmoScoutScraper
from .immowelt import ImmoweltScraper
from .kleinanzeigen import KleinanzeigenScraper

# Optional: Scrapfly Integration
try:
    from .scrapfly_scraper import ScrapflyScraper, SCRAPFLY_AVAILABLE
except ImportError:
    SCRAPFLY_AVAILABLE = False
    ScrapflyScraper = None

# Optional: ScrapeOps Integration
try:
    from .scrapeops_scraper import ScrapeOpsScraper, SCRAPEOPS_AVAILABLE
except ImportError:
    SCRAPEOPS_AVAILABLE = False
    ScrapeOpsScraper = None

__all__ = [
    'BatchScraper', 
    'AddressNormalizer',
    'BaseScraper',
    'WGGesuchtScraper',
    'ImmoScoutScraper', 
    'ImmoweltScraper',
    'KleinanzeigenScraper',
    'ScrapflyScraper',
    'SCRAPFLY_AVAILABLE',
    'ScrapeOpsScraper',
    'SCRAPEOPS_AVAILABLE'
]
