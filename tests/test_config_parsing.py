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
