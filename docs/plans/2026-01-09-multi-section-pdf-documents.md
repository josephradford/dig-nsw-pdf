# Multi-Section PDF Documents Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable config to define multi-section documents where multiple sections are combined into a single PDF with hierarchical structure

**Architecture:** Extend the existing config format to support a `documents` top-level key that groups multiple sections into one PDF. The PDF compiler already supports multiple sections - we just need main.py to detect and process document groups correctly.

**Tech Stack:** Python 3, existing PDFCompiler infrastructure

---

## Current vs New Config Structure

**Current (backward compatible):**
```json
{
  "sections": [
    {"section_name": "Foo", "output_filename": "foo.pdf", "pages": [...]}
  ]
}
```
Each section → separate PDF

**New (multi-section documents):**
```json
{
  "documents": [
    {
      "document_name": "NSW Design System",
      "output_filename": "nsw-design-system.pdf",
      "metadata": {...},
      "sections": [
        {"section_name": "About", "base_path": "/docs/content/about", ...},
        {"section_name": "Design", "base_path": "/docs/content/design", ...}
      ]
    }
  ],
  "sections": [...]  // Optional: standalone sections still work
}
```
Document with multiple sections → single PDF with hierarchical TOC

---

### Task 1: Create test for config parsing

**Files:**
- Create: `tests/test_config_parsing.py`

**Step 1: Write test for document config detection**

```python
import json
from pathlib import Path
import pytest

def test_detect_documents_config():
    """Test that we can detect documents vs sections in config"""
    config_with_documents = {
        "documents": [
            {
                "document_name": "Test Doc",
                "output_filename": "test.pdf",
                "sections": [
                    {"section_name": "Section 1"},
                    {"section_name": "Section 2"}
                ]
            }
        ]
    }

    config_with_sections = {
        "sections": [
            {"section_name": "Section 1"},
            {"section_name": "Section 2"}
        ]
    }

    # We'll implement these functions in main.py
    from main import has_documents, has_sections

    assert has_documents(config_with_documents) == True
    assert has_sections(config_with_documents) == False

    assert has_documents(config_with_sections) == False
    assert has_sections(config_with_sections) == True


def test_detect_mixed_config():
    """Test config with both documents and standalone sections"""
    config = {
        "documents": [{"document_name": "Doc1", "sections": []}],
        "sections": [{"section_name": "Standalone"}]
    }

    from main import has_documents, has_sections

    assert has_documents(config) == True
    assert has_sections(config) == True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config_parsing.py -v`

Expected output:
```
ImportError: cannot import name 'has_documents' from 'main'
```

**Step 3: Implement config detection functions in main.py**

Add to `main.py` after imports:

```python
def has_documents(config):
    """Check if config contains multi-section documents"""
    return 'documents' in config and len(config['documents']) > 0


def has_sections(config):
    """Check if config contains standalone sections"""
    return 'sections' in config and len(config['sections']) > 0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config_parsing.py::test_detect_documents_config -v`

Expected output:
```
test_config_parsing.py::test_detect_documents_config PASSED
```

**Step 5: Run mixed config test**

Run: `pytest tests/test_config_parsing.py::test_detect_mixed_config -v`

Expected output:
```
test_config_parsing.py::test_detect_mixed_config PASSED
```

**Step 6: Commit**

```bash
git add tests/test_config_parsing.py main.py
git commit -m "feat: add config detection for multi-section documents"
```

---

### Task 2: Add function to process multi-section documents

**Files:**
- Modify: `main.py`

**Step 1: Write test for document processing**

Add to `tests/test_config_parsing.py`:

