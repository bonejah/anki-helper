import os
import sys
import base64
from flask import Flask, render_template, request, redirect, session, url_for
from flask_babel import Babel, gettext as _

from core.anki_client import (
    get_anki_decks,
    ensure_deck_exists,
    send_audio_to_anki,
    invoke_anki,
    note_exists_in_deck,
    check_anki_status
)
from core.language import (
    detect_language_safely, 
    translate_text,
    SUPPORTED_LANGS
)
from core.scrapers import normalize_text, fetch_collins_info, parse_larousse_with_audio
from core.formatter import build_explanation_html_for_anki
from core.audio import generate_tts_audio

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(
    __name__,
    template_folder=get_resource_path("templates"),
    static_folder=get_resource_path("static")
)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")
APP_VERSION = "1.3.5"

# ===============================
# I18N
# ===============================

LANGUAGES = {
    "pt": "Português",
    "en": "English",
    "fr": "Français",
}

def get_locale():
    lang = session.get("ui_lang")
    if lang in LANGUAGES:
        return lang
    return "pt"

babel = Babel(app, locale_selector=get_locale)

@app.context_processor
def inject_globals():
    return {
        "ui_languages": LANGUAGES,
        "current_ui_lang": get_locale(),
        "app_version": APP_VERSION,
        "anki_online": check_anki_status()
    }

# ===============================
# LOGIC HELPERS
# ===============================

def get_explanation_data(text, lang):
    info = fetch_collins_info(text, lang)
    if info and info.get("definitions"):
        return info

    # Fallback to Larousse for French
    if lang == "fr":
        print(f"Collins failed for '{text}', falling back to Larousse...")
        larousse_info = parse_larousse_with_audio(text)
        if larousse_info and larousse_info.get("definitions"):
            return {
                "definitions": larousse_info["definitions"],
                "locutions": larousse_info.get("locutions", []),
                "audio_filename": larousse_info.get("audio_filename"),
                "short_translations": [], # Not provided by Larousse scraper currently
                "corpus_examples": []
            }

    return {
        "definitions": [],
        "locutions": [],
        "audio_filename": None,
        "fallback_text": _("Definition not found."),
    }

