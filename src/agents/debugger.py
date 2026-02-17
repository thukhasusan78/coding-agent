from src.core.state import AgentState
from src.core.llm import llm_engine
from config.settings import settings
from src.tools.files import file_tools
from google.genai.types import GenerateContentConfig

class DebuggerAgent:
    async def execute(self, state: AgentState):
        task = state['current_task']
        code = state['code_content']
        filename = task['file']
        
        # 1. Save Initial Draft
        file_tools.write_file(filename, code)
        created_files = state.get('created_files', [])
        if filename not in created_files:
            created_files.append(filename)

        # 2. Syntax Check (ONLY FOR PYTHON)
        if not filename.endswith(".py"):
            plan = state['plan']
            task['status'] = 'done'
            updated_plan = [t if t['file'] != task['file'] else task for t in plan]
            return {
                "plan": updated_plan, 
                "error_logs": "",
                "created_files": created_files,
                "retry_count": 0,
                "logs": [f"✅ Verified: {filename} (Non-Python file skipped)"]
            }

        try:
            compile(code, filename, 'exec')
            # ✅ Success from Start (Gemini เขียนถูก)
            plan = state['plan']
            task['status'] = 'done'
            updated_plan = [t if t['file'] != task['file'] else task for t in plan]
            return {
                "plan": updated_plan, 
                "error_logs": "",
                "created_files": created_files,
                "retry_count": 0,
                "logs": [f"✅ Verified: {filename} (Gemini Passed)"]
            }
        # ... (အပေါ်က try: compile(...) အပိုင်းက ဒီတိုင်းထားမယ်) ...

        except Exception as e:
            initial_error = str(e)
            print(f"⚠️ Stage 1: Syntax Check Failed ({initial_error}). Asking Gemini Flash to fix...")

        # 🚨 FIXED: Only use Gemini Flash (No Sonnet/Opus)
        # Budget Save ဖြစ်အောင် Google Gemini ကိုပဲ သုံးပါမယ်။
        
        try:
            client = llm_engine.get_gemini_client()
            
            prompt_fix = f"""
            You are a Senior Python Expert. Fix the following code.
            
            ERROR: {initial_error}
            
            BROKEN CODE:
            ```python
            {code}
            ```
            
            INSTRUCTION:
            - Return ONLY the fixed code inside ```python ... ``` block.
            - Do NOT explain. Just fix the syntax/logic error.
            """
            
            # Gemini Call
            response = client.models.generate_content(
                model=settings.MODEL_CODER, # Gemini 3 Flash
                contents=prompt_fix,
                config=GenerateContentConfig(temperature=0.2)
            )
            
            fixed_code = response.text
            
            # Cleaning Code
            if "```" in fixed_code:
                parts = fixed_code.split("```")
                if len(parts) > 1:
                    fixed_code = parts[1]
                    if fixed_code.startswith("python"): fixed_code = fixed_code[6:]
                    fixed_code = fixed_code.strip()
            
            # Syntax Check Again
            compile(fixed_code, filename, 'exec')
            
            # Save Fixed File
            file_tools.write_file(filename, fixed_code)
            print(f"✅ Debugger: Gemini Flash fixed {filename}")
            
            plan = state['plan']
            task['status'] = 'done'
            updated_plan = [t if t['file'] != task['file'] else task for t in plan]
            
            return {
                "code_content": fixed_code,
                "plan": updated_plan, 
                "error_logs": "",
                "created_files": created_files,
                "retry_count": 0,
                "logs": [f"✅ Debugger: Gemini Flash fixed {filename}"]
            }

        except Exception as gemini_err:
            print(f"💀 Debugger Failed: {gemini_err}")
            return {
                "error_logs": f"Fix Failed: {str(gemini_err)}. \nOriginal: {initial_error}",
                "logs": [f"❌ Debugger could not fix {filename}."] 
            }