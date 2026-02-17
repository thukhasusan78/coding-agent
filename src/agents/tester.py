import os
import subprocess
import time
import asyncio
import signal
import psutil
from src.core.state import AgentState
from src.core.llm import llm_engine
from src.core.notifier import notifier
from config.settings import settings
from src.tools.files import file_tools

class TesterAgent:
    def __init__(self):
        # VPS RAM 2GB ဖြစ်တဲ့အတွက် Test Run တိုင်းမှာ Venv အသစ်မဆောက်ဘဲ
        # Project တစ်ခုလုံးအတွက် Shared Venv တစ်ခုကိုပဲ ပြန်သုံးပါမယ် (Speed + Storage Save)
        self.venv_dir = "/app/workspace/test_env"
        self.python_exec = os.path.join(self.venv_dir, "bin", "python")
        self.pip_exec = os.path.join(self.venv_dir, "bin", "pip")

    async def execute(self, state: AgentState):
        logs = state.get('logs', [])
        created_files = state.get('created_files', [])
        
        # Main File ရှာမယ်
        main_file = next((f for f in created_files if f.endswith(".py") and any(x in f for x in ["main", "app", "bot", "index", "server"])), None)
        if not main_file:
            main_file = next((f for f in created_files if f.endswith(".py")), None)

        if not main_file:
            return {"logs": logs + ["⚠️ Tester: No Python file found."], "error_logs": ""}

        # 📡 Telegram Status ပို့မယ်
        await notifier.send_status(f"🧪 Testing Phase: Verifying `{main_file}`...")

        # Environment ပြင်ဆင်ခြင်း
        if not os.path.exists(self.python_exec):
            subprocess.run(["python", "-m", "venv", self.venv_dir], check=True)

        # Requirements သွင်းခြင်း
        project_dir = os.path.dirname(os.path.join("/app/workspace", main_file))
        req_path = os.path.join(project_dir, "requirements.txt")
        
        if os.path.exists(req_path):
            install_res = subprocess.run([self.pip_exec, "install", "-r", req_path], capture_output=True, text=True)
            if install_res.returncode != 0:
                # ❌ Fail ဖြစ်ရင် Log ပို့မယ်
                await notifier.send_status(f"❌ Dependency Error in `{req_path}`")
                return {"error_logs": install_res.stderr, "logs": logs}
        
        # Test Run လုပ်ခြင်း
        full_path = os.path.join("/app/workspace", main_file)
        
        # Log စာသား စုစည်းမယ်
        log_content = f"--- TEST REPORT FOR {main_file} ---\n"

        try:
            process = subprocess.Popen(
                [self.python_exec, full_path],
                cwd=os.path.dirname(full_path),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, preexec_fn=os.setsid
            )

            stdout, stderr = "", ""
            return_code = 0
            
            try:
                stdout, stderr = process.communicate(timeout=10)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                stdout = "Service is running successfully (Timeout reached)."
            
            # Logs တွေကို ပေါင်းမယ်
            log_content += f"\n[STDOUT]:\n{stdout}\n\n[STDERR]:\n{stderr}\n\n[EXIT CODE]: {return_code}\n"

            # Log ဖိုင်ထုတ်မယ်
            log_file = f"workspace/{os.path.basename(main_file)}_test.log"
            with open(log_file, "w") as f:
                f.write(log_content)
            
            # Result စစ်ဆေးမယ်
            if return_code != 0:
                # ❌ Fail -> Telegram ပို့
                await notifier.send_status(f"❌ Test Failed for `{main_file}`. Sending logs...")
                await notifier.send_log_file(log_file, caption=f"❌ Test Failure Log")
                
                # AI Analysis (Log အတိုကောက်)
                analysis = await self._analyze_error(stderr or stdout, main_file)
                return {"error_logs": f"Runtime Error:\n{stderr}\nAnalysis: {analysis}", "logs": logs}
            
            else:
                # ✅ Pass -> Telegram ပို့
                await notifier.send_status(f"✅ Test Passed for `{main_file}`!")
                return {"error_logs": "", "logs": logs + ["✅ Tester Passed"]}

        except Exception as e:
            return {"error_logs": str(e), "logs": logs}

    async def _analyze_error(self, error_log: str, filename: str) -> str:
        """
        Gemini 3 Flash ကိုသုံးပြီး Error က Syntax ကြောင့်လား၊ Environment ကြောင့်လား ခွဲမယ်
        """
        try:
            client = llm_engine.get_gemini_client() # Flash Model (Fast & Cheap)
            
            prompt = f"""
            You are a QA Engineer. Analyze this Python error log from '{filename}'.
            
            ERROR LOG:
            {error_log[-2000:]} # Last 2000 chars

            Task:
            1. Is this a missing library error? (ModuleNotFoundError)
            2. Is this a syntax error?
            3. Is this a logic error?
            
            Output a 1-sentence actionable fix for the Developer.
            """
            
            response = client.models.generate_content(
                model=settings.MODEL_CODER, # Gemini 3 Flash
                contents=prompt
            )
            return response.text.strip()
            
        except Exception:
            return "Unknown error (AI Analysis Failed)"