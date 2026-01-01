# Digital NSW Standards PDF Compiler - Implementation Plan

## Project Overview

**Goal:** Create a Python script that downloads Digital NSW standards pages and compiles them into a single, well-structured PDF document with maintained hyperlinks and logical ordering.

**Key Requirements:**
- Scrape multiple pages from digital.nsw.gov.au
- Maintain internal hyperlinks between sections
- Preserve external links to resources
- Create logical document structure with table of contents
- Handle images and formatting appropriately
- Generate a professional, readable PDF output

---

## Technical Architecture

### Core Technologies

```
Primary Stack:
- Python 3.9+
- requests + BeautifulSoup4 (web scraping)
- weasyprint (HTML to PDF conversion with CSS support)
- PyPDF2 or pypdf (PDF manipulation)

Alternative Stack (if weasyprint has issues):
- pdfkit + wkhtmltopdf (HTML to PDF)
- reportlab (for custom PDF generation)
```

### Why WeasyPrint?

1. Best CSS support for HTML to PDF conversion
2. Maintains hyperlinks automatically
3. Handles complex layouts well
4. Pure Python (easier deployment)
5. Good documentation and active maintenance

---

## Phase 1: Web Scraping Module

### 1.1 Page Fetching

```python
# Pseudo-code structure

class DigitalNSWScraper:
    def __init__(self, base_url="https://www.digital.nsw.gov.au"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; DigitalNSW-PDF-Compiler/1.0)'
        })
    
    def fetch_page(self, url):
        """
        Fetch a single page with error handling
        - Implements retry logic (exponential backoff)
        - Respects rate limiting (politeness delay)
        - Handles timeouts and errors gracefully
        """
        pass
    
    def extract_content(self, html):
        """
        Extract main content from page
        - Identify content container (likely #main-content or similar)
        - Remove navigation, headers, footers
        - Preserve article structure
        - Extract title/heading hierarchy
        """
        pass
```

### 1.2 Content Extraction Strategy

```python
def extract_main_content(soup):
    """
    Target selectors based on Digital NSW structure:
    - Main content: #main-content or article element
    - Remove: nav, header, footer, .skip-link
    - Keep: all headings (h1-h6), paragraphs, lists, tables
    - Images: download and embed or reference
    """
    
    # Pseudocode logic:
    # 1. Find main content container
    main_content = soup.find('main') or soup.find(id='main-content')
    
    # 2. Remove unwanted elements
    for element in main_content.find_all(['nav', 'header', 'footer']):
        element.decompose()
    
    # 3. Clean up navigation breadcrumbs (but preserve them as text)
    # 4. Extract and normalize headings
    # 5. Process lists and ensure proper nesting
    # 6. Handle tables (preserve structure)
    
    return clean_html
```

### 1.3 URL Management

```python
class URLManager:
    def __init__(self, urls_config):
        """
        Load URLs from configuration file
        urls_config structure:
        {
            "sections": [
                {
                    "title": "Design Standards",
                    "url": "...",
                    "priority": 1,
                    "subsections": [...]
                }
            ]
        }
        """
        self.urls = self.load_urls(urls_config)
        self.visited = set()
    
    def get_ordered_urls(self):
        """
        Return URLs in logical reading order
        Priority: Essential -> Interview Prep -> Specific Scenarios
        """
        pass
```

**Configuration File Example (urls_config.json):**

```json
{
  "sections": [
    {
      "section_name": "Essential Reading",
      "priority": 1,
      "pages": [
        {
          "title": "Design Standards",
          "url": "https://www.digital.nsw.gov.au/delivery/digital-service-toolkit/design-standards",
          "order": 1
        },
        {
          "title": "Delivery Manual Overview",
          "url": "https://www.digital.nsw.gov.au/delivery/digital-service-toolkit/delivery-manual",
          "order": 2
        }
      ]
    }
  ]
}
```

---

## Phase 2: HTML Processing and Normalization

### 2.1 Link Handling

```python
class LinkProcessor:
    def __init__(self, base_url, url_map):
        """
        url_map: dict mapping original URLs to PDF section anchors
        {
            "https://digital.nsw.gov.au/page1": "#section-1",
            "https://digital.nsw.gov.au/page2": "#section-2"
        }
        """
        self.base_url = base_url
        self.url_map = url_map
    
    def process_links(self, soup):
        """
        Convert links:
        - Internal links within scraped pages -> PDF anchors (#section-X)
        - External links -> preserve as-is
        - Relative links -> convert to absolute
        """
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if self.is_internal_scraped_link(href):
                # Convert to PDF anchor
                link['href'] = self.url_map.get(href, href)
            elif self.is_relative_link(href):
                # Convert to absolute URL
                link['href'] = urljoin(self.base_url, href)
            # else: keep external links as-is
        
        return soup
```

