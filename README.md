# 🌍 Anki Helper: Trilingual Dictionary & Flashcard Creator

**Anki Helper** is a premium web application designed to accelerate language learning (French, English, and Portuguese). It seamlessly integrates with the **Collins Dictionary** to provide accurate definitions, native audio, and real-world example phrases, all while allowing you to create high-quality Anki flashcards with a single click.

---

## ✨ Key Features

- **Trilingual Support**: Seamless translation and language detection between **French (🇫🇷)**, **English (🇺🇸)**, and **Portuguese (🇧🇷)**.
- **Collins Dictionary Integration**: Fetches detailed definitions, synonyms, and "Example sentences from the Collins Corpus" for natural usage.
- **One-Click Anki Cards**: Automatically creates formatted Anki cards with:
    - Target word and translations.
    - Native audio (MP3) automatically attached.
    - Detailed definitions and example phrases.
- **Premium UI/UX**: Modern interface featuring **Glassmorphism**, smooth staggered animations, and a dynamic loading system.
- **Robust Detection**: Intelligent language detection with a Google Translate fallback for broken or ambiguous sentences.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Anki** (Desktop version)
- **AnkiConnect Plugin**: Install the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on in Anki to enable the integration.

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/bonejah/anki-helper.git
   cd anki-helper
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # .venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

1. Ensure **Anki** is open on your computer.
2. Start the Flask server:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🌍 Localization & Translations (Babel)

The app is localized using Flask-Babel. If you add new strings to the code, use these commands to update translations:

```bash
# 1. Extract new strings
pybabel extract -F babel.cfg -o messages.pot .

# 2. Update existing translation files
pybabel update -i messages.pot -d translations

# 3. (Optional) Edit the .po files in translations/ to add your translations

# 4. Compile translations
pybabel compile -d translations
```

---

## 🛠️ Built With

- **Flask**: Web backend.
- **BeautifulSoup4 & CloudScraper**: Advanced web scraping for dictionary data.
- **Googletrans**: Multi-language translation and robust detection.
- **AnkiConnect**: API integration with Anki.
- **CSS3 (Advanced)**: Glassmorphism and premium animations.

---

## 📝 License

This project is for educational purposes. All dictionary data belongs to [Collins Dictionary](https://www.collinsdictionary.com/).

---

*Made with ❤️ for language learners.*