from google import genai
from google.genai import types
import sys

API_KEY = "AIzaSyCgFOcQaYlgQ8eOQ3vyXhOpQo7IUiDgB9c"
client = genai.Client(api_key=API_KEY)

def test_gemini():
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Hello"
        )
        print(f"Success: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_gemini()
