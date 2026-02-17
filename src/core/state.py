from typing import TypedDict, List, Annotated
import operator

# Task တစ်ခုရဲ့ ပုံစံ
class Task(TypedDict):
    file: str
    description: str
    status: str  # pending, coding, done

# Agent တစ်ခုလုံးရဲ့ မှတ်ဉာဏ်ပုံစံ
class AgentState(TypedDict):
    mission: str                    # User ခိုင်းလိုက်တဲ့ အလုပ်
    plan: List[Task]                # လုပ်ရမယ့် Task စာရင်း
    current_task: Task              # လက်ရှိလုပ်နေတဲ့ Task
    code_content: str               # ရေးပြီးသား Code
    error_logs: str                 # Error တက်ခဲ့ရင် မှတ်ဖို့
    retry_count: int                # ဘယ်နှခါ ပြန်ကြိုးစားပြီးပြီလဲ
    cleanup_needed: bool            # အဟောင်းဖျက်ဖို့ လိုလား
    created_files: List[str]        # ဖန်တီးလိုက်တဲ့ ဖိုင်စာရင်း
    subdomain: str                  # Web App နာမည် (URL အတွက်)
    final_report: str               # နောက်ဆုံး User ကို ပြမယ့်စာ
    logs: Annotated[List[str], operator.add] # Log တွေ ပေါင်းထည့်သွားမယ်