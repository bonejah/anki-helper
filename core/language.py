from googletrans import Translator
from langdetect import LangDetectException, detect_langs
from core.scrapers import (
    normalize_text, 
    fetch_collins_info, 
    is_valid_french_word
)

SUPPORTED_LANGS = {
    "fr": {"label": "French", "deck": "French"},
    "en": {"label": "English", "deck": "English"},
    "pt": {"label": "Portuguese", "deck": "Portuguese"}
}

TRANSLATION_MAP = {
    "fr": [("en", "English"), ("pt", "Portuguese")],
    "en": [("fr", "French"), ("pt", "Portuguese")],
    "pt": [("en", "English"), ("fr", "French")]
}

def detect_language_safely(text: str) -> str:
    if not text:
        return None
    try:
        langs = detect_langs(text)
        print('detected languages: ' + str(langs))
        if langs:
            for lang in langs:
                if lang.lang in SUPPORTED_LANGS:
                    return lang.lang
    except LangDetectException:
        pass

    if is_valid_french_word(text):
        return "fr"

    # Fallback to Google Translate for more robust detection (especially for broken sentences)
    try:
        translator = Translator()
        detection = translator.detect(text)
        print(f"Google detection: {detection.lang} (conf: {detection.confidence})")
        if detection.lang in SUPPORTED_LANGS:
            return detection.lang
    except Exception as e:
        print("Erro fallback detecção Google:", e)

    return None

def translate_text(text, src_lang):
    translator = Translator()
    if src_lang not in TRANSLATION_MAP:
        raise ValueError("Unsupported language.")

    is_short = len(text.split()) <= 3
    collins_info = fetch_collins_info(text, src_lang) if is_short else None
    collins_candidates = collins_info["short_translations"] if collins_info else []

    translations = []
    for dest_lang, label in TRANSLATION_MAP[src_lang]:
        translated_text = None
        if dest_lang == "en" and collins_candidates:
            translated_text = " / ".join(collins_candidates)

        if not translated_text:
            translated_text = translator.translate(text, src=src_lang, dest=dest_lang).text

        translations.append({
            "label": label,
            "text": translated_text,
        })
    return translations
