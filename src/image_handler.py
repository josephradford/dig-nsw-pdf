import requests
import base64
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ImageHandler:
    """
    Handle image downloading and embedding for PDF generation
    """

    def __init__(self, config):
        self.config = config
        self.download_images = config.DOWNLOAD_IMAGES
        self.embed_as_base64 = config.EMBED_IMAGES_AS_BASE64
        self.image_cache = {}

    def download_image(self, url):
        """Download image from URL"""
        try:
            # Check cache first
            if url in self.image_cache:
                return self.image_cache[url]

            logger.info(f"Downloading image: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            img_data = response.content
            self.image_cache[url] = img_data
            return img_data

        except Exception as e:
            logger.error(f"Failed to download image {url}: {e}")
            return None

    def detect_mime_type(self, img_data):
        """Detect MIME type from image data"""
        # Check magic bytes for common formats
        if img_data[:2] == b'\xff\xd8':
            return 'image/jpeg'
        elif img_data[:8] == b'\x89PNG\r\n\x1a\n':
            return 'image/png'
        elif img_data[:6] in (b'GIF87a', b'GIF89a'):
            return 'image/gif'
        elif img_data[:4] == b'RIFF' and img_data[8:12] == b'WEBP':
            return 'image/webp'
        elif img_data[:2] in (b'II', b'MM'):
            return 'image/tiff'
        else:
            # Default fallback
            return 'image/png'

    def process_images(self, soup, output_dir=None):
        """
        Process all images in the HTML soup
        Options:
        1. Download images locally and reference in PDF
        2. Convert images to base64 data URIs (embed in HTML)
        3. Leave as external URLs (may fail in PDF)

        Using Option 2 (base64) for portability
        """
        if not self.download_images:
            return soup

        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue

            # Convert relative URLs to absolute
            if not src.startswith(('http://', 'https://', 'data:')):
                src = urljoin('https://www.digital.nsw.gov.au', src)
                img['src'] = src

            # Skip if already a data URI
            if src.startswith('data:'):
                continue

            if self.embed_as_base64:
                # Download and embed as base64
                img_data = self.download_image(src)
                if img_data:
                    # Convert to base64
                    base64_data = base64.b64encode(img_data).decode()
                    mime_type = self.detect_mime_type(img_data)

                    # Update src to data URI
                    img['src'] = f"data:{mime_type};base64,{base64_data}"
            else:
                # Keep as absolute URL
                img['src'] = src

        return soup
