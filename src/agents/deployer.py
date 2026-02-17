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

        # 1. Auto Git Push
        git_res = git_tools.auto_push("Auto-update by Jarvis Agent")
        logs.append(f"Git: {git_res}")
        
        # 2. Identify Main File & Configuration
        main_file = next((f for f in created_files if "app" in f or "main" in f or "bot" in f or "index" in f), None)
        
        # 🔥 FIX: အသစ်တွေထဲမှာ မပါရင် (ဥပမာ requirements.txt ပဲပြင်ရင်) ရှိပြီးသား Folder ထဲမှာ သွားရှာမယ်
        if not main_file and created_files:
            # ပထမဆုံး ဖိုင်ရဲ့ Folder ကို Project Folder လို့ ယူဆမယ်
            project_dir = os.path.dirname(created_files[0])
            if project_dir:
                # အဲ့ဒီ Folder ထဲမှာ main.py တို့ app.py တို့ ရှိလား ရှာမယ်
                possible_names = ["main.py", "app.py", "bot.py", "index.py", "streamlit_app.py"]
                for name in possible_names:
                    # Check if file exists using file_tools logic (path join)
                    potential_path = os.path.join(project_dir, name)
                    # workspace folder အောက်မှာ တကယ်ရှိလား စစ်မယ်
                    if os.path.exists(os.path.join("/app/workspace", potential_path)):
                        main_file = potential_path
                        print(f"🔄 Found existing entry point: {main_file}")
                        break
        
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
                # Streamlit requires specific address binding
                command = f"streamlit run {main_file} --server.port 8501 --server.address 0.0.0.0"
                
            elif "fastapi" in file_content.lower():
                port = 8000
                app_module = main_file.replace(".py", "").replace("/", ".")
                command = f"uvicorn {app_module}:app --host 0.0.0.0 --port 8000"

            # 3. Docker Container Deployment
            print(f"🚀 Deploying {subdomain} on Port {port}...")
            logs.append(f"🚀 Deploying {subdomain}...")
            
            deploy_res = docker_mgr.start_container(
                image=image,
                name=subdomain,
                port=port,
                command=f"bash -c 'pip install -r requirements.txt && {command}'", # Install deps first
                env={"PORT": str(port)}
            )
            logs.append(deploy_res)
            
            # ... (အပေါ်က Code တွေ အတူတူပဲ) ...
            
            deploy_res = docker_mgr.start_container(
                image=image,
                name=subdomain,
                port=port,
                command=f"bash -c 'pip install -r requirements.txt && {command}'", 
                env={"PORT": str(port)}
            )
            logs.append(deploy_res)
            
            # 🔥 OPENCLAW METHOD: "Smart State-Aware Monitoring"
            if "SUCCESS" in str(deploy_res) or "Started" in str(deploy_res):
                logs.append(f"🏥 Starting Smart Health Check for {subdomain}...")
                is_healthy = False
                internal_url = f"http://{subdomain}:{port}"
                
                # Maximum Wait Time: 5 Minutes (Install ကြာနိုင်လို့)
                max_retries = 30 
                retry_interval = 10 

                container = None
                try:
                    container = docker_mgr.client.containers.get(subdomain)
                except:
                    pass

                for i in range(max_retries):
                    print(f"⏳ Health Check Attempt {i+1}/{max_retries}...")
                    
                    # 1. Check Crash
                    if container:
                        container.reload()
                        if container.status != "running":
                            logs.append("❌ Container died prematurely.")
                            break
                    
                    # 2. Check Logs (Install လုပ်နေလား ချောင်းကြည့်မယ်)
                    try:
                        # နောက်ဆုံး Log 10 ကြောင်းကို ယူမယ်
                        current_logs = container.logs().decode('utf-8')[-500:].lower()
                        if "installing" in current_logs or "downloading" in current_logs or "building" in current_logs:
                            print(f"⚙️ App is installing dependencies... Waiting.")
                            time.sleep(retry_interval)
                            continue # Install လုပ်တုန်းမို့ Error မစစ်ဘဲ ဆက်စောင့်မယ်
                    except:
                        pass

                    # 3. Active Ping (တကယ်တက်မတက် စစ်မယ်)
                    try:
                        response = requests.get(internal_url, timeout=3)
                        if response.status_code < 500:
                            is_healthy = True
                            logs.append(f"✅ App is responding! (Status: {response.status_code})")
                            break
                    except Exception:
                        # မရသေးရင် စောင့်မယ်
                        time.sleep(retry_interval)
                
                if is_healthy:
                    final_url = f"https://{subdomain}.thukha.online"
                else:
                    # 🚨 Time out ဖြစ်သွားရင် (သို့) Crash ရင်
                    logs.append(f"❌ Smart Health Check Failed after {max_retries*retry_interval}s.")
                    try:
                        crash_log = container.logs().decode('utf-8')[-2000:]
                        # Self-Healing Trigger လုပ်ဖို့ Return ပြန်မယ်
                        return {
                            "error_logs": crash_log,
                            "logs": logs
                        }
                    except:
                        return {"error_logs": "Unknown Error", "logs": logs}
            else:
                final_url = "⚠️ Docker Start Failed"
                return {"error_logs": str(deploy_res), "logs": logs}
        
        # 4. Final Report
        report = f"""
        🏁 **Mission Accomplished**
        🌍 Live URL: {final_url}
        📂 Files: {len(created_files)}
        🤖 Git: {git_res}
        
        (Note: If the URL is 502/Unreachable, wait 1-2 mins for Cloudflare Tunnel to propagate)
        """
        return {"final_report": report}