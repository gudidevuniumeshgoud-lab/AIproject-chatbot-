import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

try:
    for model in client.models.list():
        print(f"Model: {model.name}, Supported: {model.supported_generation_methods}")
except Exception as e:
    print(f"Error: {e}")
