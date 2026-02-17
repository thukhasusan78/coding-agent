import os
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

class Notifier:
    def __init__(self):
        self.chat_id = os.getenv("ALLOWED_USER_ID")
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.bot = Bot(token=self.token) if self.token else None

    async def send_status(self, message: str):
        """Status အခြေအနေ ပို့မယ်"""
        if not self.bot or not self.chat_id: return
        try:
            # Console မှာလည်းပြ၊ Telegram လည်းပို့
            print(f"📡 Telegram: {message}") 
            await self.bot.send_message(chat_id=self.chat_id, text=message)
        except Exception as e:
            print(f"⚠️ Notifier Error: {e}")

    async def send_log_file(self, file_path: str, caption: str = "📜 Execution Log"):
        """Log ဖိုင် ပို့မယ်"""
        if not self.bot or not self.chat_id: return
        if not os.path.exists(file_path): return

        try:
            with open(file_path, 'rb') as f:
                await self.bot.send_document(
                    chat_id=self.chat_id,
                    document=f,
                    caption=caption
                )
        except Exception as e:
            print(f"⚠️ Log Upload Error: {e}")

# Global Instance
notifier = Notifier()