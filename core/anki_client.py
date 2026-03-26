import base64
import os
import requests

ANKI_CONNECT_URL = "http://localhost:8765"

def invoke_anki(action, params=None):
    payload = {
        "action": action,
        "version": 6,
        "params": params or {},
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload, timeout=10)
    return response.json()

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
    print('filename: ' + str(filename))
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
