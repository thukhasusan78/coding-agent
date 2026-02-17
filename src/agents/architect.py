import json
from src.core.state import AgentState
from src.core.llm import llm_engine
from config.settings import settings
from src.tools.files import file_tools

class ArchitectAgent:
    async def execute(self, state: AgentState):
        mission = state['mission']
        structure = file_tools.get_project_structure()
        
        print(f"🏗️ Architect ({settings.MODEL_ARCHITECT}): Analyzing Mission...\n")
        
        # Cleanup Check (မူရင်း Logic)
        cleanup_needed = False
        if any(w in mission.lower() for w in ["delete", "remove", "cleanup", "wipe"]):
            cleanup_needed = True

        system_msg = f"""
        You are the Chief Software Architect using Claude 3.5 Sonnet.
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
            client = llm_engine.get_openrouter_client()
            response = await client.chat.completions.create(
                model=settings.MODEL_ARCHITECT,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": "Create the execution plan."}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
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
            return {"logs": [f"❌ Architect Error: {e}"], "plan": []}