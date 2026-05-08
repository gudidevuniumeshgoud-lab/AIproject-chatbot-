import subprocess
from tools import get_browser

def handle_automation(command):
    command = command.lower().strip()
    browser = get_browser()

    # Specialized Searches
    if "search on youtube for" in command or "search youtube for" in command:
        query = command.split("for")[-1].strip()
        browser.open(f"https://www.youtube.com/results?search_query={query}")
        return f"Searching YouTube for {query}"

    if "search on google for" in command or "search google for" in command:
        query = command.split("for")[-1].strip()
        browser.open(f"https://www.google.com/search?q={query}")
        return f"Searching Google for {query}"

    # Handle combined "Open X and search for Y"
    if "open youtube and search for" in command:
        query = command.split("search for")[-1].strip()
        browser.open(f"https://www.youtube.com/results?search_query={query}")
        return f"Opening YouTube and searching for {query}"

    if "open google and search for" in command:
        query = command.split("search for")[-1].strip()
        browser.open(f"https://www.google.com/search?q={query}")
        return f"Opening Google and searching for {query}"

    # Multiple commands (general splitting)
    if " and " in command and not any(x in command for x in ["search for", "search youtube", "search google"]):
        parts = command.split(" and ")
        results = []
        for p in parts:
            res = handle_automation(p)
            if res: results.append(res)
        return " | ".join(results) if results else None

    # Apps
    if "notepad" in command:
        subprocess.Popen("notepad")
        return "Opening Notepad."

    if "calculator" in command:
        subprocess.Popen("calc")
        return "Opening Calculator."

    if "cmd" in command or "command prompt" in command:
        subprocess.Popen("cmd")
        return "Opening Command Prompt."

    # General Search
    if "search for" in command:
        query = command.split("search for")[-1].strip()
        browser.open(f"https://www.google.com/search?q={query}")
        return f"Searching for {query}"

    # Open website
    if command.startswith("open "):
        site = command.replace("open ", "").strip()
        if "." not in site:
            url = f"https://www.{site}.com"
        else:
            url = f"https://{site}"

        browser.open(url)
        return f"Opening {site}"

    return None
