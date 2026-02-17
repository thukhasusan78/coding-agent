import asyncio
import socket
import time
from google import genai
from google.genai.types import GenerateContentConfig
from src.core.state import AgentState
from src.core.llm import llm_engine
from config.settings import settings
from src.tools.files import file_tools

# 🚑 NETWORK FIX: Smart IPv4 Patch
# VPS တွေမှာ Google API ခေါ်ရင် IPv6 ကြောင့် Connection လေးတာ/ပြုတ်ကျတာ ဖြစ်တတ်ပါတယ်။
# IPv4 ကို ဦးစားပေးပြီး၊ မရမှ IPv6 သုံးမယ့် Hybrid Patch ပါ။
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    ipv4 = [r for r in responses if r[0] == socket.AF_INET]
    return ipv4 if ipv4 else responses
socket.getaddrinfo = new_getaddrinfo

class CoderAgent:
    async def execute(self, state: AgentState):
        task = state['current_task']
        existing_code = file_tools.read_file(task['file'])
        structure = file_tools.get_project_structure()
        
        if "Error" in existing_code: existing_code = ""

        print(f"⚡ Coder ({settings.MODEL_CODER_NAME}): Started coding {task['file']}...")

        prompt = f"""
        You are a Senior Python Developer.
        Task: {task['description']}
        File: {task['file']}
        Context: {structure}
        Current Code: {existing_code}
        Errors: {state.get('error_logs', 'None')}
        Requirement: Write the COMPLETE code inside ```python ... ``` (or relevant language) block.
        """
        
        code = ""
        
        # 🔥 FIX: No complicated HttpOptions. Just raw, simple Client.
        # Retry ကို ကိုယ့်ဘာသာ Loop နဲ့ထိန်းမယ်။
        
        for attempt in range(settings.MAX_RETRIES):
            try:
                # 1. Get Key
                current_key = llm_engine.key_manager.get_next_key()
                
                # 2. Sync Client (Purer & More Stable on VPS)
                client = genai.Client(api_key=current_key)

                # 3. Config to KILL AFC (Function Calling)
                # Dictionary style config is safer than importing types
                config = GenerateContentConfig(
                    temperature=0.2,
                    tools=[], 
                    tool_config={
                        'function_calling_config': {
                            'mode': 'NONE' # 🛑 This strictly disables AFC logs
                        }
                    },
                    system_instruction="You are a coding engine. Output only code."
                )

                # 4. Run Sync Call in Thread (Non-blocking)
                # Thread ထဲမှာ run တာမို့ Main Loop မရပ်ဘူး၊ Timeout ပြဿနာကင်းမယ်
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=settings.MODEL_CODER_NAME,
                    contents=prompt,
                    config=config
                )
                
                # 5. Validate Response
                if not response.text:
                    if response.candidates and response.candidates[0].content.parts:
                        code = response.candidates[0].content.parts[0].text
                    else:
                        raise Exception("Empty response (Possible Safety Filter)")
                else:
                    code = response.text

                print(f"✅ Coder: Success with Key ...{current_key[-4:]}")
                break 

            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Attempt {attempt+1} Failed: {error_msg}")
                
                # Backup Logic (Gemini 2.0 Flash)
                if "503" in error_msg or "429" in error_msg or "deadline" in error_msg.lower():
                    if attempt == settings.MAX_RETRIES - 1:
                        print("❌ Switching to Backup Model (Gemini 2.0 Flash)...")
                        try:
                            # Backup call (also in thread)
                            backup_resp = await asyncio.to_thread(
                                client.models.generate_content,
                                model="gemini-2.5-flash", 
                                contents=prompt,
                                config=config
                            )
                            code = backup_resp.text
                            break
                        except Exception as backup_err:
                            print(f"❌ Backup Failed: {backup_err}")
                
                # Smart Delay
                await asyncio.sleep(2 ** attempt)

        # Code Parsing Logic
        if code and "```" in code:
            parts = code.split("```")
            if len(parts) > 1:
                code = parts[1]
                if code.startswith("python"): code = code[6:]
                elif code.startswith("html"): code = code[4:]
                elif code.startswith("css"): code = code[3:]
                elif code.startswith("javascript"): code = code[10:]
                elif code.startswith("js"): code = code[2:]
                code = code.strip()
            
        return {"code_content": code}