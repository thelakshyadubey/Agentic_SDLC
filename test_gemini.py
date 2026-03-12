import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

models_to_test = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-2.0-flash"]
for model_name in models_to_test:
    try:
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=os.getenv("GEMINI_API_KEY"))
        result = llm.invoke("Say hi")
        print(f"✅ Success with {model_name}")
        break
    except Exception as e:
        print(f"❌ Failed with {model_name}: {e}")
