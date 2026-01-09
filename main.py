#!/usr/bin/env python3
"""
Digital NSW Standards PDF Compiler
Scrapes Digital NSW website and compiles each section into separate PDFs
"""

import json
import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

from src.scraper import DigitalNSWScraper
from src.html_processor import HTMLProcessor
from src.image_handler import ImageHandler
from src.pdf_compiler import PDFCompiler
from config import settings


def has_documents(config):
    """Check if config contains multi-section documents"""
    return 'documents' in config and len(config['documents']) > 0


def has_sections(config):
    """Check if config contains standalone sections"""
    return 'sections' in config and len(config['sections']) > 0


def load_url_config(config_path):
    """Load URL configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


def create_url_map(pages):
    """Create mapping of URLs to section anchors for a single section"""
    url_map = {}
    for page in pages:
        slug = HTMLProcessor.slugify(page['title'])
        url_map[page['url']] = slug
    return url_map


def process_section(section_config, scraper, settings, output_dir, save_html=False):
    """Process a single section and generate its PDF"""
    section_name = section_config['section_name']
    output_filename = section_config.get('output_filename', f"{HTMLProcessor.slugify(section_name)}.pdf")

    print(f"\n{'=' * 60}")
    print(f"Processing: {section_name}")
    print(f"{'=' * 60}")

    # Get base URL for this section - either from config or extract from first page URL
    if 'base_url' in section_config:
        base_url = section_config['base_url']
    else:
        # Extract base URL from the first page URL
        first_page_url = section_config['pages'][0]['url']
        parsed = urlparse(first_page_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

    # Scrape pages
    print("\n[1/5] Scraping web pages...")
    scraped_content = scraper.scrape_url_list({'sections': [section_config]})

    if not scraped_content or not scraped_content[0]['pages']:
        print(f"  ⚠ No pages found for {section_name}")
        return None

    section_data = scraped_content[0]
    page_count = len(section_data['pages'])
    print(f"  Scraped {page_count} pages")

    # Create URL map for internal linking
    print("\n[2/5] Processing HTML content...")
    url_map = create_url_map(section_data['pages'])
    processor = HTMLProcessor(base_url, url_map)

    # Process all pages
    for page in section_data['pages']:
        if page['content'] is None:
            print(f"  ⚠ Skipping page with no content: {page['title']}")
            continue
        section_id = HTMLProcessor.slugify(page['title'])
        try:
            page['content'] = processor.process_page(page['content'], section_id)
        except Exception as e:
            print(f"  ✗ Error processing page '{page['title']}' ({page['url']}): {e}")
            print(f"     Content type: {type(page['content'])}")
            raise

    # Filter out pages with None content
    section_data['pages'] = [p for p in section_data['pages'] if p['content'] is not None]

    print(f"  Processed {len(url_map)} pages")

    # Handle images (if enabled)
    if settings.DOWNLOAD_IMAGES:
        print("\n[3/5] Processing images...")
        image_handler = ImageHandler(settings)
        for page in section_data['pages']:
            page['content'] = image_handler.process_images(
                page['content'],
                output_dir / 'images'
            )
        print("  Images processed")
    else:
        print("\n[3/5] Skipping image processing")

    # Compile HTML
    print("\n[4/5] Compiling HTML document...")
    compiler = PDFCompiler(settings)
    html_document, generation_timestamp = compiler.compile_html_document(
        [section_data],
        section_config.get('metadata', {'title': section_name})
    )

    if save_html:
        html_path = output_dir / 'html' / output_filename.replace('.pdf', '.html')
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_document)
        print(f"  HTML saved to: {html_path}")

    # Generate PDF
    print("\n[5/5] Generating PDF...")
    output_path = output_dir / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    compiler.generate_pdf(html_document, str(output_path), generation_timestamp)

    print(f"✓ {section_name} complete!")
    print(f"  Output: {output_path.absolute()}")

    return output_path


def process_document(document_config, scraper, settings, output_dir, save_html=False):
    """Process a multi-section document and generate a single PDF

    Args:
        document_config: Document configuration with 'sections' list
        scraper: DigitalNSWScraper instance
        settings: Application settings
        output_dir: Path to output directory
        save_html: Whether to save intermediate HTML

    Returns:
        Path to generated PDF or None if failed
    """
    document_name = document_config['document_name']
    output_filename = document_config.get('output_filename', f"{HTMLProcessor.slugify(document_name)}.pdf")

    print(f"\n{'=' * 60}")
    print(f"Processing Document: {document_name}")
    print(f"  Contains {len(document_config['sections'])} sections")
    print(f"{'=' * 60}")

    # Scrape all sections
    all_section_data = []
    all_pages = []

    for i, section_config in enumerate(document_config['sections'], 1):
        section_name = section_config['section_name']
        print(f"\n[Section {i}/{len(document_config['sections'])}] {section_name}")

        # Get base URL
        if 'base_url' in section_config:
            base_url = section_config['base_url']
        else:
            first_page_url = section_config['pages'][0]['url']
            parsed = urlparse(first_page_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Scrape this section
        print("  Scraping web pages...")
        scraped_content = scraper.scrape_url_list({'sections': [section_config]})

        if not scraped_content or not scraped_content[0]['pages']:
            print(f"  ⚠ No pages found for {section_name}")
            continue

        section_data = scraped_content[0]
        page_count = len(section_data['pages'])
        print(f"  Scraped {page_count} pages")

        # Collect all pages for URL mapping
        all_pages.extend(section_data['pages'])
        all_section_data.append((section_data, base_url))

    if not all_section_data:
        print(f"  ⚠ No content found for document {document_name}")
        return None

    # Create unified URL map for all sections
    print(f"\nProcessing HTML content for all sections...")
    url_map = create_url_map(all_pages)

    # Process each section's pages
    for section_data, base_url in all_section_data:
        processor = HTMLProcessor(base_url, url_map)

        for page in section_data['pages']:
            if page['content'] is None:
                print(f"  ⚠ Skipping page with no content: {page['title']}")
                continue

            section_id = HTMLProcessor.slugify(page['title'])
            try:
                page['content'] = processor.process_page(page['content'], section_id)
            except Exception as e:
                print(f"  ✗ Error processing page '{page['title']}' ({page['url']}): {e}")
                print(f"     Content type: {type(page['content'])}")
                raise

        # Filter out None content
        section_data['pages'] = [p for p in section_data['pages'] if p['content'] is not None]

    total_pages = sum(len(sd['pages']) for sd, _ in all_section_data)
    print(f"  Processed {total_pages} total pages across {len(all_section_data)} sections")

    # Process images if enabled
    if settings.DOWNLOAD_IMAGES:
        print("\nProcessing images...")
        image_handler = ImageHandler(settings)
        for section_data, _ in all_section_data:
            for page in section_data['pages']:
                page['content'] = image_handler.process_images(
                    page['content'],
                    output_dir / 'images'
                )
        print("  Images processed")
    else:
        print("\nSkipping image processing")

    # Compile into single HTML document
    print("\nCompiling HTML document...")
    compiler = PDFCompiler(settings)

    # Extract just the section_data objects
    sections_list = [section_data for section_data, _ in all_section_data]

    html_document, generation_timestamp = compiler.compile_html_document(
        sections_list,
        document_config.get('metadata', {'title': document_name})
    )

    if save_html:
        html_path = output_dir / 'html' / output_filename.replace('.pdf', '.html')
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_document)
        print(f"  HTML saved to: {html_path}")

    # Generate PDF
    print("\nGenerating PDF...")
    output_path = output_dir / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    compiler.generate_pdf(html_document, str(output_path), generation_timestamp)

    print(f"✓ {document_name} complete!")
    print(f"  Output: {output_path.absolute()}")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Compile Digital NSW standards into separate PDF documents'
    )
    parser.add_argument(
        '--config',
        default='config/urls_config.json',
        help='Path to URL configuration file'
    )
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for PDFs'
    )
    parser.add_argument(
        '--save-html',
        action='store_true',
        help='Save intermediate HTML files'
    )
    parser.add_argument(
        '--section',
        help='Process only a specific section by name'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Digital NSW Standards PDF Compiler")
    print("=" * 60)

    # Load configuration
    print("\nLoading configuration...")
    url_config = load_url_config(args.config)
    sections = url_config['sections']

    # Filter sections if specific section requested
    if args.section:
        sections = [s for s in sections if s['section_name'] == args.section]
        if not sections:
            print(f"Error: Section '{args.section}' not found in configuration")
            sys.exit(1)

    print(f"  Loaded {len(sections)} section(s) to process")

    # Initialize scraper
    scraper = DigitalNSWScraper(settings)
    output_dir = Path(args.output_dir)

    # Process each section separately
    generated_pdfs = []
    for i, section_config in enumerate(sections, 1):
        print(f"\n\nSection {i}/{len(sections)}")
        try:
            pdf_path = process_section(
                section_config,
                scraper,
                settings,
                output_dir,
                args.save_html
            )
            if pdf_path:
                generated_pdfs.append(pdf_path)
        except Exception as e:
            print(f"  ✗ Error processing {section_config['section_name']}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n\n" + "=" * 60)
    print("✓ Compilation complete!")
    print(f"  Generated {len(generated_pdfs)} PDF(s):")
    for pdf_path in generated_pdfs:
        print(f"    - {pdf_path.name}")
    print(f"  Output directory: {output_dir.absolute()}")
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
