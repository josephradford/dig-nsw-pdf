from weasyprint import HTML, CSS
from bs4 import BeautifulSoup
import os
from datetime import datetime
from src.html_processor import HTMLProcessor


def build_page_tree(pages):
    """
    Build a hierarchical tree structure from flat list of pages based on URL hierarchy

    Args:
        pages: List of page dictionaries with 'url' and other fields

    Returns:
        List of root pages with 'children' field populated recursively
    """
    from urllib.parse import urlparse

    # Create a mapping of URL to page
    pages_by_url = {page['url']: {**page, 'children': []} for page in pages}

    # Build parent-child relationships based on URL path hierarchy
    # For each page, find its parent by removing the last path segment
    for page in pages:
        url = page['url']
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]

        # Store the page reference
        page_obj = pages_by_url[url]

        # Try to find parent by progressively removing path segments
        if len(path_parts) > 0:
            # Try shorter paths to find parent
            for i in range(len(path_parts) - 1, 0, -1):
                parent_path = '/' + '/'.join(path_parts[:i])
                parent_url = f"{parsed.scheme}://{parsed.netloc}{parent_path}"

                if parent_url in pages_by_url and parent_url != url:
                    # Found a parent that exists in our pages
                    pages_by_url[parent_url]['children'].append(page_obj)
                    break

    # Collect root pages (pages that aren't children of any other page)
    all_children = set()
    for page in pages_by_url.values():
        for child in page['children']:
            all_children.add(child['url'])

    root_pages = [p for p in pages_by_url.values() if p['url'] not in all_children]

    return root_pages


