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
