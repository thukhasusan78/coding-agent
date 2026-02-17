import os
import asyncio
import logging
import uvicorn
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Import Brain & Telegram Bot
from src.brain import SeniorEngineerBrain
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from telegram import Update

load_dotenv()

# --- Logging Setup ---
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", 0))
API_PORT = int(os.getenv("PORT", 8000))

# --- Global State (Initially None) ---
# 🔥 FIX: အပြင်မှာ Brain ကို ကြိုမဆောက်တော့ဘူး (RAM သက်သာအောင်)
app_state = {
    "brain": None, 
    "telegram_app": None
}

# --- Telegram Logic ---
async def telegram_handler(update: Update, context):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    
    user_text = update.message.text
    # Brain မရှိသေးရင် Error ပြန်မယ်
    if not app_state["brain"]:
        await update.message.reply_text("⚠️ Brain is initializing... Please wait.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    # Global state ထဲက brain ကိုလှမ်းခေါ်မယ်
    response = await app_state["brain"].think_and_reply(user_text)
    
    if len(response) > 4000:
        for x in range(0, len(response), 4000):
            await update.message.reply_text(response[x:x+4000])
    else:
        await update.message.reply_text(response)

async def start_telegram():
    if not TELEGRAM_TOKEN:
        logger.warning("⚠️ No TELEGRAM_TOKEN found.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), telegram_handler))
    
    app_state["telegram_app"] = application
    logger.info("🚀 Telegram Bot Started (Polling)...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

# --- FastAPI Lifecycle (The Magic Fix) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔥 Server Run မှ Brain ကို တစ်ခါတည်းပဲ ဆောက်မယ်
    logger.info("🧠 Initializing Single Instance of Jarvis Brain...")
    app_state["brain"] = SeniorEngineerBrain()
    
    # Telegram Start
    asyncio.create_task(start_telegram())
    
    yield
    
    # Cleanup
    if app_state["telegram_app"]:
        await app_state["telegram_app"].updater.stop()
        await app_state["telegram_app"].stop()
        await app_state["telegram_app"].shutdown()

# --- API Definition ---
app = FastAPI(title="Ironman Agent API", lifespan=lifespan)

@app.get("/")
def health_check():
    ram_usage = "Normal" if app_state["brain"] else "Initializing"
    return {"status": "online", "brain_status": ram_usage}

@app.post("/execute")
async def execute_task(request: Request):
    data = await request.json()
    task = data.get("task")
    if not task: return {"error": "No task"}
    
    if not app_state["brain"]:
        return {"error": "Brain not ready"}

    logger.info(f"📥 API Task: {task}")
    report = await app_state["brain"].think_and_reply(task)
    return {"status": "success", "report": report}

if __name__ == "__main__":
    # 🔥 reload=False ထားထားပြီးသားမို့ ပြဿနာမရှိ၊ ဒါပေမဲ့ uvicorn run ရင် 
    # အပေါ်က global initialization မရှိတော့လို့ RAM နှစ်ခါမစားတော့ဘူး
    uvicorn.run("src.main:app", host="0.0.0.0", port=API_PORT, reload=False)