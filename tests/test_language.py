import pytest
from unittest.mock import patch, MagicMock
from core.language import detect_language_safely, translate_text
from langdetect import LangDetectException

@patch("core.language.detect_langs")
def test_detect_language_safely_fr(mock_detect):
    # Mock return value of detect_langs
    mock_lang = MagicMock()
    mock_lang.lang = "fr"
    mock_detect.return_value = [mock_lang]
    
    assert detect_language_safely("bonjour") == "fr"

@patch("core.language.detect_langs")
@patch("core.language.is_valid_french_word")
def test_detect_language_safely_fallback(mock_is_french, mock_detect):
    mock_detect.side_effect = LangDetectException(0, "failed")
    mock_is_french.return_value = True
    
    assert detect_language_safely("bonjour") == "fr"

@patch("core.language.fetch_collins_info")
@patch("core.language.Translator")
def test_translate_text(mock_translator, mock_collins):
    # Mock Collins to return nothing
    mock_collins.return_value = {"short_translations": []}
    
    # Mock Translator
    mock_instance = mock_translator.return_value
    mock_instance.translate.return_value.text = "Hello"
    
    # We expect translation from FR to EN and PT
    translations = translate_text("bonjour", "fr")
    
    assert len(translations) == 2
    assert any(t["label"] == "English" and t["text"] == "Hello" for t in translations)
    assert any(t["label"] == "Portuguese" and t["text"] == "Hello" for t in translations)
