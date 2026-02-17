import os
import time
import requests
from src.core.state import AgentState
from src.tools import git_tools, file_tools
from src.runtime.docker_mgr import docker_mgr

class DeployerAgent:
    async def execute(self, state: AgentState):
        logs = []
        final_url = "N/A"
        created_files = state.get('created_files', [])
        subdomain = state.get('subdomain')
        mission = state.get('mission', "").lower()

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
            command = f"python {main_file}"
            port = 8000

            if "streamlit" in file_content:
                port = 8501
                command = f"streamlit run {main_file} --server.port 8501 --server.address 0.0.0.0"
                
            elif "fastapi" in file_content.lower():
                port = 8000
                app_module = main_file.replace(".py", "").replace("/", ".")
                command = f"uvicorn {app_module}:app --host 0.0.0.0 --port 8000"

            # 3. Docker Container Deployment
            print(f"🚀 Deploying {subdomain} on Port {port}...")
            logs.append(f"🚀 Deploying {subdomain}...")
            
            deploy_res = "Init"
            try:
                # 🔥 FIX: Container ရှိပြီးသားဆိုရင် Restart ပဲလုပ်မယ် (Loop မဖြစ်အောင်)
                existing = docker_mgr.client.containers.get(subdomain)
                if existing.status == "running":
                    logs.append(f"ℹ️ Container {subdomain} is already running. Restarting...")
                    existing.restart()
                    deploy_res = f"✅ Container Restarted: {subdomain}"
                else:
                    raise Exception("Not running")
            except:
                # မရှိမှ အသစ် run မယ်
                deploy_res = docker_mgr.start_container(
                    image=image,
                    name=subdomain,
                    port=port,
                    command=f"bash -c 'pip install -r requirements.txt && {command}'", 
                    env={"PORT": str(port)}
                )
            
            logs.append(str(deploy_res))
            
            # 🔥 Smart Health Check Logic
            if "SUCCESS" in str(deploy_res) or "Started" in str(deploy_res) or "Restarted" in str(deploy_res):
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