import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DigitalNSWScraper:
    """
    Scraper for digital.nsw.gov.au content
    """

    def __init__(self, config):
        self.base_url = "https://www.digital.nsw.gov.au"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; DigitalNSW-PDF-Compiler/1.0)'
        })
        self.config = config
        self.pages_cache = {}

    def fetch_page(self, url, retry_count=0):
        """Fetch a single page with retry logic"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.config.TIMEOUT)
            response.raise_for_status()

            # Be polite - delay between requests
            time.sleep(self.config.REQUEST_DELAY)

            return response.text

        except requests.RequestException as e:
            if retry_count < self.config.MAX_RETRIES:
                logger.warning(f"Retry {retry_count + 1}/{self.config.MAX_RETRIES} for {url}")
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self.fetch_page(url, retry_count + 1)
            else:
                logger.error(f"Failed to fetch {url}: {e}")
                return None

    def extract_main_content(self, html, url):
        """Extract main content from page"""
        soup = BeautifulSoup(html, 'lxml')

        # Find main content area
        main_content = (
            soup.find('main') or
            soup.find(id='main-content') or
            soup.find('article') or
            soup.find(class_='content')
        )

        if not main_content:
            logger.warning(f"Could not find main content area for {url}")
            return None

        # Remove unwanted elements
        for unwanted in main_content.find_all(['nav', 'header', 'footer', 'script', 'style']):
            unwanted.decompose()

        # Remove skip links
        for skip_link in main_content.find_all(class_=['skip-link', 'skip-to-content']):
            skip_link.decompose()

        return main_content

    def scrape_url_list(self, url_config):
        """Scrape all URLs from configuration"""
        results = []

        for section in url_config['sections']:
            section_results = {
                'section_name': section['section_name'],
                'pages': []
            }

            for page in section['pages']:
                html = self.fetch_page(page['url'])
                if html:
                    content = self.extract_main_content(html, page['url'])
                    if content:
                        section_results['pages'].append({
                            'title': page['title'],
                            'url': page['url'],
                            'content': content,
                            'order': page['order']
                        })

            results.append(section_results)

        return results
