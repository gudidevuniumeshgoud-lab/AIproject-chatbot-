from google import genai
import os
import json
import time
from dotenv import load_dotenv

print("✅ CLEAN brain.py loaded (google-genai SDK)")

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise Exception("GEMINI_API_KEY missing")

# Initialize the new GenAI Client
client = genai.Client(api_key=API_KEY)

HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

chat_history = load_history()

def clear_chat_history():
    global chat_history
    chat_history = []
    if os.path.exists(HISTORY_FILE):
        try:
            os.remove(HISTORY_FILE)
        except Exception as e:
            print(f"Error deleting history file: {e}")

def add_to_history(role, text):
    global chat_history
    chat_history.append({"role": role, "parts": [{"text": text}]})
    save_history(chat_history)

def get_gemini_response(user_query, system_instruction=None):
    global chat_history

    # Convert history format for the new SDK
    formatted_history = []
    for msg in chat_history:
        role = msg["role"]
        parts = msg["parts"]
        if len(parts) > 0 and isinstance(parts[0], dict) and "text" in parts[0]:
            text = parts[0]["text"]
        else:
            text = parts[0]
        
        role_map = {"model": "model", "assistant": "model", "user": "user"}
        final_role = role_map.get(role.lower(), "user")
        formatted_history.append({"role": final_role, "parts": [{"text": text}]})

    # List of models to try in order of preference
    models_to_try = [
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ]

    last_error = None
    for model_name in models_to_try:
        try:
            print(f"DEBUG: Trying model {model_name}...")
            
            # Setup config with system instruction if provided
            config = {}
            if system_instruction:
                config["system_instruction"] = system_instruction

            chat = client.chats.create(
                model=model_name,
                history=formatted_history,
                config=config
            )
            
            response = chat.send_message(user_query)
            reply = response.text or "No response"
            
            # Success!
            add_to_history("user", user_query)
            add_to_history("model", reply)
            return reply

        except Exception as e:
            error_msg = str(e)
            if any(code in error_msg for code in ["404", "not found", "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                print(f"DEBUG: {model_name} failed ({error_msg}), trying next model...")
                last_error = e
                continue
            else:
                raise e

    if last_error:
        raise last_error
    return "Error: No models available."

def export_chat_to_txt():
    global chat_history
    if not chat_history:
        return "No chat history to export."
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"chat_export_{timestamp}.txt"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== NEXUS AI CHAT EXPORT ===\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for msg in chat_history:
                role = "YOU" if msg["role"] == "user" else "NEXUS"
                text = msg["parts"][0]["text"]
                f.write(f"[{role}]: {text}\n\n")
        
        return f"Chat exported successfully to {filename}"
    except Exception as e:
        return f"Failed to export chat: {e}"

