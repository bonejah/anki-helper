import pytest
from unittest.mock import patch, MagicMock
from core.audio import generate_tts_audio, get_temp_audio_path
import os

@patch("core.audio.gTTS")
@patch("os.path.exists")
def test_generate_tts_audio(mock_exists, mock_gtts):
    mock_exists.return_value = True
    
    # Mocking gTTS instance
    mock_instance = mock_gtts.return_value
    mock_instance.save.return_value = None
    
    # Text and lang
    text = "bonjour"
    lang = "fr"
    
    result = generate_tts_audio(text, lang)
    
    assert result is not None
    assert "tts_fr_" in result
    assert result.endswith(".mp3")
    assert mock_instance.save.called

def test_get_temp_audio_path():
    path = get_temp_audio_path("test.mp3")
    assert "/test.mp3" in path
    # It should be absolute
    assert path.startswith("/")
