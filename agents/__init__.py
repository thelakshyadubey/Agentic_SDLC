import os
import json
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

class DualLLM:
    def __init__(self, models):
        self.models = models
        self.current_idx = 0
        self.total_calls = 0

    def invoke(self, prompt, **kwargs):
        # Determine the primary and fallback models based on round-robin
        primary_model = self.models[self.current_idx]
        fallback_model = self.models[(self.current_idx + 1) % len(self.models)]
        
        # Advance the index for the next call
        self.current_idx = (self.current_idx + 1) % len(self.models)
        self.total_calls += 1
        
        print("\n" + "="*50)
        print(f"🤖 DualLLM Call #{self.total_calls} Started")
        print(f"🔄 Primary Model Assigned: {primary_model.__class__.__name__} ({getattr(primary_model, 'model_name', getattr(primary_model, 'model', 'unknown'))})")
        print(f"📝 Prompt Preview (first 100 chars):")
        
        # safely extract prompt text for preview
        prompt_text = str(prompt[0].content) if isinstance(prompt, list) and len(prompt)>0 else str(prompt)
        print(f"   {prompt_text[:100]}...")
        print("-" * 50)
        
        try:
            print(f"⏳ Executing primary model...")
            response = primary_model.invoke(prompt, **kwargs)
            print(f"✅ Success with primary model!")
            print("="*50 + "\n")
            return response
            
        except Exception as e:
            print(f"⚠️ Primary model failed: {str(e)}")
            print(f"🔄 Falling back to: {fallback_model.__class__.__name__} ({getattr(fallback_model, 'model_name', getattr(fallback_model, 'model', 'unknown'))})")
            
            try:
                print(f"⏳ Executing fallback model...")
                response = fallback_model.invoke(prompt, **kwargs)
                print(f"✅ Success with fallback model!")
                print("="*50 + "\n")
                return response
            except Exception as inner_e:
                print(f"❌ FATAL: Both models failed. Fallback error: {str(inner_e)}")
                print("="*50 + "\n")
                raise inner_e

# Heavy models — used for BA, Architect, PM, Dev (complex reasoning)
heavy_models = [
    ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3, api_key=os.getenv("GROQ_API_KEY")),
    ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3, google_api_key=os.getenv("GEMINI_API_KEY"))
]

# Light models — used for QA (simple pass/fail review, saves tokens)
light_models = [
    ChatGroq(model="llama-3.1-8b-instant", temperature=0.1, api_key=os.getenv("GROQ_API_KEY")),
    ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1, google_api_key=os.getenv("GEMINI_API_KEY"))
]

# Expose instantiated DualLLMs
llm = DualLLM(heavy_models)
llm_fast = DualLLM(light_models)