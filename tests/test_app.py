import pytest
from unittest.mock import patch, MagicMock

def test_home_page(client):
    """Test response of home page."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Anki Helper" in response.data or b"Trilingual" in response.data

def test_set_language_redirect(client):
    """Test switching UI language."""
    response = client.get("/set-language/fr", follow_redirects=True)
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess["ui_lang"] == "fr"

@patch("app.ensure_deck_exists")
def test_create_deck_route(mock_ensure, client):
    """Test direct deck creation route."""
    mock_ensure.return_value = True
    response = client.post("/create_deck", data={"new_deck": "TestDeck"}, follow_redirects=True)
    assert response.status_code == 200
    assert mock_ensure.called

@patch("app.check_anki_status")
@patch("app.get_anki_decks")
@patch("app.detect_language_safely")
@patch("app.translate_text")
@patch("app.fetch_collins_info")
@patch("app.ensure_deck_exists")
@patch("app.create_anki_card")
@patch("app.build_explanation_html_for_anki")
@patch("app.send_audio_to_anki")
def test_translation_flow(
    mock_send, 
    mock_build, 
    mock_create, 
    mock_ensure, 
    mock_fetch, 
    mock_trans, 
    mock_detect, 
    mock_decks, 
    mock_status,
    client
):
    """Smoke test of the main translation and card creation flow."""
    mock_status.return_value = True
    mock_decks.return_value = ["French"]
    mock_detect.return_value = "fr"
    mock_trans.return_value = [{"label": "Portuguese", "text": "Oi"}]
    mock_fetch.return_value = {"definitions": [{"text": "def"}], "audio_filename": None}
    mock_ensure.return_value = True
    mock_create.return_value = (True, "Card created!")
    mock_build.return_value = "<html>Explanation</html>"
    mock_send.return_value = None
    
    response = client.post("/", data={"text": "bonjour", "deck": "Auto Detect"})
    
    assert response.status_code == 200
    assert b"Card created!" in response.data
