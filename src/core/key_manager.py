import itertools
import random
from google import genai
from config.settings import settings

class KeyManager:
    def __init__(self):
        self.keys = settings.GOOGLE_API_KEYS
        
        if not self.keys:
            # Fallback for safety to prevent crash, though settings handles it
            print("⚠️ Warning: No Google API Keys found!")
            self.keys = ["dummy_key"]

        print(f"🔑 KeyManager Loaded: {len(self.keys)} keys available for rotation.")
        # Cycle iterator (Round Robin)
        self.key_cycle = itertools.cycle(self.keys)

    def get_client(self):
        """Returns a genai.Client with the next key in rotation"""
        next_key = next(self.key_cycle)
        # Debug print (Optional)
        print(f"🔄 Using Key ending in: ...{next_key[-4:]}")
        return genai.Client(api_key=next_key)

    def get_next_key(self):
        return next(self.key_cycle)    
    
    def get_random_key(self):
        """Get a random key (Alternative strategy)"""
        return random.choice(self.keys)