```python
def test_process_document(tmp_path, monkeypatch):
    """Test that we can process a multi-section document"""
    from main import process_document
    from src.scraper import DigitalNSWScraper
    from config import settings

    # Mock document config
    document_config = {
        "document_name": "Test Document",
        "output_filename": "test-doc.pdf",
        "metadata": {
            "title": "Test Document",
            "author": "Test"
        },
        "sections": [
            {
                "section_name": "Section One",
                "base_url": "https://example.com",
                "base_path": "/section1",
                "pages": [{"title": "Page 1", "url": "https://example.com/section1/page1"}]
            },
            {
                "section_name": "Section Two",
                "base_url": "https://example.com",
                "base_path": "/section2",
                "pages": [{"title": "Page 2", "url": "https://example.com/section2/page2"}]
            }
        ]
    }

    # We need to mock the scraper to avoid real HTTP requests
    # For now, just test that the function exists and accepts the right params
    scraper = DigitalNSWScraper(settings)

    # This should not raise an error (even if it doesn't fully work without mocks)
    try:
        result = process_document(document_config, scraper, settings, tmp_path, save_html=False)
        # Result could be None if scraping fails, that's ok for this test
        assert result is None or isinstance(result, Path)
    except Exception as e:
        # Function should exist and have the right signature
        assert False, f"process_document failed with wrong signature: {e}"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config_parsing.py::test_process_document -v`

Expected output:
```
ImportError: cannot import name 'process_document' from 'main'
```

**Step 3: Implement process_document function**

Add to `main.py` before the `main()` function:

```python
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
                print(f"  ✗ Error processing page '{page['title']}': {e}")
                raise

        # Filter out None content
        section_data['pages'] = [p for p in section_data['pages'] if p['content'] is not None]

    print(f"  Processed {len(url_map)} total pages")

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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config_parsing.py::test_process_document -v`

Expected output:
```
test_config_parsing.py::test_process_document PASSED
```

**Step 5: Commit**

```bash
git add main.py tests/test_config_parsing.py
git commit -m "feat: add process_document for multi-section PDFs"
```

---

### Task 3: Update main() to handle documents

**Files:**
- Modify: `main.py` (main function)

**Step 1: Update main() to detect and process documents**

Replace the main loop in `main()` (lines 159-203) with:

```python
    # Load configuration
    print("\nLoading configuration...")
    url_config = load_url_config(args.config)

    # Determine what to process
    process_documents = has_documents(url_config)
    process_sections = has_sections(url_config)

    # Filter by --section argument if provided
    if args.section:
        if process_documents:
            # Filter documents that contain the specified section
            url_config['documents'] = [
                doc for doc in url_config.get('documents', [])
                if args.section in [s['section_name'] for s in doc['sections']]
            ]
        if process_sections:
            # Filter standalone sections
            url_config['sections'] = [
                s for s in url_config.get('sections', [])
                if s['section_name'] == args.section
            ]

        if (not url_config.get('documents') and not url_config.get('sections')):
            print(f"Error: Section '{args.section}' not found in configuration")
            sys.exit(1)

    total_items = len(url_config.get('documents', [])) + len(url_config.get('sections', []))
    print(f"  Loaded {total_items} item(s) to process")

    # Initialize scraper
    scraper = DigitalNSWScraper(settings)
    output_dir = Path(args.output_dir)

    generated_pdfs = []

    # Process multi-section documents
    if process_documents:
        for i, document_config in enumerate(url_config['documents'], 1):
            print(f"\n\nDocument {i}/{len(url_config['documents'])}")
            try:
                pdf_path = process_document(
                    document_config,
                    scraper,
                    settings,
                    output_dir,
                    args.save_html
                )
                if pdf_path:
                    generated_pdfs.append(pdf_path)
            except Exception as e:
                print(f"  ✗ Error processing {document_config['document_name']}: {e}")
                import traceback
                traceback.print_exc()

    # Process standalone sections
    if process_sections:
        for i, section_config in enumerate(url_config['sections'], 1):
            print(f"\n\nSection {i}/{len(url_config['sections'])}")
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
```

**Step 2: Test with existing config**

Run: `./venv/bin/python main.py --section "Digital Service Toolkit"`

