import base64
import os
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, session
from flask_babel import Babel, gettext as _
from googletrans import Translator
from langdetect import LangDetectException, detect_langs

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

# Flask-Babel config
LANGUAGES = {
    "pt": "Português",
    "en": "English",
    "fr": "Français",
}


def get_locale():
    lang = session.get("ui_lang")
    if lang in LANGUAGES:
        return lang
    return request.accept_languages.best_match(list(LANGUAGES.keys())) or "pt"


babel = Babel(app, locale_selector=get_locale)

ANKI_CONNECT_URL = "http://localhost:8765"

SUPPORTED_LANGS = {
    "fr": {
        "label": "French",
        "deck": "French",
        "dictionary": "larousse_fr",
    },
    "en": {
        "label": "English",
        "deck": "English",
        "dictionary": "basic_placeholder",
    },
    "pt": {
        "label": "Portuguese",
        "deck": "Portuguese",
        "dictionary": "basic_placeholder",
    },
}

SHORT_TEXT_HINTS = {
    "bonjour": "fr",
    "salut": "fr",
    "merci": "fr",
    "au revoir": "fr",
    "devoir": "fr",
    "hello": "en",
    "hi": "en",
    "thanks": "en",
    "thank you": "en",
    "book": "en",
    "olá": "pt",
    "ola": "pt",
    "oi": "pt",
    "obrigado": "pt",
    "obrigada": "pt",
    "como vai": "pt",
    "como voce vai": "pt",
}

TRANSLATION_MAP = {
    "fr": [("en", "English"), ("pt", "Portuguese")],
    "en": [("fr", "French"), ("pt", "Portuguese")],
    "pt": [("en", "English"), ("fr", "French")],
}


@app.context_processor
def inject_globals():
    return {
        "ui_languages": LANGUAGES,
        "current_ui_lang": get_locale(),
    }


def normalize_text(text: str) -> str:
    return (text or "").strip()


