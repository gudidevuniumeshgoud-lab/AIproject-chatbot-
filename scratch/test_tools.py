from google import genai
from google.genai import types
import sys

API_KEY = "AIzaSyCgFOcQaYlgQ8eOQ3vyXhOpQo7IUiDgB9c"
client = genai.Client(api_key=API_KEY)

def search_google(query: str):
    return f"Searching Google for {query}"

def test_tools():
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Search for pizza",
            config=types.GenerateContentConfig(
                tools=[search_google]
            )
        )
        print(f"Success!")
        for part in response.candidates[0].content.parts:
            if part.function_call:
                print(f"Function Call: {part.function_call.name}")
            elif part.text:
                print(f"Text: {part.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_tools()
