from src.core.state import AgentState

class TechLeadAgent:
    async def execute(self, state: AgentState):
        plan = state['plan']
        error_logs = state.get('error_logs', "")
        retry_count = state.get('retry_count', 0)

        # 🔥 FIX: Error ပါလာရင် Task အသစ်ပြန်ဖန်တီးမယ် (Self-Healing Logic)
        if error_logs and retry_count < 3: # ၃ ခါထိ ပြန်ကြိုးစားခွင့်ပေးမယ်
            print(f"🔄 Self-Healing Triggered! (Attempt {retry_count+1}/3)")
            
            # Error ကိုပြင်ဖို့ Task အသစ်လုပ်မယ်
            fix_task = {
                "file": "error_fix_strategy.md", # Logic စဉ်းစားခိုင်းတာ
                "description": f"Analyze this deployment error and FIX the code/structure. ERROR: {error_logs}",
                "status": "pending"
            }
            
            # Plan ရဲ့ ထိပ်ဆုံးမှာ ထည့်လိုက်မယ် (Priority)
            plan.insert(0, fix_task)
            
            return {
                "current_task": None, # Reset လုပ်
                "plan": plan,
                "retry_count": retry_count + 1,
                "error_logs": "", # Error ကို ယူသုံးပြီးပြီမို့ ရှင်းလိုက်မယ်
                "logs": [f"⚠️ Error Detected. Adding fix task..."]
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