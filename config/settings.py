import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # --- API Keys ---
    # List of Keys for rotation
    GOOGLE_API_KEYS = [k.strip() for k in os.getenv("GOOGLE_API_KEYS", "").split(",") if k.strip()]
    # Fallback to single key if list is empty
    if not GOOGLE_API_KEYS and os.getenv("GOOGLE_API_KEY"):
        GOOGLE_API_KEYS.append(os.getenv("GOOGLE_API_KEY"))

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    # --- Model Configuration ---
    # Architect (Planner) - Claude 3.5 Sonnet is best for reasoning
    MODEL_ARCHITECT = "anthropic/claude-3.5-sonnet"
    
    # Coder (Writer) - Gemini Flash is fast & cheap for bulk coding
    MODEL_CODER = "gemini-3-flash-preview"
    
    MODEL_CODER_NAME = "gemini-3-flash-preview" 

    # Debugger (The Fixer)
    MODEL_DEBUGGER = "anthropic/claude-3.5-sonnet"
    
    # Super Brain (The Last Resort)
    MODEL_SUPER = "anthropic/claude-opus-4-6"
    
    # --- System Limits ---
    MAX_RETRIES = 3
    RETRY_DELAY = 5 # seconds

settings = Settings()