Expected output:
```
Section 1/1
Processing: Digital Service Toolkit
...
✓ Compilation complete!
  Generated 1 PDF(s):
    - digital-service-toolkit.pdf
```

**Step 3: Verify backward compatibility**

The config should still work with the old format (sections only).

**Step 4: Commit**

```bash
git add main.py
git commit -m "feat: update main() to handle both documents and sections"
```

---

### Task 4: Create Design System config

**Files:**
- Modify: `config/urls_config.json`

**Step 1: Add Design System as multi-section document**

Add this to the config file (replace the existing single-section NSW Design System):

```json
{
  "documents": [
    {
      "document_name": "NSW Design System",
      "output_filename": "nsw-design-system.pdf",
      "metadata": {
        "title": "NSW Design System",
        "author": "Compiled from NSW Design System",
        "subject": "NSW Government Design System Documentation"
      },
      "sections": [
        {
          "section_name": "About",
          "base_url": "https://designsystem.nsw.gov.au",
          "base_path": "/docs/content/about",
          "max_depth": 2,
          "pages": [
            {
              "title": "What is Design System",
              "url": "https://designsystem.nsw.gov.au/docs/content/about/what-is-design-system.html",
              "order": 1
            }
          ]
        },
        {
          "section_name": "Design",
          "base_url": "https://designsystem.nsw.gov.au",
          "base_path": "/docs/content/design",
          "max_depth": 2,
          "pages": [
            {
              "title": "Getting Started",
              "url": "https://designsystem.nsw.gov.au/docs/content/design/getting-started.html",
              "order": 1
            }
          ]
        },
        {
          "section_name": "Develop",
          "base_url": "https://designsystem.nsw.gov.au",
          "base_path": "/docs/content/develop",
          "max_depth": 2,
          "pages": [
            {
              "title": "Getting Started",
              "url": "https://designsystem.nsw.gov.au/docs/content/develop/getting-started.html",
              "order": 1
            }
          ]
        },
        {
          "section_name": "Core Styles",
          "base_url": "https://designsystem.nsw.gov.au",
          "base_path": "/core",
          "max_depth": 1,
          "pages": [
            {
              "title": "Logo",
              "url": "https://designsystem.nsw.gov.au/core/logo/index.html",
              "order": 1
            }
          ]
        },
        {
          "section_name": "Components",
          "base_url": "https://designsystem.nsw.gov.au",
          "base_path": "/components",
          "max_depth": 1,
          "pages": [
            {
              "title": "Accordion",
              "url": "https://designsystem.nsw.gov.au/components/accordion/index.html",
              "order": 1
            }
          ]
        },
        {
          "section_name": "Utility Classes",
          "base_url": "https://designsystem.nsw.gov.au",
          "base_path": "/docs/content/utilities",
          "max_depth": 1,
          "pages": [
            {
              "title": "Background",
              "url": "https://designsystem.nsw.gov.au/docs/content/utilities/background.html",
              "order": 1
            }
          ]
        },
        {
          "section_name": "Methods",
          "base_url": "https://designsystem.nsw.gov.au",
          "base_path": "/docs/content/methods",
          "max_depth": 1,
          "pages": [
            {
              "title": "Search",
              "url": "https://designsystem.nsw.gov.au/docs/content/methods/search.html",
              "order": 1
            }
          ]
        },
        {
          "section_name": "Templates",
          "base_url": "https://designsystem.nsw.gov.au",
          "base_path": "/templates",
          "max_depth": 1,
          "pages": [
            {
              "title": "Templates",
              "url": "https://designsystem.nsw.gov.au/templates/index.html",
              "order": 1
            }
          ]
        },
        {
          "section_name": "Contribute",
          "base_url": "https://designsystem.nsw.gov.au",
          "base_path": "/docs/content/contribute",
          "max_depth": 2,
          "pages": [
            {
              "title": "Contribution Criteria",
              "url": "https://designsystem.nsw.gov.au/docs/content/contribute/contribution-criteria.html",
              "order": 1
            }
          ]
        }
      ]
    }
  ],
  "sections": [
    // ... existing Digital NSW sections remain here ...
  ]
}
```

