# Digital NSW Standards PDF Compiler

A Python tool that scrapes the Digital NSW website and compiles delivery-related content into separate, comprehensive PDF documents with full internal content and maintained hyperlinks.

## Features

- **Recursive Content Scraping**: Automatically follows and includes all internal links within each section
- **Separate PDFs per Section**: Generates individual PDFs for each major delivery area
- **Self-Contained Documents**: All linked content is included in the PDF - no external dependencies
- **Internal Link Preservation**: Links between pages work within the PDF itself
- **Automated GitHub Actions**: PDFs regenerate automatically when code is pushed
- **Professional Formatting**: Table of contents, NSW Government branding, and clean typography
- **Image Embedding**: Downloads and embeds all images as base64 for portability

## Installation

### Prerequisites

- Python 3.9 or higher
- macOS, Linux, or Windows

### Setup

1. Clone the repository:
```bash
git clone https://github.com/josephradford/dig-nsw-pdf.git
cd dig-nsw-pdf
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Generate all PDFs:
```bash
python main.py
```

This will:
1. Scrape all sections defined in `config/urls_config.json`
2. Recursively follow internal links within each section
3. Process HTML and images
4. Generate separate PDFs in the `output/` directory

### Advanced Options

```bash
# Generate a specific section only
python main.py --section "Digital Service Toolkit"

# Specify custom output directory
python main.py --output-dir my_output

# Save intermediate HTML files for debugging
python main.py --save-html

# Use custom configuration file
python main.py --config my_config.json
```

## Configuration

### URL Configuration

Edit `config/urls_config.json` to customize sections to scrape:

```json
{
  "sections": [
    {
      "section_name": "Digital Service Toolkit",
      "description": "Description of section",
      "base_path": "/delivery/digital-service-toolkit",
      "output_filename": "digital-service-toolkit.pdf",
      "max_depth": 3,
      "metadata": {
        "title": "Digital NSW - Digital Service Toolkit",
        "author": "Compiled from Digital NSW",
        "subject": "Digital Service Standards"
      },
      "pages": [
        {
          "title": "Starting Page",
          "url": "https://www.digital.nsw.gov.au/delivery/digital-service-toolkit",
          "order": 1
        }
      ]
    }
  ]
}
```

**Key Configuration Options:**
- `base_path`: Limits recursive scraping to URLs within this path
- `max_depth`: How many levels deep to follow links (default: 3)
- `output_filename`: Name of the generated PDF file

### Application Settings

Edit `config/settings.py` to customize behavior:

- `REQUEST_DELAY`: Delay between requests (default: 1.0 seconds)
- `DOWNLOAD_IMAGES`: Whether to download images (default: True)
- `EMBED_IMAGES_AS_BASE64`: Embed images in HTML (default: True)

## Project Structure

```
digital-nsw-pdf/
├── src/
│   ├── scraper.py           # Web scraping logic
│   ├── html_processor.py    # HTML cleaning and normalization
│   ├── image_handler.py     # Image downloading and processing
│   └── pdf_compiler.py      # PDF generation logic
├── config/
│   ├── urls_config.json     # URLs to scrape
│   └── settings.py          # Configuration settings
├── styles/
│   └── pdf_styles.css       # CSS for PDF output
├── output/
│   ├── html/                # Intermediate HTML files
│   ├── images/              # Downloaded images
│   └── digital_nsw_standards.pdf  # Final PDF output
├── main.py                  # Entry point script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## How It Works

1. **Recursive Scraping**: Starts from a root URL and follows all internal links within the section
2. **Link Discovery**: Extracts internal links from each page within the configured `base_path`
3. **Content Processing**: Cleans HTML, converts links to PDF anchors, and embeds images
4. **PDF Compilation**: Combines all discovered pages with a title page and table of contents
5. **PDF Generation**: Uses WeasyPrint to create professional PDFs with CSS styling

Each section is processed independently, creating self-contained PDF documents with all referenced content included.

## Generated PDFs

The default configuration generates 7 separate PDFs:

- **digital-service-toolkit.pdf**: Design standards, design system, delivery manual, resources, and all linked pages
- **government-technology-platforms.pdf**: Platform documentation, products, privacy, and FAQs
- **state-digital-assets.pdf**: Reusable components and assets
- **accessibility-and-inclusivity-toolkit.pdf**: Accessibility guidelines and resources
- **cyber-security.pdf**: Security guidance and resources
- **nsw-automation-guide.pdf**: Automation implementation guidance
- **test-and-buy-innovation.pdf**: Innovation procurement framework and journey

Each PDF includes ALL pages linked from the main section page, up to the configured depth limit.

## GitHub Actions Automation

The repository includes a GitHub Actions workflow that automatically regenerates PDFs when code is pushed to the main branch.

**Workflow features:**
- Triggers on push to main or manual dispatch
- Installs all system dependencies for WeasyPrint
- Generates all PDFs
- Commits updated PDFs back to the repository

The workflow is defined in `.github/workflows/generate-pdfs.yml`.

## Troubleshooting

### WeasyPrint Installation Issues

If you encounter issues with WeasyPrint:

**macOS**:
```bash
brew install cairo pango gdk-pixbuf libffi
```

**Ubuntu/Debian**:
```bash
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0
```

### Rate Limiting

If you're being rate-limited, increase `REQUEST_DELAY` in `config/settings.py`.

### Large PDF File Sizes

Some sections (like "Test and Buy Innovation") may generate large PDFs (20+ MB) due to extensive content and embedded images. This is expected behavior when all linked content is included.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is for educational and reference purposes. Content belongs to Digital NSW.

## Acknowledgments

- Digital NSW for providing comprehensive public documentation
- WeasyPrint for excellent HTML-to-PDF conversion
