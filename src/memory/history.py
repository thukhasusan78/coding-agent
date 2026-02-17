import json
import os
from datetime import datetime

class ConversationHistory:
    def __init__(self, history_file="workspace/history.json"):
        self.history_file = history_file
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)

    def add_message(self, role: str, content: str):
        """
        Role: 'user' or 'assistant'
        """
        history = self.load_history()
        history.append({
            "role": role,
            "content": content,
            "timestamp": str(datetime.now())
        })
        # Keep last 50 turns to save space
        if len(history) > 50:
            history = history[-50:]
            
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def load_history(self):
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def get_context_string(self):
        """Agent ကို ပို့ပေးဖို့ String ဖွဲ့မယ်"""
        history = self.load_history()
        context = ""
        for msg in history[-10:]: # Last 10 messages for context
            context += f"{msg['role'].upper()}: {msg['content']}\n"
        return context

history_manager = ConversationHistory()