import pyttsx3
import pythoncom

def speak(text):
    # Initialize COM for Windows background thread compatibility
    try:
        pythoncom.CoInitialize()
    except Exception:
        pass
        
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.setProperty("volume", 1.0)
    engine.say(text)
    engine.runAndWait()
