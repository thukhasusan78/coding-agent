import traceback
import os
import glob
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from src.core.workflow import workflow
from src.core.state import AgentState

class SeniorEngineerBrain:
    def __init__(self):
        print("🧠 Jarvis Hybrid Brain Initialized (Async Memory)")
        # 🔥 Agent စတာနဲ့ Memory Size ကို အရင်စစ်မယ်
        self._manage_memory_health()

    def _manage_memory_health(self):
        """
        🔥 AUTO-CLEANUP: Database ဖောင်းပွလာရင် အသစ်လဲမယ့် စနစ်
        RAM 2GB VPS မှာ SQLite က 500MB ကျော်ရင် Query လေးပြီး Hang တတ်လို့
        Warning ပေးမယ်၊ အရမ်းများမှ ဖျက်မယ်။
        """
        # Workspace Folder မရှိရင် အရင်ဆောက်မယ်
        os.makedirs("workspace", exist_ok=True)
        
        db_path = "workspace/checkpoints.sqlite"
        
        # Warning Limit (သတိပေးရုံ)
        soft_limit_mb = 500
        # Hard Limit (ဖျက်မယ့်အဆင့် - VPS မကွဲအောင်)
        hard_limit_mb = 900 
        
        try:
            if os.path.exists(db_path):
                size_mb = os.path.getsize(db_path) / (1024 * 1024)
                
                if size_mb > hard_limit_mb:
                    print(f"🚨 CRITICAL MEMORY ({size_mb:.2f}MB). Wiping database to save VPS...")
                    # Database Related File တွေကို (.wal, .shm အပါအဝင်) အကုန်ရှင်းမယ်
                    for f in glob.glob("workspace/checkpoints.sqlite*"):
                        try:
                            os.remove(f)
                            print(f"🗑️ Deleted old memory: {f}")
                        except Exception as e:
                            print(f"⚠️ Failed to delete {f}: {e}")
                        
                elif size_mb > soft_limit_mb:
                    print(f"⚠️ Memory Warning: Database is huge ({size_mb:.2f}MB). Consider manual reset.")
                else:
                    print(f"✅ Memory Health Good: {size_mb:.2f}MB")
        except Exception as e:
            print(f"⚠️ Memory Check Error: {e}")

    async def think_and_reply(self, user_input: str) -> str:
        """
        Main Entry Point: Receives User Input -> Runs Graph -> Returns Report
        """
        try:
            # 1. State အသစ် စဆောက်မယ်
            initial_state: AgentState = {
                "mission": user_input,
                "plan": [],
                "current_task": None,
                "code_content": "",
                "error_logs": "",
                "retry_count": 0,
                "cleanup_needed": False,
                "created_files": [],
                "subdomain": "",
                "final_report": "Processing...",
                "logs": []
            }

            print(f"🚀 Starting Mission: {user_input}")
            
            # 🔥 Async Database Connection
            async with AsyncSqliteSaver.from_conn_string("workspace/checkpoints.sqlite") as checkpointer:
                
                # Workflow ကို Memory နဲ့ ပေါင်းပြီး App (Executable) ဖန်တီးမယ်
                app = workflow.compile(checkpointer=checkpointer)
                
                # Thread ID သတ်မှတ်မယ် (Memory အတွက် မရှိမဖြစ်)
                config = {"configurable": {"thread_id": "ironman-master-session"}}
                
                # Run မယ် (Async)
                final_state = await app.ainvoke(initial_state, config=config)
                
                # Report ပြန်ထုတ်မယ်
                report = final_state.get("final_report", "Mission Completed.")
                logs = "\n".join(final_state.get("logs", [])[-10:]) # Last 10 logs
                
                return f"{report}\n\n📋 **Logs:**\n{logs}"

        except Exception as e:
            error_msg = f"💥 Critical Brain Failure: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return error_msg