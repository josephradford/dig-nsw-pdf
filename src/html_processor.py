from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re


class HTMLProcessor:
    """
    Process and normalize HTML content for PDF generation
    """

    def __init__(self, base_url, url_map):
        self.base_url = base_url
        self.url_map = url_map  # Maps URLs to section anchors

    def add_section_anchors(self, soup, section_id):
        """Add anchor ID to main heading for internal linking"""
        h1 = soup.find('h1')
        if h1:
            h1['id'] = section_id
        return soup

    def process_links(self, soup):
        """Convert links for PDF navigation"""
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Skip anchor-only links
            if href.startswith('#'):
                continue

            # Convert internal links to PDF anchors
            full_url = urljoin(self.base_url, href)
            if full_url in self.url_map:
                link['href'] = f"#{self.url_map[full_url]}"
                link['class'] = link.get('class', []) + ['internal-link']
            else:
                # External link - ensure it's absolute
                link['href'] = full_url
                link['class'] = link.get('class', []) + ['external-link']
                link['target'] = '_blank'

        return soup

    def clean_headings(self, soup):
        """Normalize heading hierarchy"""
        # If page has h1, ensure others follow logical sequence
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        # Add heading IDs for TOC generation
        for i, heading in enumerate(headings):
            if not heading.get('id'):
                heading['id'] = self.slugify(heading.get_text())

        return soup

    def process_tables(self, soup):
        """Ensure tables are PDF-friendly"""
        # Get the root BeautifulSoup object (needed for new_tag method)
        # If soup is a Tag, traverse up to find the root BeautifulSoup object
        root = soup
        while hasattr(root, 'parent') and root.parent is not None:
            root = root.parent

        for table in soup.find_all('table'):
            # Add class for styling
            table['class'] = table.get('class', []) + ['pdf-table']

            # Ensure proper structure
            if not table.find('thead') and table.find('tr'):
                # First row might be header
                first_row = table.find('tr')
                if all(cell.name == 'th' for cell in first_row.find_all(['th', 'td'])):
                    thead = root.new_tag('thead')
                    first_row.wrap(thead)

        return soup

    def process_code_blocks(self, soup):
        """Enhance code blocks for PDF"""
        for code in soup.find_all('code'):
            if not code.parent or code.parent.name != 'pre':
                # Inline code - add class
                code['class'] = code.get('class', []) + ['inline-code']

        for pre in soup.find_all('pre'):
            pre['class'] = pre.get('class', []) + ['code-block']

        return soup

    @staticmethod
    def slugify(text):
        """Convert text to URL-safe slug"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text

    def process_page(self, soup, section_id):
        """Apply all processing to a page"""
        soup = self.add_section_anchors(soup, section_id)
        soup = self.clean_headings(soup)
        soup = self.process_links(soup)
        soup = self.process_tables(soup)
        soup = self.process_code_blocks(soup)
        return soup