class PDFCompiler:
    """
    Compile scraped HTML content into a single PDF
    """

    def __init__(self, config, css_path=None):
        self.config = config
        self.css_path = css_path or config.CUSTOM_CSS_PATH

    def create_title_page(self, metadata, generation_timestamp):
        """Generate title page HTML with important notice (no heading elements for bookmarks)"""
        formatted_date = generation_timestamp.strftime('%d %B %Y')
        formatted_datetime = generation_timestamp.strftime('%d %B %Y at %H:%M UTC')

        return f"""
        <div class="title-page">
            <p class="title-page-heading">{metadata.get('title', 'Digital NSW Standards')}</p>
            <p class="subtitle">Reference Guide for Government Digital Roles</p>
            <p class="metadata">
                {metadata.get('author', '')}
            </p>

            <div class="important-notice">
                <p class="important-notice-heading">IMPORTANT NOTICE</p>
                <p>This document was automatically generated on <strong>{formatted_date}</strong> from
                content published at <a href="https://www.digital.nsw.gov.au/delivery" class="website-link">https://www.digital.nsw.gov.au/delivery</a>.</p>

                <p>This is a point-in-time snapshot and may not reflect the current state
                of NSW Government policies, standards, or guidance.</p>

                <p>For the most up-to-date information, please visit:<br>
                <a href="https://www.digital.nsw.gov.au/delivery" class="website-link">https://www.digital.nsw.gov.au/delivery</a></p>

                <p class="timestamp">Last Generated: {formatted_datetime}</p>
            </div>
        </div>
        """

    def create_toc(self, sections):
        """Generate table of contents with hierarchical structure (no h1 for bookmarks)"""
        toc_html = ['<div class="toc"><p class="toc-heading" id="table-of-contents">Table of Contents</p><ul>']

        for section in sections:
            section_slug = HTMLProcessor.slugify(section['section_name'])
            toc_html.append(f'<li class="toc-section">')
            toc_html.append(f'<a href="#{section_slug}">{section["section_name"]}</a>')

            # Render hierarchical page structure
            if section.get('page_tree'):
                toc_html.append(self._render_toc_tree(section['page_tree']))

            toc_html.append('</li>')

        toc_html.append('</ul></div>')
        return ''.join(toc_html)

    def _render_toc_tree(self, pages, level=0):
        """Recursively render TOC tree structure"""
        if not pages:
            return ''

        html = ['<ul>']
        for page in pages:
            page_slug = HTMLProcessor.slugify(page['title'])
            indent_class = f'toc-level-{level}' if level > 0 else ''
            html.append(f'<li class="{indent_class}">')
            html.append(f'<a href="#{page_slug}">{page["title"]}</a>')

            # Recursively render children
            if page.get('children'):
                html.append(self._render_toc_tree(page['children'], level + 1))

            html.append('</li>')
        html.append('</ul>')
        return ''.join(html)

    def _normalize_content_headings(self, content):
        """
        Convert h1-h6 headings in page content to styled divs to prevent PDF bookmark conflicts

        Args:
            content: BeautifulSoup content object or string

        Returns:
            Modified content with headings converted to divs
        """
        from bs4 import BeautifulSoup

        # Wrap content in a container soup if it's a tag
        if hasattr(content, 'name'):  # It's a BeautifulSoup Tag
            # Create a new soup and add the content to it
            soup = BeautifulSoup('', 'html.parser')
            container = soup.new_tag('div')
            # Copy the content
            for child in list(content.children):
                container.append(child.extract())
            soup.append(container)
        elif isinstance(content, str):
            soup = BeautifulSoup(content, 'html.parser')
            container = soup
        else:
            # Already a soup object
            soup = content
            container = content

        # Replace all headings with styled divs
        for heading_level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for heading in container.find_all(heading_level):
                # Create a div with the same content
                div = soup.new_tag('div')
                div['class'] = heading.get('class', []) + [f'content-{heading_level}']

                # Copy all children
                for child in list(heading.children):
                    div.append(child.extract())

                # Copy id if present
                if heading.get('id'):
                    div['id'] = heading['id']

                # Replace heading with div
                heading.replace_with(div)

        # Return just the container content if we created a wrapper
        if hasattr(content, 'name'):
            return container
        return soup

    def _render_page_tree(self, pages, base_heading_level=2):
        """
        Recursively render pages with hierarchical structure

        Args:
            pages: List of page dictionaries with 'children' field
            base_heading_level: Starting heading level (2 = h2, 3 = h3, etc.)

        Returns:
            HTML string with hierarchical page structure
        """
        if not pages:
            return ''

        html_parts = []

        for page in pages:
            page_slug = HTMLProcessor.slugify(page['title'])
            heading_level = min(base_heading_level, 6)  # HTML only goes to h6

            # Start page div
            html_parts.append(f'<div class="page page-level-{base_heading_level - 2}" id="{page_slug}">')

            # Add page heading (this creates the PDF bookmark)
            html_parts.append(f'<h{heading_level} class="page-title">{page["title"]}</h{heading_level}>')

            # Normalize content headings to prevent bookmark conflicts
            normalized_content = self._normalize_content_headings(page['content'])
            html_parts.append(str(normalized_content))

            # Recursively render children
            if page.get('children'):
                html_parts.append('<div class="page-children">')
                html_parts.append(self._render_page_tree(page['children'], base_heading_level + 1))
                html_parts.append('</div>')

            html_parts.append('</div>')

        return ''.join(html_parts)

    def compile_html_document(self, sections, metadata):
        """Compile all sections into single HTML document

        Returns:
            tuple: (html_content, generation_timestamp)
        """
        html_parts = []

        # Get generation timestamp in UTC
        generation_timestamp = datetime.utcnow()

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
        html_parts.append(self.create_title_page(metadata, generation_timestamp))

        # Build tree structure for each section
        for section in sections:
            section['page_tree'] = build_page_tree(section['pages'])

        # Table of contents
        html_parts.append(self.create_toc(sections))

        # Content sections
        for section in sections:
            section_slug = HTMLProcessor.slugify(section['section_name'])
            html_parts.append(f'<div class="section" id="{section_slug}">')
            html_parts.append(f'<h1 class="section-title">{section["section_name"]}</h1>')

            # Render hierarchical page structure
            html_parts.append(self._render_page_tree(section['page_tree'], base_heading_level=2))

            html_parts.append('</div>')

        # HTML footer
        html_parts.append('</body></html>')

        return ''.join(html_parts), generation_timestamp

    def generate_pdf(self, html_content, output_path, generation_timestamp=None):
        """Generate PDF from HTML content"""
        # Load CSS
        with open(self.css_path, 'r') as f:
            css_content = f.read()

        # Inject generation timestamp into CSS if provided
        if generation_timestamp:
            # Format timestamp as UTC
            formatted_datetime = generation_timestamp.strftime('%d %b %Y %H:%M UTC')
            footer_text = f"Generated: {formatted_datetime} | Source: digital.nsw.gov.au/delivery"

            # Add dynamic CSS for the footer
            dynamic_css = f"""
            @page {{
                @bottom-left {{
                    content: "{footer_text}";
                    font-size: 8pt;
                    color: #999;
                }}
            }}
            """
            css_content = css_content + dynamic_css

        # Create WeasyPrint objects
        html = HTML(string=html_content)
        css = CSS(string=css_content)

        # Generate PDF
        html.write_pdf(output_path, stylesheets=[css])

        print(f"✓ PDF generated successfully: {output_path}")

        # Get file size
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  File size: {size_mb:.2f} MB")
