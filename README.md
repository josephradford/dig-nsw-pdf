# Digital NSW Standards PDF Compiler

A Python tool that scrapes the Digital NSW website and compiles all delivery-related content into a single, well-structured PDF document with maintained hyperlinks and logical ordering.

## Features

- Scrapes all content from https://www.digital.nsw.gov.au/delivery
- Maintains internal hyperlinks between sections
- Preserves external links to resources
- Creates a professional table of contents
- Downloads and embeds images as base64
- Generates a professionally formatted PDF with NSW Government branding

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

Run with default configuration:
```bash
python main.py
```

This will:
1. Scrape all pages defined in `config/urls_config.json`
2. Process HTML and images
3. Generate `output/digital_nsw_standards.pdf`

### Advanced Options

```bash
# Specify custom configuration file
python main.py --config my_config.json

# Specify custom output path
python main.py --output my_output.pdf

# Save intermediate HTML file for debugging
python main.py --save-html
```

## Configuration

### URL Configuration

Edit `config/urls_config.json` to customize which pages to scrape:

```json
{
  "metadata": {
    "title": "Digital NSW Delivery Reference Guide",
    "author": "Your Name",
    "subject": "Digital Service Standards"
  },
  "sections": [
    {
      "section_name": "Section Name",
      "priority": 1,
      "pages": [
        {
          "title": "Page Title",
          "url": "https://www.digital.nsw.gov.au/...",
          "order": 1
        }
      ]
    }
  ]
}
```

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

1. **Scraping**: Fetches HTML content from configured URLs with polite delays
2. **Processing**: Cleans HTML, processes links, and handles images
3. **Compilation**: Combines all pages with a title page and table of contents
4. **PDF Generation**: Uses WeasyPrint to create a professional PDF with CSS styling

## Included Content

The default configuration scrapes:

- **Digital Service Toolkit**: Design standards, design system, resources
- **Delivery Manual**: All phases (pre-discovery through live and retiring)
- **Government Technology Platforms**: Platform documentation and FAQs
- **Accessibility and Inclusivity**: Toolkit and guidelines
- **Cyber Security**: Overview and resources
- **State Digital Assets**: Reusable components
- **NSW Automation Guide**: Automation lifecycle and maturity
- **Test and Buy Innovation**: Innovation procurement

## Troubleshooting

### WeasyPrint Installation Issues

If you encounter issues with WeasyPrint:

**macOS**:
```bash
brew install cairo pango gdk-pixbuf libffi
```

**Ubuntu/Debian**:
```bash
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
```

### Rate Limiting

If you're being rate-limited, increase `REQUEST_DELAY` in `config/settings.py`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is for educational and reference purposes. Content belongs to Digital NSW.

## Acknowledgments

- Digital NSW for providing comprehensive public documentation
- WeasyPrint for excellent HTML-to-PDF conversion