### 2.2 Image Handling

```python
class ImageHandler:
    def __init__(self, download_images=True):
        self.download_images = download_images
        self.image_cache = {}
    
    def process_images(self, soup, output_dir):
        """
        Options:
        1. Download images locally and reference in PDF
        2. Convert images to base64 data URIs (embed in HTML)
        3. Leave as external URLs (may fail in PDF)
        
        Recommended: Option 2 (base64) for portability
        """
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Download image
                img_data = self.download_image(src)
                
                # Convert to base64
                base64_data = base64.b64encode(img_data).decode()
                mime_type = self.detect_mime_type(img_data)
                
                # Update src to data URI
                img['src'] = f"data:{mime_type};base64,{base64_data}"
        
        return soup
```

### 2.3 CSS Styling

```python
def generate_pdf_css():
    """
    Generate CSS for PDF output:
    - NSW Government branding (if desired)
    - Proper page breaks
    - Header/footer styling
    - Table of contents styling
    - Code block formatting
    - Responsive table handling
    """
    return """
    @page {
        size: A4;
        margin: 2cm;
        @top-center {
            content: "Digital NSW Standards";
        }
        @bottom-right {
            content: "Page " counter(page);
        }
    }
    
    body {
        font-family: 'Public Sans', Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }
    
    h1 {
        page-break-before: always;
        color: #002664; /* NSW Blue */
        font-size: 24pt;
        margin-top: 0;
    }
    
    h2 {
        color: #002664;
        font-size: 18pt;
        margin-top: 1em;
    }
    
    /* Prevent widows and orphans */
    p {
        orphans: 3;
        widows: 3;
    }
    
    /* Code blocks */
    pre, code {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        padding: 0.5em;
        font-family: 'Courier New', monospace;
    }
    
    /* Tables */
    table {
        width: 100%;
        border-collapse: collapse;
        page-break-inside: avoid;
    }
    
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    
    th {
        background-color: #002664;
        color: white;
    }
    
    /* Links */
    a {
        color: #0085B3; /* NSW Teal */
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    /* Table of Contents */
    .toc {
        page-break-after: always;
    }
    
    .toc ul {
        list-style: none;
        padding-left: 0;
    }
    
    .toc a {
        text-decoration: none;
    }
    
    .toc a::after {
        content: leader('.') target-counter(attr(href), page);
    }
    """
```

---

## Phase 3: PDF Generation

### 3.1 HTML Compilation

```python
class PDFCompiler:
    def __init__(self, pages, css_path=None):
        self.pages = pages  # List of processed HTML content
        self.css = css_path or self.generate_default_css()
    
    def create_toc(self):
        """
        Generate table of contents from page titles and headings
        Structure:
        - Section 1: Essential Reading
          - 1.1 Design Standards
          - 1.2 Delivery Manual
        - Section 2: Interview Preparation
          - 2.1 Agile Procurement
        """
        toc_html = ['<div class="toc"><h1>Table of Contents</h1><ul>']
        
        for section in self.pages:
            section_id = self.slugify(section['title'])
            toc_html.append(f'<li><a href="#{section_id}">{section["title"]}</a><ul>')
            
            # Add subsections based on h2 headings
            for subsection in section['subsections']:
                subsection_id = self.slugify(subsection)
                toc_html.append(f'<li><a href="#{subsection_id}">{subsection}</a></li>')
            
            toc_html.append('</ul></li>')
        
        toc_html.append('</ul></div>')
        return ''.join(toc_html)
    
    def compile_html(self):
        """
        Combine all pages into single HTML document:
        1. HTML header with CSS
        2. Title page
        3. Table of contents
        4. All content pages in order
        5. Close HTML
        """
        html_parts = [
            self.html_header(),
            self.title_page(),
            self.create_toc(),
        ]
        
        for page in self.pages:
            html_parts.append(self.format_page(page))
        
        html_parts.append(self.html_footer())
        
        return ''.join(html_parts)
```

### 3.2 WeasyPrint Conversion

