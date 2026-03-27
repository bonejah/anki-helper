import hashlib
import os
import tempfile
from gtts import gTTS

def get_temp_audio_path(filename):
    """Returns an absolute path in the system temp directory."""
    return os.path.join(tempfile.gettempdir(), filename)

def generate_tts_audio(text, lang):
    """Generates an MP3 file using Google Text-to-Speech."""
    if not text or not lang:
        return None
        
    try:
        # Create a unique filename based on the text hash
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        filename = f"tts_{lang}_{text_hash[:10]}.mp3"
        # Ensure the filename is absolute in a writable temp directory
        temp_path = get_temp_audio_path(filename)
        
        tts = gTTS(text=text, lang=lang)
        tts.save(temp_path)
        
        if os.path.exists(temp_path):
            print(f"TTS generated at: {temp_path}")
            return temp_path
            
        return None
    except Exception as e:
        print(f"Error generating TTS for '{text}' ({lang}): {e}")
        return None
