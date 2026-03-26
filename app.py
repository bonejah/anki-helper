import base64
import os
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
from googletrans import Translator
from langdetect import LangDetectException, detect_langs

app = Flask(__name__)

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


def normalize_text(text: str) -> str:
    return (text or "").strip()


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

    normalized = (
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

    if lang == "en":
        return {
            "definitions": [],
            "locutions": [],
            "audio_filename": None,
            "fallback_text": f"Explicação detalhada ainda não implementada para {SUPPORTED_LANGS[lang]['label']}. Palavra consultada: {text}",
        }

    if lang == "pt":
        return {
            "definitions": [],
            "locutions": [],
            "audio_filename": None,
            "fallback_text": f"Explicação detalhada ainda não implementada para {SUPPORTED_LANGS[lang]['label']}. Palavra consultada: {text}",
        }

    return {
        "definitions": [],
        "locutions": [],
        "audio_filename": None,
        "fallback_text": "Definição não encontrada.",
    }


def build_explanation_text_for_anki(explanation_data):
    parts = []

    definitions = explanation_data.get("definitions", [])
    locutions = explanation_data.get("locutions", [])
    fallback_text = explanation_data.get("fallback_text")

    if definitions:
        parts.append("Definições:")
        parts.append("")

        for item in definitions:
            number = f"{item['number']}. " if item.get("number") else ""
            parts.append(f"{number}{item['text']}")

            if item.get("examples"):
                parts.append("Exemplos: " + " ; ".join(item["examples"]))

            if item.get("synonyms"):
                parts.append("Sinônimos: " + ", ".join(item["synonyms"]))

            parts.append("")

    if locutions:
        parts.append("Expressões / Locuções:")
        for loc in locutions:
            parts.append(f"{loc['title']}: {loc['text']}")

    if not parts and fallback_text:
        return fallback_text

    return "\n".join(parts).strip() or "Definição não encontrada."


def translate_text(text, src_lang):
    translator = Translator()

    if src_lang not in TRANSLATION_MAP:
        raise ValueError("Idioma não suportado.")

    translations = []

    for dest_lang, label in TRANSLATION_MAP[src_lang]:
        translated = translator.translate(text, src=src_lang, dest=dest_lang).text
        translations.append({
            "label": label,
            "text": translated,
        })

    return translations


def create_anki_card(text, translation_data, deck_name, detected_lang, explanation_text_for_anki, audio_tag_for_anki=""):
    translations_text = "\n\n".join(
        [f"{item['label']}: {item['text']}" for item in translation_data["translations"]]
    )

    payload = {
        "note": {
            "deckName": deck_name,
            "modelName": "Basic",
            "fields": {
                "Front": text,
                "Back": (
                    f"Idioma detectado: {SUPPORTED_LANGS[detected_lang]['label']}\n\n"
                    f"{translations_text}\n\n"
                    f"{audio_tag_for_anki}{explanation_text_for_anki}"
                ),
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
                "error_message": "Digite um texto antes de traduzir."
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
                "error_message": "Este app suporta apenas French, English e Portuguese."
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
        audio_tag_for_anki = f"[audio:{audio_file_safe}]\n" if audio_file_safe else ""

        try:
            translations = translate_text(text, detected_lang)
            explanation_text_for_anki = build_explanation_text_for_anki(explanation_data)

            translation_data = {
                "translations": translations,
                "detected_language": SUPPORTED_LANGS[detected_lang]["label"],
                "explanation_data": explanation_data,
            }

            if deck_ok:
                success, message = create_anki_card(
                    text=text,
                    translation_data=translation_data,
                    deck_name=selected_deck,
                    detected_lang=detected_lang,
                    explanation_text_for_anki=explanation_text_for_anki,
                    audio_tag_for_anki=audio_tag_for_anki,
                )

                if success:
                    translation_data["saved_message"] = message
                else:
                    translation_data["error_message"] = message
            else:
                translation_data["error_message"] = f"Não foi possível criar ou acessar o deck {selected_deck}."

        except Exception as e:
            translation_data = {
                "detected_language": SUPPORTED_LANGS[detected_lang]["label"],
                "error_message": f"Erro ao traduzir o texto: {e}",
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
        return "Nome do deck vazio", 400

    try:
        created = ensure_deck_exists(deck_name)

        if created:
            message = f"Deck {deck_name} criado com sucesso."
        else:
            message = f"Não foi possível criar o deck {deck_name}."

        return render_template(
            "index.html",
            decks=get_anki_decks(),
            translation_data={"saved_message": message} if created else {"error_message": message},
            original_text="",
            selected_deck=deck_name,
        )

    except Exception as e:
        return f"Erro ao criar deck: {e}", 500


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)