```python
from weasyprint import HTML, CSS

def generate_pdf(html_content, output_path, css_content=None):
    """
    Convert HTML to PDF using WeasyPrint
    
    Advantages:
    - Maintains hyperlinks automatically
    - Good CSS3 support
    - Handles @page rules for headers/footers
    - Pure Python (no external dependencies)
    """
    html = HTML(string=html_content)
    
    if css_content:
        css = CSS(string=css_content)
        html.write_pdf(output_path, stylesheets=[css])
    else:
        html.write_pdf(output_path)
    
    print(f"PDF generated: {output_path}")
```

---

## Phase 4: Project Structure

```
digital-nsw-pdf-compiler/
│
├── src/
│   ├── __init__.py
│   ├── scraper.py           # Web scraping logic
│   ├── html_processor.py    # HTML cleaning and normalization
│   ├── link_handler.py      # Link conversion logic
│   ├── image_handler.py     # Image downloading and processing
│   ├── pdf_compiler.py      # PDF generation logic
│   └── utils.py             # Helper functions
│
├── config/
│   ├── urls_config.json     # URLs to scrape in order
│   └── settings.py          # Configuration settings
│
├── styles/
│   ├── pdf_styles.css       # CSS for PDF output
│   └── nsw_branding.css     # Optional NSW branding
│
├── output/
│   ├── html/                # Intermediate HTML files
│   ├── images/              # Downloaded images
│   └── digital_nsw_standards.pdf  # Final PDF output
│
├── tests/
│   ├── test_scraper.py
│   ├── test_html_processor.py
│   └── test_pdf_generation.py
│
├── requirements.txt
├── README.md
├── main.py                  # Entry point script
└── .gitignore
```

---

## Phase 5: Implementation Steps

### Step 1: Environment Setup (30 mins)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install requests beautifulsoup4 weasyprint lxml

# For WeasyPrint dependencies on different systems:
# Ubuntu/Debian: sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
# macOS: brew install cairo pango gdk-pixbuf libffi
# Windows: Often works out of the box, but may need GTK3 runtime
```

**requirements.txt:**
```
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
weasyprint>=60.0
Pillow>=10.0.0  # For image handling
```

### Step 2: Configuration Setup (20 mins)

Create `config/urls_config.json` based on the reading list structure:

```json
{
  "metadata": {
    "title": "Digital NSW Standards Reference Guide",
    "author": "Compiled for NSW Government Applications",
    "subject": "Digital Service Standards, Delivery Manual, and Guidelines"
  },
  "sections": [
    {
      "section_name": "Essential Reading",
      "description": "Foundation knowledge for NSW government digital roles",
      "priority": 1,
      "pages": [
        {
          "title": "Design Standards",
          "url": "https://www.digital.nsw.gov.au/delivery/digital-service-toolkit/design-standards",
          "order": 1,
          "estimated_reading_mins": 30
        }
        // ... more pages
      ]
    }
    // ... more sections
  ]
}
```

Create `config/settings.py`:

```python
# Scraping settings
REQUEST_DELAY = 1.0  # Seconds between requests (be polite!)
MAX_RETRIES = 3
TIMEOUT = 30  # Request timeout in seconds

# Processing settings
DOWNLOAD_IMAGES = True
EMBED_IMAGES_AS_BASE64 = True
REMOVE_NAVIGATION = True
REMOVE_FOOTERS = True

# PDF settings
OUTPUT_FILENAME = "digital_nsw_standards.pdf"
PAGE_SIZE = "A4"
INCLUDE_TOC = True
INCLUDE_PAGE_NUMBERS = True
INCLUDE_TIMESTAMPS = True

# CSS settings
USE_NSW_BRANDING = True
CUSTOM_CSS_PATH = "styles/pdf_styles.css"
```

### Step 3: Core Scraper Implementation (2-3 hours)

**src/scraper.py:**

```python
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
```

### Step 4: HTML Processing Implementation (2-3 hours)

**src/html_processor.py:**

```python
from bs4 import BeautifulSoup, NavigableString
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
        for table in soup.find_all('table'):
            # Add class for styling
            table['class'] = table.get('class', []) + ['pdf-table']
            
            # Ensure proper structure
            if not table.find('thead') and table.find('tr'):
                # First row might be header
                first_row = table.find('tr')
                if all(cell.name == 'th' for cell in first_row.find_all(['th', 'td'])):
                    thead = soup.new_tag('thead')
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
```

### Step 5: PDF Compiler Implementation (2-3 hours)

**src/pdf_compiler.py:**

```python
from weasyprint import HTML, CSS
from bs4 import BeautifulSoup
import os
from datetime import datetime


