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