def normalize_for_hint(text: str) -> str:
    return (
        text.lower()
        .strip(" .,;:!?")
        .replace("á", "a")
        .replace("à", "a")
        .replace("â", "a")
        .replace("ã", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )


def invoke_anki(action, params=None):
    payload = {
        "action": action,
        "version": 6,
        "params": params or {},
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload, timeout=10)
    return response.json()


def detect_language_safely(text: str):
    text = normalize_text(text)

    if not text:
        return None

    normalized = normalize_for_hint(text)

    if len(text.split()) <= 3 and normalized in SHORT_TEXT_HINTS:
        lang = SHORT_TEXT_HINTS[normalized]
        print(f"Heurística aplicada para texto curto: {lang}")
        return lang

    try:
        candidates = detect_langs(text)
        print("Idiomas candidatos:", candidates)

        for candidate in candidates:
            if candidate.lang in SUPPORTED_LANGS and candidate.prob >= 0.70:
                print(f"Idioma detectado com confiança: {candidate.lang} ({candidate.prob:.2f})")
                return candidate.lang

        for candidate in candidates:
            if candidate.lang in SUPPORTED_LANGS:
                print(f"Idioma suportado com baixa confiança: {candidate.lang}")
                return candidate.lang

        print("Idioma detectado fora dos suportados.")
        return None

    except LangDetectException:
        print("Não foi possível detectar o idioma.")
        return None
    except Exception as e:
        print("Erro ao detectar idioma:", e)
        return None


def get_anki_decks():
    try:
        result = invoke_anki("deckNames")
        if result.get("error"):
            print("Erro ao buscar decks:", result["error"])
            return ["Auto Detect"]

        decks = result.get("result", [])
        decks = [deck for deck in decks if deck != "Default"]

        if "Auto Detect" not in decks:
            decks.insert(0, "Auto Detect")

        return decks

    except requests.exceptions.ConnectionError:
        print("Anki não está aberto.")
        return ["Auto Detect"]
    except Exception as e:
        print("Erro ao listar decks:", e)
        return ["Auto Detect"]


def ensure_deck_exists(deck_name: str) -> bool:
    try:
        result = invoke_anki("createDeck", {"deck": deck_name})
        if result.get("error"):
            print("Erro ao criar/verificar deck:", result["error"])
            return False
        return True

    except requests.exceptions.ConnectionError:
        print("Erro: Anki não está aberto.")
        return False
    except Exception as e:
        print("Erro ao garantir deck:", e)
        return False


def note_exists_in_deck(text: str, deck_name: str) -> bool:
    try:
        query = f'deck:"{deck_name}" Front:"{text}"'
        result = invoke_anki("findNotes", {"query": query})

        if result.get("error"):
            print("Erro ao buscar nota existente:", result["error"])
            return False

        return len(result.get("result", [])) > 0

    except Exception as e:
        print("Erro ao verificar duplicidade:", e)
        return False


def send_audio_to_anki(filename):
    if not filename or not os.path.exists(filename):
        return None

    safe_filename = filename.replace(" ", "_").replace(":", "_")

    try:
        with open(filename, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode("utf-8")

        result = invoke_anki(
            "storeMediaFile",
            {
                "filename": safe_filename,
                "data": audio_data,
            },
        )

        if result.get("error"):
            print("Erro ao enviar áudio para Anki:", result["error"])
            return None

        os.remove(filename)
        return safe_filename

    except Exception as e:
        print("Erro ao enviar áudio para Anki:", e)
        return None


def parse_larousse_with_audio(word, max_definitions=4, max_locutions=4):
    safe_word = quote(word)
    url = f"https://www.larousse.fr/dictionnaires/francais/{safe_word}"

    try:
        response = requests.get(url, allow_redirects=True, timeout=8)
        if response.status_code != 200:
            return {
                "definitions": [],
                "locutions": [],
                "audio_filename": None,
            }

        soup = BeautifulSoup(response.text, "html.parser")

        audio_filename = None
        audio_tag = soup.find("audio")
        if audio_tag and audio_tag.get("src"):
            audio_url = "https://www.larousse.fr" + audio_tag["src"]
            audio_filename = f"{word}.mp3"

            audio_response = requests.get(audio_url, timeout=8)
            if audio_response.status_code == 200:
                with open(audio_filename, "wb") as f:
                    f.write(audio_response.content)
            else:
                audio_filename = None

        result = {
            "definitions": [],
            "locutions": [],
            "audio_filename": audio_filename,
        }

        definitions_block = soup.find("article", class_="BlocDefinition")
        if definitions_block:
            items = definitions_block.find_all("li", class_="DivisionDefinition")[:max_definitions]

            for li in items:
                num_def_tag = li.find("span", class_="numDef")
                num_def = num_def_tag.get_text(strip=True) if num_def_tag else ""

                examples = [
                    ex.get_text(" ", strip=True)
                    for ex in li.find_all("span", class_="ExempleDefinition")
                ]

                synonyms = []
                for syn_block in li.find_all("p", class_="Synonymes"):
                    synonyms.extend(
                        [a.get_text(" ", strip=True) for a in syn_block.find_all("a")]
                    )

                li_clone = BeautifulSoup(str(li), "html.parser")
                li_root = li_clone.find("li")

                for tag in li_root.find_all("span", class_="ExempleDefinition"):
                    tag.decompose()

                for tag in li_root.find_all("p", class_="Synonymes"):
                    tag.decompose()

                for tag in li_root.find_all("span", class_="numDef"):
                    tag.decompose()

                definition_text = li_root.get_text(" ", strip=True)

                result["definitions"].append({
                    "number": num_def,
                    "text": definition_text,
                    "examples": examples,
                    "synonyms": synonyms,
                })

        locutions_block = soup.find("article", class_="BlocLocutions")
        if locutions_block:
            items = locutions_block.find_all("li", class_="Locution")[:max_locutions]

            for li in items:
                title_tag = li.find("h2", class_="AdresseLocution")
                text_tag = li.find("span", class_="TexteLocution")

                title = title_tag.get_text(" ", strip=True) if title_tag else ""
                text = text_tag.get_text(" ", strip=True) if text_tag else ""

                if title and text:
                    result["locutions"].append({
                        "title": title,
                        "text": text,
                    })

        return result

    except Exception as e:
        print("Erro ao buscar Larousse:", e)
        return {
            "definitions": [],
            "locutions": [],
            "audio_filename": None,
        }


def get_explanation_by_language(text, lang):
    if lang == "fr":
        return parse_larousse_with_audio(text)

    if lang in {"en", "pt"}:
        return {
            "definitions": [],
            "locutions": [],
            "audio_filename": None,
            "fallback_text": _(
                "Detailed explanation is not implemented yet for %(language)s. Queried word: %(word)s",
                language=SUPPORTED_LANGS[lang]["label"],
                word=text,
            ),
        }

    return {
        "definitions": [],
        "locutions": [],
        "audio_filename": None,
        "fallback_text": _("Definition not found."),
    }


def build_explanation_html_for_anki(explanation_data):
    definitions = explanation_data.get("definitions", [])
    locutions = explanation_data.get("locutions", [])
    fallback_text = explanation_data.get("fallback_text")

    html_parts = []

    if definitions:
        html_parts.append("<div><b>Definitions</b></div>")
        html_parts.append("<br>")

        for item in definitions:
            number = f"{item['number']}. " if item.get("number") else ""
            html_parts.append(f"<div><b>{number}</b>{item['text']}</div>")

            if item.get("examples"):
                examples_html = "".join(
                    [f"<li>{ex}</li>" for ex in item["examples"]]
                )
                html_parts.append(f"""
                    <div style="margin-top:6px;">
                        <b>Examples:</b>
                        <ul style="margin-top:4px;">{examples_html}</ul>
                    </div>
                """)

            if item.get("synonyms"):
                synonyms = ", ".join(item["synonyms"])
                html_parts.append(f"""
                    <div style="margin-top:6px;">
                        <b>Synonyms:</b> {synonyms}
                    </div>
                """)

            html_parts.append("<br>")

    if locutions:
        html_parts.append("<div style='margin-top:12px;'><b>Expressions / Locutions</b></div>")
        html_parts.append("<br>")

        for loc in locutions:
            html_parts.append(f"""
                <div style="margin-bottom:10px;">
                    <b>{loc['title']}</b><br>
                    {loc['text']}
                </div>
            """)

    if not html_parts and fallback_text:
        return f"<div>{fallback_text}</div>"

    return "".join(html_parts) or "<div>Definition not found.</div>"


def translate_text(text, src_lang):
    translator = Translator()

    if src_lang not in TRANSLATION_MAP:
        raise ValueError(_("Unsupported language."))

    translations = []

    for dest_lang, label in TRANSLATION_MAP[src_lang]:
        translated = translator.translate(text, src=src_lang, dest=dest_lang).text
        translations.append({
            "label": label,
            "text": translated,
        })

    return translations


def create_anki_card(text, translation_data, deck_name, detected_lang, explanation_html_for_anki, audio_tag_for_anki=""):
    translations_html = "".join([
        f"""
        <div style="margin-bottom:10px; padding:10px; border:1px solid #e5e7eb; border-radius:10px;">
            <b>{item['label']}:</b><br>
            {item['text']}
        </div>
        """
        for item in translation_data["translations"]
    ])

    back_html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.5; text-align: left;">
        <div style="margin-bottom:12px;">
            <b>Detected language:</b> {SUPPORTED_LANGS[detected_lang]['label']}
        </div>

        <div style="margin-bottom:16px;">
            {translations_html}
        </div>

        <div style="margin-bottom:16px;">
            {audio_tag_for_anki}
        </div>

        <div style="padding:14px; border:1px solid #e5e7eb; border-radius:12px; background:#fafafa;">
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

    try:
        if note_exists_in_deck(text, deck_name):
            message = f"Este card já existe no deck {deck_name}."
            print(message)
            return False, message

        result = invoke_anki("addNote", payload)

        if result.get("error"):
            error_msg = f"Erro ao criar card: {result['error']}"
            print(error_msg)
            return False, error_msg

        success_msg = f"Card criado com sucesso no deck {deck_name}."
        print(success_msg, "ID:", result.get("result"))
        return True, success_msg

    except requests.exceptions.ConnectionError:
        error_msg = "Erro: Anki não está aberto ou AnkiConnect não está rodando."
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Erro inesperado ao criar card: {e}"
        print(error_msg)
        return False, error_msg


@app.route("/set-language/<lang_code>")
def set_language(lang_code):
    if lang_code in LANGUAGES:
        session["ui_lang"] = lang_code
    return redirect(request.referrer or "/")


@app.route("/", methods=["GET", "POST"])
def home():
    translation_data = {}
    decks = get_anki_decks()

    text = ""
    selected_deck = "Auto Detect"

    if request.method == "POST":
        text = normalize_text(request.form.get("text", ""))
        deck_selected = request.form.get("deck", "Auto Detect")

        if not text:
            translation_data = {
                "error_message": _("Type some text before translating.")
            }
            return render_template(
                "index.html",
                translation_data=translation_data,
                decks=decks,
                original_text=text,
                selected_deck=deck_selected,
            )

        detected_lang = detect_language_safely(text)

        if not detected_lang:
            translation_data = {
                "error_message": _("This app only supports French, English and Portuguese.")
            }
            return render_template(
                "index.html",
                translation_data=translation_data,
                decks=decks,
                original_text=text,
                selected_deck=deck_selected,
            )

        if not deck_selected or deck_selected == "Auto Detect":
            selected_deck = SUPPORTED_LANGS[detected_lang]["deck"]
        else:
            selected_deck = deck_selected

        deck_ok = ensure_deck_exists(selected_deck)

        explanation_data = get_explanation_by_language(text, detected_lang)
        audio_file = explanation_data.get("audio_filename")
        audio_file_safe = send_audio_to_anki(audio_file)
        audio_tag_for_anki = f"[sound:{audio_file_safe}]\n" if audio_file_safe else ""

        try:
            translations = translate_text(text, detected_lang)
            explanation_html_for_anki = build_explanation_html_for_anki(explanation_data)

            translation_data = {
                "translations": translations,
                "detected_language": SUPPORTED_LANGS[detected_lang]["label"],
                "explanation_data": explanation_html_for_anki,
            }

            if deck_ok:
                success, message = create_anki_card(
                    text=text,
                    translation_data=translation_data,
                    deck_name=selected_deck,
                    detected_lang=detected_lang,
                    explanation_text_for_anki=explanation_html_for_anki,
                    audio_tag_for_anki=audio_tag_for_anki,
                )

                if success:
                    translation_data["saved_message"] = message
                else:
                    translation_data["error_message"] = message
            else:
                translation_data["error_message"] = _(
                    "Could not create or access the %(deck)s deck.",
                    deck=selected_deck,
                )

        except Exception as e:
            translation_data = {
                "detected_language": SUPPORTED_LANGS[detected_lang]["label"],
                "error_message": _("Error translating text: %(error)s", error=e),
            }

        decks = get_anki_decks()

    return render_template(
        "index.html",
        translation_data=translation_data,
        decks=decks,
        original_text=text,
        selected_deck=selected_deck,
    )


@app.route("/create_deck", methods=["POST"])
def create_deck():
    deck_name = normalize_text(request.form.get("new_deck"))

    if not deck_name:
        return _("Empty deck name"), 400

    try:
        created = ensure_deck_exists(deck_name)

        if created:
            message = _("Deck %(deck)s created successfully.", deck=deck_name)
        else:
            message = _("Could not create the %(deck)s deck.", deck=deck_name)

        return render_template(
            "index.html",
            decks=get_anki_decks(),
            translation_data={"saved_message": message} if created else {"error_message": message},
            original_text="",
            selected_deck=deck_name,
        )

    except Exception as e:
        return _("Error creating deck: %(error)s", error=e), 500


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
    