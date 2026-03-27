import pytest
from unittest.mock import patch, MagicMock
from core.scrapers import fetch_collins_info, normalize_text, is_valid_french_word

def test_normalize_text():
    assert normalize_text("  bonjour  ") == "bonjour"
    assert normalize_text(None) == ""

@patch("cloudscraper.create_scraper")
def test_fetch_collins_info_fr(mock_create):
    mock_scraper = mock_create.return_value
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Minimal HTML that BeautifulSoup can parse
    mock_response.text = """
    <html>
        <a class="hwd_sound" data-src-mp3="http://example.com/audio.mp3"></a>
        <div class="sense">
            <span class="def">Definition text</span>
            <span class="exam">Example text</span>
        </div>
    </html>
    """
    mock_scraper.get.return_value = mock_response
    
    # Also mock the audio download
    mock_audio_res = MagicMock()
    mock_audio_res.status_code = 404 # Skip audio download for now
    mock_scraper.get.side_effect = [mock_response, mock_audio_res]
    
    result = fetch_collins_info("bonjour", "fr")
    
    assert result is not None
    assert len(result["definitions"]) > 0
    assert result["definitions"][0]["text"] == "Definition text"
    assert "Example text" in result["definitions"][0]["examples"]

@patch("core.scrapers.fetch_collins_info")
def test_is_valid_french_word(mock_fetch):
    mock_fetch.return_value = {"definitions": [{"text": "def"}]}
    assert is_valid_french_word("bonjour") is True
    
    mock_fetch.return_value = {"definitions": []}
    assert is_valid_french_word("invalid") is False
