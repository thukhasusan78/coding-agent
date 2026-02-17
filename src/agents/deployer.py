import os
import time
import requests
from src.core.state import AgentState
from src.core.notifier import notifier
from src.tools import git_tools, file_tools
from src.runtime.docker_mgr import docker_mgr
from src.core.llm import llm_engine # Brain ကို ခေါ်သုံးမယ်
from config.settings import settings

class DeployerAgent:
    async def execute(self, state: AgentState):
        logs = []
        final_url = "N/A"
        created_files = state.get('created_files', [])
        subdomain = state.get('subdomain')
        mission = state.get('mission', "").lower()
        # 📡 Telegram Alert
        subdomain = state.get('subdomain', 'app')
        await notifier.send_status(f"🚀 Deployment Phase: Launching `{subdomain}`...")

        # 1. Auto Git Push
        git_res = git_tools.auto_push("Auto-update by Jarvis Agent")
        logs.append(f"Git: {git_res}")
        
        # 2. Identify Main File & Configuration
        # အသစ်ဖန်တီးထားတဲ့ ဖိုင်တွေထဲမှာ Main ပါလားရှာမယ်
        main_file = next((f for f in created_files if "app" in f or "main" in f or "bot" in f or "index" in f), None)
        
        # 🔥 FIX: ဖိုင်အသစ်မရှိရင် Workspace ထဲက Project အဟောင်းတွေကို ရှာမယ် (Auto-Discovery)
        if not main_file:
            print("🔍 Searching existing projects in workspace...")
            best_match = None
            highest_score = 0
            
            # Workspace ထဲက ဖိုင်အားလုံးကို လိုက်စစ်မယ်
            workspace_dir = "/app/workspace"
            for root, dirs, files in os.walk(workspace_dir):
                if "memory_db" in root or "__pycache__" in root or ".git" in root: 
                    continue
                
                for file in files:
                    # Run လို့ရမယ့် ဖိုင်အမျိုးအစားဖြစ်ရမယ်
                    if file in ["main.py", "app.py", "index.py", "streamlit_app.py", "bot.py"]:
                        full_path = os.path.join(root, file)
                        folder_name = os.path.basename(root).lower()
                        
                        # User ပြောတဲ့ mission ထဲက စကားလုံးတွေနဲ့ တိုက်စစ်မယ်
                        # ဥပမာ: mission="bitcoin run", folder="bitcoin_tracker" -> Match!
                        score = 0
                        if folder_name in mission: score += 2
                        if "bitcoin" in mission and "bitcoin" in folder_name: score += 2
                        
                        # အသစ်ပြင်ထားတဲ့ ဖိုင်ဆို ပိုဦးစားပေးမယ်
                        mtime = os.path.getmtime(full_path)
                        
                        # ပထမဆုံးတွေ့တဲ့ကောင် (သို့) Score များတဲ့ကောင်ကို မှတ်ထားမယ်
                        if score > highest_score or best_match is None:
                            highest_score = score
                            # Relative path ပြောင်းမယ် (src/tools/files.py က relative ပဲသိလို့)
                            best_match = os.path.relpath(full_path, workspace_dir)

            if best_match:
                main_file = best_match
                print(f"✅ Auto-Selected Project: {main_file}")
                logs.append(f"✅ Auto-Selected Project: {main_file}")
            else:
                logs.append("⚠️ No runnable project found in workspace.")

        if main_file:
            # Subdomain Determination
            if not subdomain:
                folder_name = os.path.dirname(main_file)
                subdomain = folder_name.replace("_", "-").lower() if folder_name else "jarvis-app"

            # App Type & Port Detection
            file_content = file_tools.read_file(main_file)
            image = "python:3.11-slim"
            
            # 🔥 FIX: Container ထဲမှာ Folder အထပ်မရှိတော့လို့ ဖိုင်နာမည်သန့်သန့်ကိုပဲ ယူမယ်
            container_file = os.path.basename(main_file)
            
            # 🔥 Default Command (အရင်ဆုံး ဒါကို ကြေညာရမယ်)
            command = f"python {container_file}"
            port = 8000

            # Framework ပေါ်မူတည်ပြီး Command ပြောင်းမယ်
            if "streamlit" in file_content:
                port = 8501
                command = f"streamlit run {container_file} --server.port 8501 --server.address 0.0.0.0"
            elif "fastapi" in file_content.lower():
                port = 8000
                app_module = container_file.replace(".py", "")
                command = f"uvicorn {app_module}:app --host 0.0.0.0 --port 8000"

            # --- Smart Command Strategy ---
            current_command = command
            
            # 3. Smart Deployment Loop (Auto-Fixing)
            print(f"🚀 Deploying {subdomain} with Smart Recovery...")
            logs.append(f"🚀 Deploying {subdomain}...")

            # Project Folder အပြည့်အစုံ
            project_full_path = os.path.dirname(os.path.join("/app/workspace", main_file))
            
            deploy_res = "Init" # Variable initialize
            
            # 🔥 ၃ ခါအထိ ကြိုးစားခွင့်ပေးမယ်
            for attempt in range(3):
                try:
                    logs.append(f"🔄 Attempt {attempt+1}: Trying command -> {current_command}")
                    
                    # Container အဟောင်းရှိရင် အရင်ဖျက်မယ် (Clean Start ရဖို့)
                    try:
                        old = docker_mgr.client.containers.get(subdomain)
                        old.remove(force=True)
                    except: pass

                    # Run မယ်
                    deploy_res = docker_mgr.start_container(
                        image=image,
                        name=subdomain,
                        port=port,
                        command=f"pip install -r requirements.txt && {current_command}",
                        env={"PORT": str(port)},
                        code_path=project_full_path
                    )

                    # ၅ စက္ကန့်လောက် စောင့်ပြီး Error တက်မတက် "ချောင်း" ကြည့်မယ်
                    time.sleep(5) 
                    container = docker_mgr.client.containers.get(subdomain)
                    
                    # Log တွေကို စစ်မယ်
                    recent_logs = container.logs().decode('utf-8')
                    
                    # Error စစ်ဆေးခြင်း
                    if "Error" in recent_logs or "Exception" in recent_logs or "not found" in recent_logs or container.status != "running":
                        print(f"⚠️ Deployment Warning on Attempt {attempt+1}")
                        
                        # 🔥 BRAIN POWER: Error ကို Sonnet ဆီ ပို့ပြီး Command အသစ်တောင်းမယ်
                        if attempt < 2: 
                            logs.append(f"⚠️ Error detected. Asking Sonnet to fix command...")
                            
                            client = llm_engine.get_openrouter_client() # Sonnet (Paid)
                            
                            prompt = f"""
                            You are a DevOps Expert.
                            I tried to run a Python container but it failed.
                            
                            CONTEXT:
                            - File structure inside container: /app/{container_file} (and other files injected flatly)
                            - Current Command: {current_command}
                            - ERROR LOGS:
                            {recent_logs[-1000:]}

                            TASK:
                            - Analyze the error (e.g., ModuleNotFound, FileDoesNotExist).
                            - Return ONLY the corrected bash command to run the app.
                            - Do NOT include 'pip install'. Just the run command.
                            - Example Output: streamlit run main.py --server.port 8501
                            
                            RESPONSE (Command ONLY):
                            """
                            
                            # Sonnet ကို မေးမယ်
                            try:
                                response = await client.chat.completions.create(
                                    model=settings.MODEL_ARCHITECT, 
                                    messages=[{"role": "user", "content": prompt}]
                                )
                                fixed_command = response.choices[0].message.content.strip().replace("`", "")
                                print(f"💡 Sonnet suggested fix: {fixed_command}")
                                logs.append(f"💡 AI Fix: Switching to '{fixed_command}'")
                                current_command = fixed_command 
                                continue # Loop အစကို ပြန်သွားမယ်
                            except Exception as e:
                                logs.append(f"❌ AI Fix Failed: {e}")

                    else:
                        logs.append("✅ Container seems stable.")
                        break # အောင်မြင်ရင် Loop ထဲက ထွက်မယ်

                except Exception as e:
                    logs.append(f"❌ Exception: {e}")
                    time.sleep(2)

            logs.append(str(deploy_res))
            # 📜 Container Log ယူပြီး Telegram ပို့မယ်
            try:
                container = docker_mgr.client.containers.get(subdomain)
                raw_logs = container.logs().decode('utf-8')

                # Log ဖိုင်သိမ်း
                log_file = f"workspace/{subdomain}_deploy.log"
                with open(log_file, "w") as f:
                    f.write(raw_logs)
            except: 
                pass
            
            # 🔥 Smart Health Check Logic
            # "Deployed" ဆိုတဲ့ စာလုံးပါရင်လည်း Success လို့ ယူဆမယ်
            if "SUCCESS" in str(deploy_res) or "Started" in str(deploy_res) or "Restarted" in str(deploy_res) or "Deployed" in str(deploy_res):
                
                # 🛑 Simple Script Bypass: Web Server မဟုတ်ရင် Health Check ကျော်မယ်
                # Docker Log ထဲမှာ "Uvicorn running" (သို့) "Streamlit" မတွေ့ရင် Script လို့ ယူဆမယ်
                container = docker_mgr.client.containers.get(subdomain)
                initial_logs = container.logs().decode('utf-8').lower()
                
                if not any(x in initial_logs for x in ["listening", "running on", "uvicorn", "streamlit", "http server"]):
                    # 🛑 Double Check: Web Server မဟုတ်ပေမယ့် Container က သေသွားပြီလား?
                    container.reload()
                    if container.status != "running":
                        print(f"❌ {subdomain} crashed immediately.")
                        return {
                            "error_logs": f"CRASH DETECTED: Container stopped immediately after starting.\nLast Logs:\n{initial_logs}",
                            "logs": logs + [f"❌ {subdomain} crashed. See logs."]
                        }

                    print(f"ℹ️ {subdomain} appears to be a background script. Skipping HTTP Health Check.")
                    
                    # 📡 Log ပို့မယ်
                    log_file = f"workspace/{subdomain}_deploy.log"
                    # Log မရှိရင်တောင် အလွတ်မဖြစ်အောင် ကာမယ်
                    if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
                        with open(log_file, "w") as f: f.write("No logs captured (Process might be silent).")

                    await notifier.send_status("✅ Background Script Running. Sending logs...")
                    await notifier.send_log_file(log_file, caption=f"📜 Execution Log: {subdomain}")
                    
                    return {"final_report": f"🚀 Script is running in background!\nCheck logs with: `docker logs -f {subdomain}`"}

                # Web Server ဆိုမှ အောက်က Health Check ကို ဆက်လုပ်မယ်
                print("🏥 Starting Smart Health Check...")
                is_healthy = False

                internal_url = f"http://{subdomain}:{port}"
                max_retries = 30 
                retry_interval = 5

                container = None
                try:
                    container = docker_mgr.client.containers.get(subdomain)
                except: pass

                for i in range(max_retries):
                    # 1. Check Crash
                    if container:
                        container.reload()
                        if container.status != "running":
                            logs.append("❌ Container died prematurely.")
                            break
                    
                    # 2. Check Logs (Install လုပ်နေတုန်းလား)
                    try:
                        current_logs = container.logs().decode('utf-8')[-500:].lower()
                        if "installing" in current_logs or "downloading" in current_logs:
                            print(f"⚙️ Installing dependencies... ({i}/{max_retries})")
                            time.sleep(retry_interval)
                            continue 
                    except: pass

                    # 3. Active Ping
                    try:
                        print(f"⏳ Pinging App... ({i}/{max_retries})")
                        response = requests.get(internal_url, timeout=3)
                        if response.status_code < 500:
                            is_healthy = True
                            logs.append(f"✅ App is responding! (Status: {response.status_code})")
                            break
                    except Exception:
                        time.sleep(retry_interval)
                
                if is_healthy:
                    final_url = f"https://{subdomain}.thukha.online"
                else:
                    logs.append(f"❌ Smart Health Check Failed.")
                    try:
                        crash_log = container.logs().decode('utf-8')[-2000:]
                        return {"error_logs": crash_log, "logs": logs}
                    except:
                        return {"error_logs": "Unknown Error", "logs": logs}
            else:
                final_url = "⚠️ Docker Start Failed"
                return {"error_logs": str(deploy_res), "logs": logs}
        
        # 4. Final Report
        report = f"""
        🏁 **Mission Accomplished**
        🌍 Live URL: {final_url}
        📂 Files: {len(created_files)} (Auto-Selected: {main_file})
        🤖 Git: {git_res}
        
        (Note: If the URL is 502/Unreachable, wait 1-2 mins for Cloudflare Tunnel to propagate)
        """
        return {"final_report": report}