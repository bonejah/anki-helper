import hashlib
import os
from gtts import gTTS

def generate_tts_audio(text, lang):
    """Generates an MP3 file using Google Text-to-Speech."""
    if not text or not lang:
        return None
        
    try:
        # Create a unique filename based on the text hash
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        filename = f"tts_{lang}_{text_hash[:10]}.mp3"
        
        # Ensure the filename is absolute if needed, or just let it be current dir
        # For now, current dir is fine as it's what scrapers.py uses
        
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)
        
        if os.path.exists(filename):
            print(f"TTS generated: {filename}")
            return filename
            
        return None
    except Exception as e:
        print(f"Error generating TTS for '{text}' ({lang}): {e}")
        return None
