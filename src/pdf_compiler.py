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

    def create_title_page(self, metadata, generation_timestamp):
        """Generate title page HTML with important notice"""
        formatted_date = generation_timestamp.strftime('%d %B %Y')
        formatted_datetime = generation_timestamp.strftime('%d %B %Y at %H:%M UTC')

        return f"""
        <div class="title-page">
            <h1>{metadata.get('title', 'Digital NSW Standards')}</h1>
            <p class="subtitle">Reference Guide for Government Digital Roles</p>
            <p class="metadata">
                {metadata.get('author', '')}
            </p>

            <div class="important-notice">
                <h2>IMPORTANT NOTICE</h2>
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
