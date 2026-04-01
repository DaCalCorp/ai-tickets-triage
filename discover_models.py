import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
# This is the "Yellow Pages" of the Google API
URL = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

print("🔍 Querying Google for available models...")
response = requests.get(URL)
data = response.json()

if "models" in data:
    print("\n✅ YOUR KEY HAS ACCESS TO THESE MODELS:")
    for m in data["models"]:
        # We only want models that support generating content
        if "generateContent" in m["supportedGenerationMethods"]:
            print(f" - {m['name']}")
else:
    print("❌ Error fetching models. Check your API Key.")
    print(data)
