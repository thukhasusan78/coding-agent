import json
from src.core.state import AgentState
from src.core.llm import llm_engine
from config.settings import settings
from src.tools.files import file_tools
# 👇 Gemini Config သုံးဖို့ Import ထည့်ပါတယ်
from google.genai.types import GenerateContentConfig

class ArchitectAgent:
    async def execute(self, state: AgentState):
        mission = state['mission']
        structure = file_tools.get_project_structure()
        
        # Settings မှာ 2.5 Pro (သို့) 3 Flash ထားထားတာကို လှမ်းယူပါလိမ့်မယ်
        model_name = settings.MODEL_ARCHITECT 
        print(f"🏗️ Architect ({model_name}): Analyzing Mission...\n")
        
        # Cleanup Check
        cleanup_needed = False
        if any(w in mission.lower() for w in ["delete", "remove", "cleanup", "wipe"]):
            cleanup_needed = True

        system_msg = f"""
        You are the Chief Software Architect.
        Current Project Structure:
        {structure}
        
        Task:
        1. Analyze the mission: "{mission}"
        2. Create a specific PROJECT FOLDER NAME (e.g., 'snake_game', 'vpn_manager').
        3. Break down the mission into file tasks.
        
        CRITICAL RULE: 
        - ALL files must be inside the project folder. 
        - Example: DO NOT write 'app.py'. WRITE 'snake_game/app.py'.
        
        Output JSON format ONLY:
        {{
            "plan": [
                {{"file": "project_name/main.py", "description": "Main entry point..."}}
            ],
            "subdomain": "project-name-v1"
        }}
        """

        try:
            # 🔥 FIX: OpenRouter ကို ဖြုတ်ပြီး Google Client (Gemini) ကို သုံးပါမယ်
            client = llm_engine.get_gemini_client()
            
            # Gemini API Call (JSON Mode)
            response = client.models.generate_content(
                model=model_name,
                contents=system_msg, # Architect မှာ User Message ခွဲစရာမလိုလို့ System Prompt တစ်ခုတည်း ပေါင်းပို့လိုက်တာ ပိုငြိမ်ပါတယ်
                config=GenerateContentConfig(
                    response_mime_type="application/json", # JSON အတင်းထွက်ခိုင်းမယ်
                    temperature=0.2
                )
            )
            
            # Gemini Response ကို ယူမယ်
            content = response.text
            data = json.loads(content)
            
            plan = data.get("plan", [])
            # Status တွေကို pending ပြောင်းမယ်
            for task in plan:
                task['status'] = 'pending'
            
            subdomain = data.get("subdomain", "")
            
            return {
                "plan": plan, 
                "subdomain": subdomain,
                "cleanup_needed": cleanup_needed,
                "created_files": [],
                "logs": [f"🏗️ Architect: Plan created with {len(plan)} tasks."]
            }
        except Exception as e:
            print(f"❌ Architect Error: {e}")
            # Error တက်ရင် Plan အလွတ်ပြန်ပေးမယ် (System မရပ်သွားအောင်)
            return {"logs": [f"❌ Architect Error: {e}"], "plan": []}