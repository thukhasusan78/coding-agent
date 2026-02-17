from src.core.state import AgentState

class TechLeadAgent:
    async def execute(self, state: AgentState):
        plan = state['plan']
        error_logs = state.get('error_logs', "")
        retry_count = state.get('retry_count', 0)

        # 🔥 FIX: Error ပါလာရင် Task အသစ်ပြန်ဖန်တီးမယ် (Self-Healing Logic)
        if error_logs:
            if retry_count < 3:
                print(f"🔄 Self-Healing Triggered! (Attempt {retry_count+1}/3)")
                
                # Error ကိုပြင်ဖို့ Task အသစ်လုပ်မယ် (ပိုတိကျတဲ့ Task ပေးမယ်)
                fix_task = {
                    "file": "error_fix_strategy.md", 
                    "description": f"CRITICAL: The previous deployment failed. Analyze logs, adjust code/requirements, and RETRY. ERROR: {error_logs}",
                    "status": "pending"
                }
                
                plan.insert(0, fix_task)
                
                return {
                    "current_task": None,
                    "plan": plan,
                    "retry_count": retry_count + 1,
                    "error_logs": "",
                    "logs": [f"⚠️ Error Detected. Adding fix task (Attempt {retry_count+1})..."]
                }
            
            else:
                # 🛑 Circuit Breaker: ၃ ခါကြိုးစားလို့မရရင် "လက်မြှောက်" မယ့် Logic
                print("🛑 Max Retries Reached. Stopping Loop.")
                error_msg = f"💥 Critical Failure: Tried to fix 3 times but failed. STOPPING to prevent infinite loop.\nLast Error: {error_logs[:500]}..."
                
                return {
                    "current_task": None,
                    "plan": [], 
                    "final_report": error_msg, # 🔥 Signal ပေးလိုက်ပြီ
                    "logs": [error_msg]
                }
        # ပြီးပြီးသားမဟုတ်တဲ့ Task တစ်ခုကို ယူမယ်
        next_task = next((t for t in plan if t['status'] == 'pending'), None)
        
        if next_task:
            next_task['status'] = 'coding'
            # Plan ထဲမှာ Status လိုက်ပြောင်းမယ်
            updated_plan = [t if t['file'] != next_task['file'] else next_task for t in plan]
            return {
                "current_task": next_task,
                "plan": updated_plan,
                "retry_count": 0,
                "error_logs": "",
                "logs": [f"👉 Assigning Task: {next_task['file']}"]
            }
        else:
            return {"current_task": None}