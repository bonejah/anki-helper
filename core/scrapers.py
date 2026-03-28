import re
import requests
import cloudscraper
from urllib.parse import quote
from bs4 import BeautifulSoup
import tempfile
import os

def get_temp_audio_path(filename):
    """Returns an absolute path in the system temp directory."""
    return os.path.join(tempfile.gettempdir(), filename)

def normalize_text(text: str) -> str:
    return (text or "").strip()

def fetch_collins_info(word: str, src_lang: str):
    """
    Fetches comprehensive information from Collins Dictionary.
    Supports French-English, Portuguese-English, and English (monolingual).
    """
    word = normalize_text(word)
    if not word:
        return {
            "definitions": [],
            "examples": [],
            "locutions": [],
            "audio_filename": None,
            "short_translations": [],
            "corpus_examples": []
        }

    url_map = {
        "fr": f"https://www.collinsdictionary.com/dictionary/french-english/{quote(word.replace(' ', '-'))}",
        "pt": f"https://www.collinsdictionary.com/dictionary/portuguese-english/{quote(word.replace(' ', '-'))}",
        "en": f"https://www.collinsdictionary.com/dictionary/english/{quote(word.replace(' ', '-'))}",
    }

    if src_lang not in url_map:
        return None

    try:
        url = url_map[src_lang]
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'darwin',
                'desktop': True
            }
        )
        response = scraper.get(
            url,
            timeout=10,
        )

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Check for Cloudflare challenge (even if 200, it might be a challenge page)
        if "Just a moment..." in soup.title.string if soup.title else False:
            print("Collins Cloudflare challenge detected.")
            return None

        # Audio extraction
        audio_filename = None
        audio_tag = soup.find("a", class_="hwd_sound")
        if not audio_tag:
            audio_tag = soup.find("a", class_="ref")
            
        if audio_tag:
            audio_url = audio_tag.get("data-src-mp3") or audio_tag.get("src")
            if audio_url:
                # Ensure absolute URL
                if audio_url.startswith("//"):
                    audio_url = "https:" + audio_url
                elif audio_url.startswith("/"):
                    audio_url = "https://www.collinsdictionary.com" + audio_url
                    
                audio_filename = f"collins_{src_lang}_{word.replace(' ', '_')}.mp3"
                temp_path = get_temp_audio_path(audio_filename)
                try:
                    audio_res = scraper.get(
                        audio_url,
                        timeout=5,
                    )
                    if audio_res.status_code == 200:
                        with open(temp_path, "wb") as f:
                            f.write(audio_res.content)
                        print(f"Áudio Collins salvo em: {temp_path}")
                        audio_filename = temp_path # Return the absolute path
                    else:
                        print(f"Erro ao baixar áudio Collins (status {audio_res.status_code}): {audio_url}")
                        audio_filename = None
                except Exception as e:
                    print("Erro ao baixar áudio Collins:", e)
                    audio_filename = None

        # Extract definitions and examples
        definitions = []
        
        # Collins structure varies between dictionaries (French-English, English-English/COBUILD, etc.)
        senses = soup.select(".hom .sense, .dictentry .sense, .cobuild .sense, .sense")
        
        for sense in senses[:5]:
            # Definition
            def_tag = sense.select_one(".def")
            meaning_tag = sense.select_one(".cit.type-translation") # For bilingual
            
            def_text = ""
            if def_tag:
                def_text = def_tag.get_text(" ", strip=True)
            elif meaning_tag:
                def_text = meaning_tag.get_text(" ", strip=True)
            
            # Examples
            examples = []
            for ex in sense.select(".exam"):
                examples.append(ex.get_text(" ", strip=True))
            
            if def_text:
                definitions.append({
                    "number": len(definitions) + 1,
                    "text": def_text,
                    "examples": examples
                })

        # Better short translations: extract from main senses instead of whole page
        short_translations = []
        for d in definitions:
            if d.get("text") and len(short_translations) < 4:
                # Basic cleaning to avoid long explanations in short_translations
                clean_trans = d["text"].split(";")[0].split(",")[0].strip()
                if clean_trans and clean_trans not in short_translations:
                    short_translations.append(clean_trans)

        # Corpus Examples extraction
        corpus_examples = []
        for ex_tag in soup.select(".type-example .quote")[:5]:
            ex_text = ex_tag.get_text(" ", strip=True)
            if ex_text and ex_text not in corpus_examples:
                corpus_examples.append(ex_text)

        return {
            "definitions": definitions,
            "locutions": [], # Can expand later
            "audio_filename": audio_filename,
            "short_translations": short_translations,
            "corpus_examples": corpus_examples
        }

    except Exception as e:
        print("Erro ao consultar Collins:", e)
        return None

def is_valid_french_word(word: str) -> bool:
    """Fallback check for French words using Collins or Larousse."""
    # We can stick to Collins if the user prefers
    info = fetch_collins_info(word, "fr")
    return info is not None and len(info["definitions"]) > 0

# Keeping Larousse for reference or if the user specifically needs it later, 
# but switching default focus to Collins as requested.
def parse_larousse_with_audio(word, max_definitions=4, max_locutions=4):
    safe_word = quote(word)
    url = f"https://www.larousse.fr/dictionnaires/francais/{safe_word}"

    try:
        response = requests.get(url, allow_redirects=True, timeout=8)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        audio_filename = None
        audio_tag = soup.find("audio")
        if audio_tag and audio_tag.get("src"):
            audio_url = "https://www.larousse.fr" + audio_tag["src"]
            audio_filename = f"larousse_{word}.mp3"
            temp_path = get_temp_audio_path(audio_filename)

            audio_response = requests.get(audio_url, timeout=8)
            if audio_response.status_code == 200:
                with open(temp_path, "wb") as f:
                    f.write(audio_response.content)
                audio_filename = temp_path # Return the absolute path
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
                examples = [ex.get_text(" ", strip=True) for ex in li.find_all("span", class_="ExempleDefinition")]
                
                li_clone = BeautifulSoup(str(li), "html.parser")
                li_root = li_clone.find("li")
                for tag in li_root.find_all(["span", "p"], class_=["ExempleDefinition", "Synonymes", "numDef"]):
                    tag.decompose()

                result["definitions"].append({
                    "number": num_def,
                    "text": li_root.get_text(" ", strip=True),
                    "examples": examples
                })

        return result
    except Exception as e:
        print("Erro ao buscar Larousse:", e)
        return None
