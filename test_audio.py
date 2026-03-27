from core.audio import generate_tts_audio
import os

def test_audio(text, lang):
    print(f"\n--- Testing: '{text}' ({lang}) ---")
    filename = generate_tts_audio(text, lang)
    if filename and os.path.exists(filename):
        print(f"Success! Created: {filename}")
        os.remove(filename)
    else:
        print("Failed to generate audio.")

test_audio("Je mange muito", "fr")
test_audio("I am going to the store", "en")
test_audio("Eu gosto de programar", "pt")
