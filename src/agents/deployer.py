import os
import time
import requests
import re
from src.core.state import AgentState
from src.core.notifier import notifier
from src.tools import git_tools, file_tools
from src.runtime.docker_mgr import docker_mgr
from src.core.llm import llm_engine 
from config.settings import settings
from google.genai.types import GenerateContentConfig

class DeployerAgent:
    async def execute(self, state: AgentState):
        logs = []
        final_url = "N/A"
        created_files = state.get('created_files', [])
        subdomain = state.get('subdomain')
        mission = state.get('mission', "").lower()
        
        # 📡 Telegram Alert
        await notifier.send_status(f"🚀 Deployment Phase: Initializing...")

        # 1. Auto Git Push
        git_res = git_tools.auto_push("Auto-update by Jarvis Agent")
        logs.append(f"Git: {git_res}")
        
        # 2. Identify Main File & Configuration
        main_file = next((f for f in created_files if "app" in f or "main" in f or "bot" in f or "index" in f), None)
        
        # 🔥 FIX: Search Logic Improvement
        if not main_file:
            print("🔍 Searching existing projects in workspace...")
            best_match = None
            highest_score = 0
            
            workspace_dir = "/app/workspace"
            
            # 🛑 IGNORE LIST: ဒီ Folder တွေထဲ လုံးဝဝင်မရှာဘူး
            ignore_dirs = [
                "__pycache__", ".git", "venv", "env", "test_env", 
                "site-packages", "lib", "bin", "include", "node_modules"
            ]

            for root, dirs, files in os.walk(workspace_dir):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if d not in ignore_dirs and not any(x in os.path.join(root, d) for x in ignore_dirs)]
                
                # Double check root path just in case
                if any(ignored in root for ignored in ignore_dirs):
                    continue
                
                for file in files:
                    if file in ["main.py", "app.py", "index.py", "streamlit_app.py", "bot.py"]:
                        full_path = os.path.join(root, file)
                        folder_name = os.path.basename(root).lower()
                        
                        score = 0
                        if folder_name in mission: score += 5 # Folder Name တူရင် Score ပိုပေး
                        if "bitcoin" in mission and "bitcoin" in folder_name: score += 2
                        
                        # အသစ်ပြင်ထားတဲ့ ဖိုင်ဆို ပိုဦးစားပေးမယ်
                        try:
                            mtime = os.path.getmtime(full_path)
                            if time.time() - mtime < 300: score += 3 # 5 မိနစ်အတွင်းပြင်ထားရင်
                        except: pass

                        if score > highest_score or best_match is None:
                            highest_score = score
                            best_match = os.path.relpath(full_path, workspace_dir)

            if best_match:
                main_file = best_match
                print(f"✅ Auto-Selected Project: {main_file}")
                logs.append(f"✅ Auto-Selected Project: {main_file}")
            else:
                logs.append("⚠️ No runnable project found in workspace.")

        if main_file:
            # Subdomain / Container Name Determination
            if not subdomain:
                folder_name = os.path.dirname(main_file)
                if folder_name and folder_name != ".":
                    # 🔥 FIX: Slash တွေကို Dash ပြောင်း၊ Special Char တွေဖယ်ထုတ်
                    clean_name = folder_name.replace("/", "-").replace("\\", "-").replace("_", "-")
                    subdomain = re.sub(r'[^a-z0-9-]', '', clean_name.lower())
                else:
                    subdomain = "jarvis-app"
            
            # Ensure subdomain is valid for Docker
            subdomain = subdomain[:63].strip('-') # Docker Limit
            
            await notifier.send_status(f"🚀 Launching Project: `{subdomain}`")

            # App Type & Port Detection
            file_content = file_tools.read_file(main_file)
            image = "python:3.11-slim"
            
            container_file = os.path.basename(main_file)
            
            # Default Command
            command = f"python {container_file}"
            port = 8000

            if "streamlit" in file_content:
                port = 8501
                command = f"streamlit run {container_file} --server.port 8501 --server.address 0.0.0.0"
            elif "fastapi" in file_content.lower():
                port = 8000
                app_module = container_file.replace(".py", "")
                command = f"uvicorn {app_module}:app --host 0.0.0.0 --port 8000"

            current_command = command
            project_full_path = os.path.dirname(os.path.join("/app/workspace", main_file))
            deploy_res = "Init"
            
            # 3. Smart Deployment Loop
            print(f"🚀 Deploying {subdomain}...")
            logs.append(f"🚀 Deploying container `{subdomain}`...")

            for attempt in range(3):
                try:
                    logs.append(f"🔄 Attempt {attempt+1}: {current_command}")
                    
                    # Kill Old
                    try:
                        old = docker_mgr.client.containers.get(subdomain)
                        old.remove(force=True)
                    except: pass

                    # Run
                    deploy_res = docker_mgr.start_container(
                        image=image,
                        name=subdomain,
                        port=port,
                        command=f"pip install -r requirements.txt && {current_command}",
                        env={"PORT": str(port)},
                        code_path=project_full_path
                    )

                    time.sleep(5) 
                    container = docker_mgr.client.containers.get(subdomain)
                    recent_logs = container.logs().decode('utf-8')
                    
                    if "Error" in recent_logs or "Exception" in recent_logs or container.status != "running":
                        print(f"⚠️ Warning on Attempt {attempt+1}")
                        
                        # 🔥 BRAIN POWER: Gemini 2.5 Pro (Thinking Model)
                        if attempt < 2: 
                            logs.append(f"⚠️ Error detected. Asking Gemini 2.5 Pro to fix command...")
                            
                            client = llm_engine.get_gemini_client()
                            
                            prompt = f"""
                            You are a DevOps Expert.
                            I tried to run a Python container but it failed.
                            
                            CONTEXT:
                            - File: {container_file}
                            - Command: {current_command}
                            - LOGS: {recent_logs[-1000:]}

                            TASK:
                            - Analyze the error.
                            - Return ONLY the corrected bash command.
                            - NO explanation.
                            """
                            
                            try:
                                response = client.models.generate_content(
                                    model=settings.MODEL_ARCHITECT, # 2.5 Pro
                                    contents=prompt,
                                    config=GenerateContentConfig(temperature=0.2)
                                )
                                
                                fixed_command = response.text.strip().replace("`", "")
                                logs.append(f"💡 AI Fix: Switching to '{fixed_command}'")
                                current_command = fixed_command 
                                continue 
                            except Exception as e:
                                logs.append(f"❌ AI Fix Failed: {e}")

                    else:
                        logs.append("✅ Container seems stable.")
                        break 

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
                # Folder မရှိရင်ဆောက်
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                
                with open(log_file, "w") as f:
                    f.write(raw_logs)
            except: 
                pass
            
            # 🔥 Smart Health Check Logic
            # "Deployed" (သို့) "Success" ဆိုတဲ့ စာလုံးပါရင် အောင်မြင်တယ်လို့ ယူဆပြီး Health Check စမယ်
            if "SUCCESS" in str(deploy_res) or "Started" in str(deploy_res) or "Restarted" in str(deploy_res) or "Deployed" in str(deploy_res):
                
                # 🛑 Simple Script Bypass: Web Server မဟုတ်ရင် Health Check ကျော်မယ်
                # Docker Log ထဲမှာ "Uvicorn running" (သို့) "Streamlit" မတွေ့ရင် Script (Bot) လို့ ယူဆမယ်
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