import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# List available models
for model in genai.list_models():
    if "generateContent" in model.supported_generation_methods:
        print(f"Model: {model.name}, Methods: {model.supported_generation_methods}")