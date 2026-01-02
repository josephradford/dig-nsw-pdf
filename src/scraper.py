import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DigitalNSWScraper:
    """
    Scraper for digital.nsw.gov.au content with recursive link following
    """

    def __init__(self, config):
        self.base_url = "https://www.digital.nsw.gov.au"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; DigitalNSW-PDF-Compiler/1.0)'
        })
        self.config = config
        self.pages_cache = {}
        self.visited_urls = set()

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

        # Remove aria-hidden elements (decorative icons like Material Icons)
        for hidden in main_content.find_all(attrs={'aria-hidden': 'true'}):
            hidden.decompose()

        return main_content

    def extract_internal_links(self, soup, base_path):
        """
        Extract internal links from page that are within the same section
        base_path: e.g., '/delivery/digital-service-toolkit'
        """
        internal_links = set()

        for link in soup.find_all('a', href=True):
            href = link['href']

            # Convert to absolute URL
            if not href.startswith('http'):
                href = urljoin(self.base_url, href)

            # Parse URL
            parsed = urlparse(href)

            # Check if it's an internal link within the same section
            if (parsed.netloc == 'www.digital.nsw.gov.au' and
                parsed.path.startswith(base_path) and
                not parsed.path.endswith(('.pdf', '.docx', '.xlsx', '.zip'))):

                # Remove fragment and query
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                internal_links.add(clean_url)

        return internal_links

    def scrape_page_recursive(self, url, base_path, depth=0, max_depth=3):
        """
        Recursively scrape a page and its internal links

        Args:
            url: URL to scrape
            base_path: Base path for this section (e.g., '/delivery/digital-service-toolkit')
            depth: Current recursion depth
            max_depth: Maximum recursion depth

        Returns:
            List of page dictionaries with title, url, and content
        """
        # Check if already visited
        if url in self.visited_urls:
            return []

        # Check depth limit
        if depth > max_depth:
            logger.debug(f"Max depth reached for {url}")
            return []

        # Mark as visited
        self.visited_urls.add(url)

        # Fetch the page
        html = self.fetch_page(url)
        if not html:
            return []

        # Parse HTML
        soup = BeautifulSoup(html, 'lxml')

        # Extract main content
        content = self.extract_main_content(html, url)
        if not content:
            return []

        # Extract title
        title_elem = soup.find('h1') or soup.find('title')
        title = title_elem.get_text(strip=True) if title_elem else url.split('/')[-1]

        # Create page entry
        pages = [{
            'title': title,
            'url': url,
            'content': content,
            'order': depth
        }]

        # Extract and follow internal links
        if depth < max_depth:
            internal_links = self.extract_internal_links(soup, base_path)

            for link_url in internal_links:
                if link_url not in self.visited_urls:
                    logger.info(f"Following internal link: {link_url} (depth {depth + 1})")
                    child_pages = self.scrape_page_recursive(link_url, base_path, depth + 1, max_depth)
                    pages.extend(child_pages)

        return pages

    def scrape_url_list(self, url_config):
        """Scrape all URLs from configuration with recursive link following"""
        results = []

        for section in url_config['sections']:
            section_results = {
                'section_name': section['section_name'],
                'pages': []
            }

            # Get base path for this section
            base_path = section.get('base_path', '/delivery')

            # Reset visited URLs for each section
            self.visited_urls = set()

            for page in section['pages']:
                # Use recursive scraping
                scraped_pages = self.scrape_page_recursive(
                    page['url'],
                    base_path,
                    depth=0,
                    max_depth=section.get('max_depth', 3)
                )
                section_results['pages'].extend(scraped_pages)

            results.append(section_results)

        return results
