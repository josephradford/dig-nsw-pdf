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
