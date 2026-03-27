import pytest
from unittest.mock import patch, MagicMock
from core.anki_client import (
    check_anki_status,
    invoke_anki,
    get_anki_decks,
    ensure_deck_exists,
    note_exists_in_deck,
    send_audio_to_anki
)

@patch("requests.post")
def test_check_anki_status_success(mock_post):
    mock_post.return_value.status_code = 200
    assert check_anki_status() is True

@patch("requests.post")
def test_check_anki_status_failure(mock_post):
    mock_post.side_effect = Exception("Connection error")
    assert check_anki_status() is False

@patch("requests.post")
def test_invoke_anki(mock_post):
    mock_post.return_value.json.return_value = {"result": ["deck1"], "error": None}
    result = invoke_anki("deckNames")
    assert result["result"] == ["deck1"]
    assert mock_post.called

@patch("core.anki_client.invoke_anki")
def test_get_anki_decks(mock_invoke):
    mock_invoke.return_value = {"result": ["Default", "French"], "error": None}
    decks = get_anki_decks()
    assert "French" in decks
    assert "Auto Detect" in decks
    assert "Default" not in decks

@patch("core.anki_client.invoke_anki")
def test_ensure_deck_exists(mock_invoke):
    mock_invoke.return_value = {"result": None, "error": None}
    assert ensure_deck_exists("New Deck") is True

@patch("core.anki_client.invoke_anki")
def test_note_exists_in_deck(mock_invoke):
    mock_invoke.return_value = {"result": [12345], "error": None}
    assert note_exists_in_deck("bonjour", "French") is True
    
    mock_invoke.return_value = {"result": [], "error": None}
    assert note_exists_in_deck("unknown", "French") is False

@patch("os.path.exists")
@patch("os.remove")
@patch("core.anki_client.invoke_anki")
@patch("builtins.open", new_callable=MagicMock)
def test_send_audio_to_anki(mock_open, mock_invoke, mock_remove, mock_exists):
    mock_exists.return_value = True
    mock_invoke.return_value = {"result": "ok", "error": None}
    
    # Simulate reading file content
    mock_open.return_value.__enter__.return_value.read.return_value = b"fake audio data"
    
    result = send_audio_to_anki("fake_audio.mp3")
    assert result == "fake_audio.mp3"
    assert mock_remove.called
