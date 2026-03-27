# 🌍 Anki Helper: Trilingual Dictionary & Standalone Desktop App

**Anki Helper** is a premium, trilingual translation tool (French 🇫🇷, English 🇺🇸, and Portuguese 🇧🇷) that transforms the way you learn languages. It combines the power of the **Collins Dictionary** with high-quality **Text-to-Speech (TTS)** and a standalone **macOS Application** to create perfect Anki flashcards with a single click.

![App Preview](https://github.com/bonejah/anki-helper/raw/main/static/screenshot_placeholder.png)

---

## ✨ Key Features

- **🍎 Standalone macOS App**: No terminal required! Launch directly from your Applications folder with a professional custom icon.
- **🔊 High-Quality Audio (TTS)**: 100% audio coverage. Uses **gTTS (Google Text-to-Speech)** to generate natural-sounding audio for full sentences and native recordings from Collins for dictionary words.
- **💎 Premium UI/UX**: Modern **Glassmorphism** interface with smooth animations, loading overlays, and dynamic status indicators.
- **🔗 Smart Anki Integration**: 
    - **Live Connection Status**: Automatically detects if Anki + AnkiConnect is running.
    - **Audio Generation Badge**: Visual confirmation in the UI when audio is ready for Anki.
- **🌍 Trilingual Core**: Simultaneous translation between French, English, and Portuguese with automatic language detection.
- **📚 Rich Context**: Fetches definitions, synonyms, and real-world example phrases directly into your Anki cards.

---

## 🚀 Getting Started

### 1. The Easy Way (macOS)
1. Ensure **Anki** is open with the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) plugin installed.
2. Download the latest version from the `dist/` folder.
3. Open **`Anki Helper.app`**.
4. Your browser will open automatically at `http://127.0.0.1:5000`.

### 2. Developer Mode (Manual)
1. **Clone the repo**: `git clone https://github.com/bonejah/anki-helper.git`
2. **Install deps**: `pip install -r requirements.txt`
3. **Run**: `python app.py`

---

## 🛠️ Build & Architecture

- **Backend**: Flask (Python 3.9+)
- **Packaging**: PyInstaller (for standalone Mac bundle)
- **Audio Engine**: gTTS & Collins Audio Scraper
- **I18n**: Fully localized in Portuguese, English, and French using **Flask-Babel**.

---

## 📝 Localization

If you want to contribute new translations:
```bash
# Extract strings
pybabel extract -F babel.cfg -o messages.pot .
# Update catalog
pybabel update -i messages.pot -d translations
# Compile
pybabel compile -d translations
```

---

## ⚖️ License & Credits
- **License**: MIT
- **Data Source**: [Collins Dictionary](https://www.collinsdictionary.com/)
- **Author**: Bonejah (Bruno Lima)

---

*Made with ❤️ for language learners who want a professional study workflow.*