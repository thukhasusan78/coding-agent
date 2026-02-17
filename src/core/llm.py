import os
from openai import AsyncOpenAI
from src.core.key_manager import KeyManager
from config.settings import settings

class LLMEngine:
    def __init__(self):
        # 1. Setup Google Key Rotation
        self.key_manager = KeyManager()
        
        # 2. Setup OpenRouter (Claude/DeepSeek etc.)
        self.openrouter_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )
        
    def get_gemini_client(self):
        """For Coder Agent (Uses Rotation)"""
        return self.key_manager.get_client()

    def get_openrouter_client(self):
        """For Architect & Debugger Agents"""
        return self.openrouter_client

# Singleton Instance (တစ်နေရာတည်းကနေ ခေါ်သုံးဖို့)
llm_engine = LLMEngine()