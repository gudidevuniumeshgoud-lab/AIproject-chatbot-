import os
import webbrowser
import subprocess
import time
from dotenv import load_dotenv

load_dotenv()

def get_browser():
    """
    Returns a browser controller. Prefers Chrome if path is provided in .env
    or if it can be found in common Windows locations.
    """
    chrome_path = os.getenv("CHROME_PATH")
    
    # Common Chrome paths on Windows if not in .env
    if not chrome_path or not os.path.exists(chrome_path):
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        for p in paths:
            if os.path.exists(p):
                chrome_path = p
                break
    
    if chrome_path and os.path.exists(chrome_path):
        # Register chrome
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
        return webbrowser.get('chrome')
    
    return webbrowser

def search_google(query: str):
    """
    Dynamically searches Google for any topic provided by the user.
    """
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    get_browser().open(url)
    return f"I have searched Google for: {query}"

def search_youtube(query: str):
    """
    Searches YouTube for videos related to the query.
    """
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    get_browser().open(url)
    return f"I have searched YouTube for: {query}"

def open_any_app(app_name: str):
    """
    Attempts to launch a local application or common website.
    """
    apps = {
        "chrome": os.getenv("CHROME_PATH", "chrome.exe"),
        "notepad": "notepad.exe",
        "vs code": "code",
        "calculator": "calc",
        "whatsapp": "https://web.whatsapp.com",
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "facebook": "https://www.facebook.com"
    }
    
    target = apps.get(app_name.lower())
    if target:
        if "http" in target:
            get_browser().open(target)
        else:
            try:
                if target.endswith(".exe") or "\\" in target:
                    os.startfile(target)
                else:
                    subprocess.Popen(target, shell=True)
            except:
                return f"Failed to open {app_name} locally."
        return f"Opening {app_name}..."
    
    # If not in predefined list, try opening as a website
    get_browser().open(f"https://www.google.com/search?q={app_name}&btnI") # I'm Feeling Lucky
    return f"Attempting to open {app_name}..."

def save_study_note(topic: str, content: str):
    """
    Saves important study notes or information to a local file for later review.
    """
    notes_dir = "study_notes"
    if not os.path.exists(notes_dir):
        os.makedirs(notes_dir)
    
    file_name = f"{topic.replace(' ', '_').lower()}.txt"
    file_path = os.path.join(notes_dir, file_name)
    
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- Note Taken: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(content + "\n")
        return f"Note about '{topic}' has been saved to {file_path}."
    except Exception as e:
        return f"Failed to save note: {e}"

def summarize_content(text: str):
    """
    Provides a concise summary of a long text or document content.
    """
    # This tool is more of a placeholder or hint for Gemini to use its internal summarizing capability,
    # but we can return a message.
    return f"I will now summarize the following content for you: {text[:100]}..."

# List for Gemini to understand its capabilities
tools_list = [search_google, search_youtube, open_any_app, save_study_note, summarize_content]