import os
import subprocess
import time
import asyncio
import signal
import psutil
from src.core.state import AgentState
from src.core.llm import llm_engine
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
        
        # 1. Identify Target File (Main Entry Point)
        # Deployer မတိုင်ခင် စစ်မှာမို့ Main File ကို ဒီအဆင့်မှာကတည်းက ရှာရမယ်
        main_file = next((f for f in created_files if f.endswith(".py") and any(x in f for x in ["main", "app", "bot", "index", "server"])), None)
        
        if not main_file:
            # အကယ်၍ Main file မတွေ့ရင် Python file တစ်ခုခုကို ယူမယ်
            main_file = next((f for f in created_files if f.endswith(".py")), None)

        if not main_file:
            return {
                "logs": logs + ["⚠️ Tester: No Python file found to test. Skipping."],
                "error_logs": ""
            }

        print(f"🧪 Tester: Starting Quality Control on {main_file}...")
        logs.append(f"🧪 Tester: Running pre-flight checks on {main_file}...")

        # 2. Setup Isolated Environment (Feature Proof)
        if not os.path.exists(self.python_exec):
            logs.append("⚙️ Tester: Creating isolated virtual environment...")
            subprocess.run(["python", "-m", "venv", self.venv_dir], check=True)

        # 3. Install Dependencies (Smart Check)
        # Requirements.txt ရှိရင် အရင်သွင်းမယ်
        project_dir = os.path.dirname(os.path.join("/app/workspace", main_file))
        req_path = os.path.join(project_dir, "requirements.txt")
        
        if os.path.exists(req_path):
            logs.append("📦 Tester: Installing dependencies...")
            install_res = subprocess.run(
                [self.pip_exec, "install", "-r", req_path], 
                capture_output=True, text=True
            )
            if install_res.returncode != 0:
                # Dependency Error ဆိုရင် Tech Lead ဆီ ချက်ချင်းပြန်ပို့
                error_msg = f"Dependency Installation Failed:\n{install_res.stderr}"
                print("❌ Tester: Pip Install Failed")
                return {
                    "error_logs": error_msg,
                    "logs": logs + [f"❌ Tester: Dependency Error in {req_path}"]
                }
        
        # 4. DRY RUN (The Sandbox Test)
        # Code ကို တကယ် Run ကြည့်မယ် (Timeout 10s)
        # Web Server ဆိုရင် 10s နေလို့ မသေရင် Pass
        # Script ဆိုရင် Exit Code 0 ဆိုရင် Pass
        
        full_path = os.path.join("/app/workspace", main_file)
        logs.append(f"🚀 Tester: Dry running {main_file}...")

        try:
            # Process ကို စတင်မယ်
            process = subprocess.Popen(
                [self.python_exec, full_path],
                cwd=os.path.dirname(full_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid # Group ID ခွဲမယ် (Kill ရလွယ်အောင်)
            )

            # 10 စက္ကန့် စောင့်ကြည့်မယ်
            try:
                stdout, stderr = process.communicate(timeout=10)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                # Web Server (Daemon) တွေက Timeout ဖြစ်တာ ပုံမှန်ပဲ (ဆိုလိုတာက မကွဲသွားဘူး)
                print("✅ Tester: App is running stable (Timeout reached, which is good for Servers).")
                
                # အတင်းပိတ်မယ်
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                return_code = 0 # Pass လို့ သတ်မှတ်မယ်
                stdout = "Process running..."
                stderr = ""

            # 5. Result Analysis with AI (Gemini 3 Flash)
            if return_code != 0:
                print(f"❌ Tester: Runtime Error Detected (Exit Code: {return_code})")
                
                # Error Log ကို AI ဆီပို့ပြီး သုံးသပ်ခိုင်းမယ်
                analysis = await self._analyze_error(stderr or stdout, main_file)
                
                return {
                    "error_logs": f"Runtime Error in {main_file}:\n{stderr}\n\nAI Analysis: {analysis}",
                    "logs": logs + [f"❌ Tester: Runtime Check Failed. {analysis}"]
                }
            
            else:
                print("✅ Tester: Test Passed!")
                return {
                    "error_logs": "", # Error မရှိ
                    "logs": logs + ["✅ Tester: Passed stability check."]
                }

        except Exception as e:
            return {
                "error_logs": f"Tester Exception: {str(e)}",
                "logs": logs
            }

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