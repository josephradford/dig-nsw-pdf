from weasyprint import HTML, CSS
from bs4 import BeautifulSoup
import os
from datetime import datetime
from src.html_processor import HTMLProcessor


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
