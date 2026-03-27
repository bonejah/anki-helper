import pytest
from core.formatter import build_explanation_html_for_anki

def test_build_explanation_html_full():
    data = {
        "definitions": [
            {
                "number": "1",
                "text": "Meaning 1",
                "examples": ["Ex 1"],
                "synonyms": ["Syn 1"]
            }
        ],
        "corpus_examples": ["Corpus 1"],
        "locutions": [{"title": "Loc 1", "text": "Loc text"}]
    }
    
    # Simple gettext mock
    def mock_gettext(s): return s
    
    html = build_explanation_html_for_anki(data, mock_gettext)
    
    # Check if key components are in the HTML
    assert "Meaning 1" in html
    assert "Ex 1" in html
    assert "Syn 1" in html
    assert "Corpus 1" in html
    assert "Loc 1" in html

def test_build_explanation_html_empty():
    def mock_gettext(s): return s
    html = build_explanation_html_for_anki({"definitions": []}, mock_gettext)
    assert "Definition not found." in html
