from src.core.state import AgentState
from src.core.llm import llm_engine
from config.settings import settings
from src.tools.files import file_tools

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
        except Exception as e:
            initial_error = str(e)
            print(f"⚠️ Stage 1: Gemini Failed ({initial_error}). Calling Sonnet 3.5...")

        # 🚨 STAGE 2: CLAUDE 3.5 SONNET
        client = llm_engine.get_openrouter_client()
        
        try:
            prompt_sonnet = f"""
            You are a Senior Python QA. Fix this code.
            Error: {initial_error}
            Code:
            ```python
            {code}
            ```
            Return ONLY fixed code inside ```python ... ``` block.
            """
            response = await client.chat.completions.create(
                model=settings.MODEL_DEBUGGER,
                messages=[{"role": "user", "content": prompt_sonnet}]
            )
            
            fixed_code = response.choices[0].message.content
            # Extract Code
            if "```" in fixed_code:
                fixed_code = fixed_code.split("```")[1]
                if fixed_code.startswith("python"): fixed_code = fixed_code[6:]
                fixed_code = fixed_code.split("```")[0].strip()
            
            compile(fixed_code, filename, 'exec')
            
            file_tools.write_file(filename, fixed_code)
            print(f"✅ Stage 2: Sonnet 3.5 Fixed {filename}")
            
            plan = state['plan']
            task['status'] = 'done'
            updated_plan = [t if t['file'] != task['file'] else task for t in plan]
            return {
                "code_content": fixed_code,
                "plan": updated_plan, 
                "error_logs": "",
                "created_files": created_files,
                "retry_count": 0,
                "logs": [f"✅ Debugger: Sonnet 3.5 fixed {filename}"]
            }

        except Exception as sonnet_err:
            sonnet_error_msg = str(sonnet_err)
            print(f"🔥 Stage 2 Failed ({sonnet_error_msg}). Awakening Opus...")
            
            # 🚨 STAGE 3: CLAUDE OPUS (The Last Resort)
            try:
                prompt_opus = f"""
                You are Claude Opus. Fix this Python code.
                Initial Error: {initial_error}
                Sonnet Error: {sonnet_error_msg}
                Code:
                ```python
                {fixed_code if 'fixed_code' in locals() else code}
                ```
                FIX IT.
                """
                
                response_opus = await client.chat.completions.create(
                    model=settings.MODEL_SUPER,
                    messages=[{"role": "user", "content": prompt_opus}]
                )
                
                opus_code = response_opus.choices[0].message.content
                if "```" in opus_code:
                    opus_code = opus_code.split("```")[1]
                    if opus_code.startswith("python"): opus_code = opus_code[6:]
                    opus_code = opus_code.split("```")[0].strip()

                compile(opus_code, filename, 'exec')

                file_tools.write_file(filename, opus_code)
                print(f"🚀 Stage 3: Opus Saved the day!")
                
                plan = state['plan']
                task['status'] = 'done'
                updated_plan = [t if t['file'] != task['file'] else task for t in plan]
                return {
                    "code_content": opus_code,
                    "plan": updated_plan, 
                    "error_logs": "",
                    "created_files": created_files,
                    "retry_count": 0,
                    "logs": [f"🚀 Debugger: Opus fixed {filename}"]
                }

            except Exception as opus_err:
                print(f"💀 Stage 3 Failed. Circling back to Developer...")
                return {
                    "error_logs": f"Opus Failed: {str(opus_err)}. \nOriginal Error: {initial_error}",
                    "logs": [f"🔄 Debugger Failed. Looping back to Developer."] 
                }