import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

try:
    with open("model_list.txt", "w") as f:
        for model in client.models.list():
            f.write(f"{model.name}\n")
    print("Models written to model_list.txt")
except Exception as e:
    with open("model_list.txt", "w") as f:
        f.write(f"Error: {str(e)}")
    print(f"Error: {e}")