def create_anki_card(
    text,
    translation_data,
    deck_name,
    detected_lang,
    explanation_html_for_anki,
    audio_tag_for_anki=""
):
    translations_html = "".join([
        f"""
        <div style="margin-bottom:10px; padding:12px; border:1px solid #e5e7eb; border-radius:12px; background:#ffffff;">
            <div style="font-size:13px; font-weight:700; color:#6b7280; text-transform:uppercase; margin-bottom:4px;">
                {item['label']}
            </div>
            <div style="font-size:16px; color:#1f2937;">
                {item['text']}
            </div>
        </div>
        """
        for item in translation_data["translations"]
    ])

    back_html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.5; text-align: left; color: #1f2937; padding: 6px;">
        <div style="margin-bottom:16px; padding:12px 14px; border-radius:12px; background:#eef2ff; border:1px solid #c7d2fe;">
            <strong>{_('Detected language')}:</strong> {SUPPORTED_LANGS[detected_lang]['label']}
        </div>

        <div style="margin-bottom:18px;">
            {translations_html}
        </div>

        {f'''
        <div style="margin-bottom:18px; padding:12px 14px; border-radius:12px; background:#f8fafc; border:1px solid #e5e7eb;">
            <div style="font-weight:700; margin-bottom:8px;">🔊 Audio</div>
            <div>{audio_tag_for_anki}</div>
        </div>
        ''' if audio_tag_for_anki else ''}

        <div style="padding:16px; border:1px solid #e5e7eb; border-radius:14px; background:#fafafa;">
            {explanation_html_for_anki}
        </div>
    </div>
    """

    payload = {
        "note": {
            "deckName": deck_name,
            "modelName": "Basic",
            "fields": {
                "Front": text,
                "Back": back_html,
            },
            "tags": ["auto-generated", f"lang-{detected_lang.lower()}"],
        }
    }

    if note_exists_in_deck(text, deck_name):
        return False, _("This card already exists in the %(deck)s deck.", deck=deck_name)

    result = invoke_anki("addNote", payload)
    if result.get("error"):
        return False, _("Error creating card: %(error)s", error=result["error"])

    return True, _("Card created successfully in the %(deck)s deck.", deck=deck_name)

# ===============================
# ROUTES
# ===============================

@app.route("/set-language/<lang_code>")
def set_language(lang_code):
    if lang_code in LANGUAGES:
        session["ui_lang"] = lang_code
    return redirect(request.referrer or "/")

def _handle_translation_post(decks):
    text = normalize_text(request.form.get("text", ""))
    print('text to be translated: ' + str(text))
    deck_selected = request.form.get("deck", "Auto Detect")

    if not text:
        translation_data = {"error_message": _("Type some text before translating.")}
        return render_template("index.html", translation_data=translation_data, decks=decks, original_text=text, selected_deck=deck_selected)

    detected_lang = detect_language_safely(text)

    if not detected_lang:
        translation_data = {"error_message": _("This app only supports French, English and Portuguese.")}
        return render_template("index.html", translation_data=translation_data, decks=decks, original_text=text, selected_deck=deck_selected)

    if not deck_selected or deck_selected == "Auto Detect":
        selected_deck = SUPPORTED_LANGS[detected_lang]["deck"]
    else:
        selected_deck = deck_selected

    deck_ok = ensure_deck_exists(selected_deck)
    explanation_data = get_explanation_data(text, detected_lang)
    
    audio_file = explanation_data.get("audio_filename")
    
    # NEW: Fallback to gTTS if no Collins audio is found (common for sentences)
    if not audio_file:
        audio_file = generate_tts_audio(text, detected_lang)

    audio_base64 = None
    if audio_file and os.path.exists(audio_file):
        with open(audio_file, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")

    audio_file_safe = send_audio_to_anki(audio_file)
    audio_tag_for_anki = f"[sound:{audio_file_safe}]" if audio_file_safe else ""

    translation_data = {}
    try:
        translations = translate_text(text, detected_lang)
        explanation_html = build_explanation_html_for_anki(explanation_data, _)

        translation_data = {
            "translations": translations,
            "detected_language": SUPPORTED_LANGS[detected_lang]["label"],
            "explanation_data": explanation_data,
            "has_audio": bool(audio_base64) or bool(audio_file_safe),
            "audio_base64": audio_base64,
        }

        if deck_ok:
            success, message = create_anki_card(
                text=text,
                translation_data=translation_data,
                deck_name=selected_deck,
                detected_lang=detected_lang,
                explanation_html_for_anki=explanation_html,
                audio_tag_for_anki=audio_tag_for_anki,
            )
            if success:
                translation_data["saved_message"] = message
            else:
                translation_data["error_message"] = message
        else:
            translation_data["error_message"] = _("Could not create or access the %(deck)s deck.", deck=selected_deck)

    except Exception as e:
        translation_data = {
            "detected_language": SUPPORTED_LANGS[detected_lang]["label"],
            "error_message": _("Error translating text: %(error)s", error=str(e)),
        }

    return render_template(
        "index.html",
        translation_data=translation_data,
        decks=decks,
        original_text=text,
        selected_deck=selected_deck,
    )

@app.route("/", methods=["GET", "POST"])
def home():
    decks = get_anki_decks()

    if request.method == "POST":
        return _handle_translation_post(decks)

    return render_template(
        "index.html",
        translation_data={},
        decks=decks,
        original_text="",
        selected_deck="Auto Detect",
    )

@app.route("/create_deck", methods=["POST"])
def create_deck():
    deck_name = request.form.get("new_deck", "").strip()
    if deck_name:
        ensure_deck_exists(deck_name)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5001)))