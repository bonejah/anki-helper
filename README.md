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

## 🚀 How to Run the App

There are two ways to use **Anki Helper**, depending on your profile:

### 1. 🍎 Standalone Mode (Recommended for Users)
This is the easiest way to use the app without touching the terminal.
1.  Open the `dist/` folder in this repository.
2.  Double-click **`Anki Helper.app`**.
3.  The app will launch a background server and automatically open your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000).

### 2. 🛠️ Developer Mode (CLI)
Use this if you want to modify the code or see debug logs.
1.  **Install dependencies**: `pip install -r requirements.txt`
2.  **Run the server**:
    ```bash
    source .venv/bin/activate
    python app.py
    ```
3.  Access the app at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Testing

This project uses `pytest` for unit testing. To run the tests:

1.  **Install test dependencies**:
    ```bash
    pip install pytest pytest-mock
    ```
2.  **Run all tests**:
    ```bash
    pytest
    ```
    
The tests use mocks for external services (Anki, Google Translate, Collins Dictionary), so they can be run offline without actual AnkiConnect or internet connectivity.

---

## 🔩 Troubleshooting

### ⚠️ "Address already in use" (Port 5000)
On **macOS Monterey or newer**, the "AirPlay Receiver" service uses port 5000 by default. If you see this error when running the app:

**Solution A (Disable AirPlay Receiver):**
1.  Go to **System Settings** > **General** > **AirDrop & Handoff**.
2.  Turn off **AirPlay Receiver**.

**Solution B (Run on a different port):**
```bash
PORT=5001 python app.py
```

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