class PDFCompiler:
    """
    Compile scraped HTML content into a single PDF
    """
    
    def __init__(self, config, css_path=None):
        self.config = config
        self.css_path = css_path or config.CUSTOM_CSS_PATH
    
    def create_title_page(self, metadata):
        """Generate title page HTML"""
        return f"""
        <div class="title-page">
            <h1>{metadata.get('title', 'Digital NSW Standards')}</h1>
            <p class="subtitle">Reference Guide for Government Digital Roles</p>
            <p class="metadata">
                Compiled: {datetime.now().strftime('%d %B %Y')}<br>
                Source: digital.nsw.gov.au<br>
                {metadata.get('author', '')}
            </p>
        </div>
        """
    
    def create_toc(self, sections):
        """Generate table of contents"""
        toc_html = ['<div class="toc"><h1 id="table-of-contents">Table of Contents</h1><ul>']
        
        for section in sections:
            section_slug = HTMLProcessor.slugify(section['section_name'])
            toc_html.append(f'<li class="toc-section">')
            toc_html.append(f'<a href="#{section_slug}">{section["section_name"]}</a>')
            toc_html.append('<ul>')
            
            for page in section['pages']:
                page_slug = HTMLProcessor.slugify(page['title'])
                toc_html.append(f'<li><a href="#{page_slug}">{page["title"]}</a></li>')
            
            toc_html.append('</ul></li>')
        
        toc_html.append('</ul></div>')
        return ''.join(toc_html)
    
    def compile_html_document(self, sections, metadata):
        """Compile all sections into single HTML document"""
        html_parts = []
        
        # HTML header
        html_parts.append("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>{}</title>
        </head>
        <body>
        """.format(metadata.get('title', 'Digital NSW Standards')))
        
        # Title page
        html_parts.append(self.create_title_page(metadata))
        
        # Table of contents
        html_parts.append(self.create_toc(sections))
        
        # Content sections
        for section in sections:
            section_slug = HTMLProcessor.slugify(section['section_name'])
            html_parts.append(f'<div class="section" id="{section_slug}">')
            html_parts.append(f'<h1 class="section-title">{section["section_name"]}</h1>')
            
            for page in section['pages']:
                page_slug = HTMLProcessor.slugify(page['title'])
                html_parts.append(f'<div class="page" id="{page_slug}">')
                html_parts.append(str(page['content']))
                html_parts.append('</div>')
            
            html_parts.append('</div>')
        
        # HTML footer
        html_parts.append('</body></html>')
        
        return ''.join(html_parts)
    
    def generate_pdf(self, html_content, output_path):
        """Generate PDF from HTML content"""
        # Load CSS
        with open(self.css_path, 'r') as f:
            css_content = f.read()
        
        # Create WeasyPrint objects
        html = HTML(string=html_content)
        css = CSS(string=css_content)
        
        # Generate PDF
        html.write_pdf(output_path, stylesheets=[css])
        
        print(f"✓ PDF generated successfully: {output_path}")
        
        # Get file size
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  File size: {size_mb:.2f} MB")
```

### Step 6: Main Script Implementation (1 hour)

**main.py:**

```python
#!/usr/bin/env python3
"""
Digital NSW Standards PDF Compiler
Scrapes Digital NSW website and compiles standards into a single PDF
"""

import json
import argparse
import sys
from pathlib import Path

from src.scraper import DigitalNSWScraper
from src.html_processor import HTMLProcessor
from src.image_handler import ImageHandler
from src.pdf_compiler import PDFCompiler
from config import settings


def load_url_config(config_path):
    """Load URL configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


def create_url_map(sections):
    """Create mapping of URLs to section anchors"""
    url_map = {}
    for section in sections:
        for page in section['pages']:
            slug = HTMLProcessor.slugify(page['title'])
            url_map[page['url']] = slug
    return url_map


def main():
    parser = argparse.ArgumentParser(
        description='Compile Digital NSW standards into a PDF document'
    )
    parser.add_argument(
        '--config',
        default='config/urls_config.json',
        help='Path to URL configuration file'
    )
    parser.add_argument(
        '--output',
        default='output/digital_nsw_standards.pdf',
        help='Output PDF path'
    )
    parser.add_argument(
        '--save-html',
        action='store_true',
        help='Save intermediate HTML file'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Digital NSW Standards PDF Compiler")
    print("=" * 60)
    
    # Load configuration
    print("\n[1/6] Loading configuration...")
    url_config = load_url_config(args.config)
    print(f"  Loaded {len(url_config['sections'])} sections")
    
    # Initialize scraper
    print("\n[2/6] Scraping web pages...")
    scraper = DigitalNSWScraper(settings)
    scraped_content = scraper.scrape_url_list(url_config)
    print(f"  Successfully scraped pages")
    
    # Create URL map for internal linking
    print("\n[3/6] Processing HTML content...")
    url_map = create_url_map(scraped_content)
    processor = HTMLProcessor(scraper.base_url, url_map)
    
    # Process all pages
    for section in scraped_content:
        for page in section['pages']:
            section_id = HTMLProcessor.slugify(page['title'])
            page['content'] = processor.process_page(page['content'], section_id)
    
    print(f"  Processed {len(url_map)} pages")
    
    # Handle images (if enabled)
    if settings.DOWNLOAD_IMAGES:
        print("\n[4/6] Processing images...")
        image_handler = ImageHandler(settings)
        for section in scraped_content:
            for page in section['pages']:
                page['content'] = image_handler.process_images(
                    page['content'],
                    'output/images'
                )
        print("  Images processed")
    else:
        print("\n[4/6] Skipping image processing")
    
    # Compile HTML
    print("\n[5/6] Compiling HTML document...")
    compiler = PDFCompiler(settings)
    html_document = compiler.compile_html_document(
        scraped_content,
        url_config.get('metadata', {})
    )
    
    if args.save_html:
        html_path = args.output.replace('.pdf', '.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_document)
        print(f"  HTML saved to: {html_path}")
    
    # Generate PDF
    print("\n[6/6] Generating PDF...")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    compiler.generate_pdf(html_document, str(output_path))
    
    print("\n" + "=" * 60)
    print("✓ Compilation complete!")
    print(f"  Output: {output_path.absolute()}")
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

### Step 7: Testing (2-3 hours)

**tests/test_scraper.py:**

```python
import unittest
from src.scraper import DigitalNSWScraper
from config import settings


class TestScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = DigitalNSWScraper(settings)
    
    def test_fetch_page(self):
        """Test fetching a known page"""
        url = "https://www.digital.nsw.gov.au/delivery/digital-service-toolkit/design-standards"
        html = self.scraper.fetch_page(url)
        self.assertIsNotNone(html)
        self.assertIn('Design Standards', html)
    
    def test_extract_main_content(self):
        """Test content extraction"""
        url = "https://www.digital.nsw.gov.au/delivery/digital-service-toolkit/design-standards"
        html = self.scraper.fetch_page(url)
        content = self.scraper.extract_main_content(html, url)
        self.assertIsNotNone(content)
        
        # Should have removed navigation
        self.assertIsNone(content.find('nav'))


if __name__ == '__main__':
    unittest.main()
```

---

## Phase 6: Usage Examples

### Basic Usage

```bash
# Run with default configuration
python main.py

# Specify custom configuration
python main.py --config my_urls.json --output my_output.pdf

# Save intermediate HTML for debugging
python main.py --save-html
```

### Advanced Configuration

```python
# Create custom URL configuration for specific topics
custom_config = {
    "metadata": {
        "title": "Scrum Master Focus - Digital NSW",
        "author": "Joseph Radford"
    },
    "sections": [
        {
            "section_name": "Agile & Scrum",
            "pages": [
                {
                    "title": "Discovery Phase",
                    "url": "https://www.digital.nsw.gov.au/delivery/digital-service-toolkit/delivery-manual/discovery-phase",
                    "order": 1
                },
                # ... more pages
            ]
        }
    ]
}
```

---

## Phase 7: Potential Enhancements

### Enhancement 1: Incremental Updates
```python
# Cache scraped content to avoid re-scraping unchanged pages
class ScraperWithCache(DigitalNSWScraper):
    def fetch_page_cached(self, url):
        cache_file = self.get_cache_path(url)
        if cache_file.exists() and not self.is_cache_stale(cache_file):
            return cache_file.read_text()
        else:
            content = self.fetch_page(url)
            cache_file.write_text(content)
            return content
```

### Enhancement 2: Progress Tracking
```python
# Add progress bar using tqdm
from tqdm import tqdm

def scrape_url_list(self, url_config):
    all_pages = self.flatten_page_list(url_config)
    with tqdm(total=len(all_pages), desc="Scraping pages") as pbar:
        for page in all_pages:
            self.fetch_page(page['url'])
            pbar.update(1)
```

### Enhancement 3: Parallel Scraping
```python
# Speed up scraping with concurrent requests
from concurrent.futures import ThreadPoolExecutor

def scrape_url_list_parallel(self, url_config, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(self.fetch_page, page['url']): page
            for section in url_config['sections']
            for page in section['pages']
        }
        # ... collect results
```

### Enhancement 4: Quality Checks
```python
# Validate scraped content
def validate_content(self, soup):
    checks = {
        'has_heading': bool(soup.find('h1')),
        'has_paragraphs': bool(soup.find('p')),
        'word_count': len(soup.get_text().split()),
        'has_links': bool(soup.find('a'))
    }
    
    if checks['word_count'] < 100:
        logger.warning("Page has very little content")
    
    return checks
```

---

## Phase 8: Error Handling & Edge Cases

### Common Issues and Solutions

**Issue 1: WeasyPrint Installation Problems**
```bash
# Solution: Use pdfkit as fallback
pip install pdfkit
# Then install wkhtmltopdf binary:
# Ubuntu: sudo apt-get install wkhtmltopdf
# macOS: brew install wkhtmltopdf
# Windows: Download from https://wkhtmltopdf.org/
```

**Issue 2: Large File Sizes**
```python
# Compress images before embedding
from PIL import Image
import io

def compress_image(image_data, quality=85):
    img = Image.open(io.BytesIO(image_data))
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    return output.getvalue()
```

**Issue 3: Rate Limiting**
```python
# Implement exponential backoff
import random

def fetch_with_backoff(self, url, attempt=0):
    try:
        return self.session.get(url)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429 and attempt < 5:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
            return self.fetch_with_backoff(url, attempt + 1)
        raise
```

---

## Estimated Total Implementation Time

| Phase | Task | Time Estimate |
|-------|------|---------------|
| 1 | Environment setup & dependencies | 0.5 hours |
| 2 | Configuration files setup | 0.5 hours |
| 3 | Core scraper implementation | 2-3 hours |
| 4 | HTML processor implementation | 2-3 hours |
| 5 | PDF compiler implementation | 2-3 hours |
| 6 | Main script & CLI | 1 hour |
| 7 | Testing & debugging | 2-3 hours |
| 8 | CSS styling & polish | 1-2 hours |
| **Total** | | **11-16 hours** |

---

## Final Deliverables

1. **Python package** with modular, testable code
2. **Configuration files** for easy URL management
3. **CSS styles** matching NSW Government branding
4. **Documentation** (README, usage examples)
5. **PDF output** with:
   - Table of contents with page numbers
   - Working internal hyperlinks
   - Preserved external links
   - Professional formatting
   - NSW Government styling (optional)

---

## Alternative Approaches to Consider

### Approach 1: Use Existing Tools
```bash
# Simple but less control
wget --mirror --convert-links --page-requisites \
     --no-parent https://www.digital.nsw.gov.au/delivery/

# Then use something like wkhtmltopdf or Pandoc
```

**Pros:** Very quick to implement
**Cons:** Less control over output, harder to maintain structure

### Approach 2: Browser Automation
```python
# Use Playwright or Selenium to render JavaScript-heavy pages
from playwright.sync_api import sync_playwright

def scrape_with_browser(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        content = page.content()
        browser.close()
        return content
```

**Pros:** Handles JavaScript, exact rendering
**Cons:** Slower, more dependencies

### Approach 3: API-Based (if available)
```python
# Check if Digital NSW has a public API
# Most government sites don't, but worth checking
```

---

## Maintenance Considerations

### Regular Updates
```bash
# Schedule periodic regeneration
0 0 * * 0 cd /path/to/project && python main.py  # Weekly on Sunday
```

### Version Control
```python
# Include metadata in PDF
metadata = {
    'title': 'Digital NSW Standards',
    'version': '2025.01.15',  # Date-based versioning
    'source_urls': len(all_urls),
    'generated': datetime.now().isoformat()
}
```

### Change Detection
```python
# Track changes between versions
def detect_changes(old_content, new_content):
    # Use difflib or similar
    import difflib
    differ = difflib.HtmlDiff()
    return differ.make_file(old_content, new_content)
```

---

This implementation plan provides a solid foundation for creating a professional PDF compilation of Digital NSW standards while maintaining hyperlinks and logical structure. The modular design makes it easy to extend and customize based on specific needs.