**Step 2: Validate JSON syntax**

Run: `python -m json.tool config/urls_config.json > /dev/null`

Expected output: (no output means valid JSON)

**Step 3: Commit**

```bash
git add config/urls_config.json
git commit -m "feat: configure Design System as multi-section document"
```

---

### Task 5: Test Design System PDF generation

**Files:**
- None (testing only)

**Step 1: Generate Design System PDF**

Run: `./venv/bin/python main.py --config config/urls_config.json`

This will process the Design System document (with 9 sections) plus all the existing standalone sections.

Expected output:
```
Document 1/1
Processing Document: NSW Design System
  Contains 9 sections

[Section 1/9] About
  Scraping web pages...
  Scraped 4 pages
...
[Section 9/9] Contribute
  Scraping web pages...
  Scraped 3 pages

Processing HTML content for all sections...
  Processed XX total pages

✓ Compilation complete!
  Generated 8 PDF(s):
    - nsw-design-system.pdf
    - digital-service-toolkit.pdf
    - ...
```

**Step 2: Verify PDF structure**

Run:
```bash
./venv/bin/python -c "
import PyPDF2
with open('output/nsw-design-system.pdf', 'rb') as f:
    pdf = PyPDF2.PdfReader(f)
    print(f'Total pages: {len(pdf.pages)}')
    print(f'Outline (first 20 items):')
    outlines = pdf.outline[:20] if hasattr(pdf, 'outline') else []
    for item in outlines:
        if hasattr(item, 'title'):
            print(f'  - {item.title}')
"
```

Expected: Should see the 9 section names (About, Design, Develop, etc.) in the outline.

**Step 3: Manual verification**

Open `output/nsw-design-system.pdf` and verify:
- ✓ Table of contents shows 9 top-level sections
- ✓ Each section has correct sub-pages
- ✓ Bookmarks match the TOC structure
- ✓ Internal links work

**Step 4: Test filtering by section name**

Run: `./venv/bin/python main.py --section "Components"`

Expected output:
```
Document 1/1
Processing Document: NSW Design System
  Contains 1 sections

[Section 1/1] Components
...
```

This should generate only the Design System PDF with only the Components section.

---

### Task 6: Final integration test

**Files:**
- None (testing only)

**Step 1: Test complete config with all sections**

Run: `./venv/bin/python main.py`

Expected: Generates 8 PDFs (1 Design System document + 7 standalone Digital NSW sections)

**Step 2: Verify backward compatibility**

Temporarily rename the documents array to test sections-only mode:

```bash
# Backup config
cp config/urls_config.json config/urls_config.json.bak

# Edit to remove documents (use your editor)
# Just keep the "sections" array

# Run
./venv/bin/python main.py

# Restore
mv config/urls_config.json.bak config/urls_config.json
```

Expected: Should still work with sections-only config.

**Step 3: Commit final changes**

```bash
git add -A
git commit -m "test: verify multi-section document implementation"
```

---

## Success Criteria

- ✓ Config supports both `documents` (multi-section) and `sections` (standalone)
- ✓ Design System PDF has 9 top-level sections matching website navigation
- ✓ TOC and bookmarks show hierarchical structure
- ✓ Backward compatibility: existing configs still work
- ✓ `--section` filter works for both documents and standalone sections
- ✓ All existing 7 Digital NSW PDFs still generate correctly

## Testing Strategy

1. Unit tests for config detection (Task 1)
2. Integration test for process_document function (Task 2)
3. Manual testing with real Design System website (Task 5)
4. Backward compatibility verification (Task 6)

## Rollback Plan

If issues arise:
1. Git revert to before multi-section changes
2. Restore old single-section Design System config
3. Debug issues in separate branch
