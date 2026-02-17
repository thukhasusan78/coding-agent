from langgraph.graph import StateGraph, END
from src.core.state import AgentState
from src.core.llm import llm_engine
from config.settings import settings

# Agent တွေကို Import လုပ်မယ်
from src.agents.architect import ArchitectAgent
from src.agents.tech_lead import TechLeadAgent
from src.agents.coder import CoderAgent
from src.agents.debugger import DebuggerAgent
from src.agents.deployer import DeployerAgent
from src.agents.tester import TesterAgent
import asyncio
from src.core.notifier import notifier
from google.genai.types import GenerateContentConfig, HttpOptions, HttpRetryOptions

# Agent Instance တွေ ဆောက်မယ်
architect = ArchitectAgent()
tech_lead = TechLeadAgent()
coder = CoderAgent()
debugger = DebuggerAgent()
deployer = DeployerAgent()
tester = TesterAgent()

# --- Router Logic (New) ---
def intent_analyzer(state: AgentState):
    """Entry Node: User ရဲ့ ရည်ရွယ်ချက်ကို သုံးသပ်မည့် နေရာ"""
    print(f"🚦 Analyzing Intent: '{state['mission']}'")
    return state

def route_init(state: AgentState):
    """
    Jarvis Router: User ရည်ရွယ်ချက်ကို Gemini Flash သုံးပြီး ခွဲခြားမယ်။
    """
    mission = state['mission']
    print(f"🚦 Jarvis Router: Analyzing '{mission}'...")

    try:
        # 🔥 FIX 1: Get Key manually to pass into Client options
        current_key = llm_engine.key_manager.get_next_key()
        
        # 🔥 FIX 2: Create Client with NO AUTO RETRY
        client = genai.Client(
            api_key=current_key,
            http_options=HttpOptions(
                retry_options=HttpRetryOptions(attempts=1) # 🛑 ONE SHOT ONLY
            )
        )
        
        prompt = f"""
        Analyze User Input and classify into ONE category:

        1. DEPLOY
           - Keywords: "run", "start", "restart", "launch", "give me link", "is it running?"
           - Intent: Execute/View app. NO coding.

        2. CHAT
           - Keywords: "hello", "hi", "how are you", "thanks", "who are you", "explain", "help"
           - Intent: General conversation, greeting, or non-coding questions.

        3. ARCHITECT
           - Default for everything else.

        User Input: "{mission}"
        Instruction: Output ONLY the category name (DEPLOY, CHAT, or ARCHITECT).
        """
        
        # 🔥 FIX 3: Disable AFC (Function Calling)
        response = client.models.generate_content(
            model=settings.MODEL_CODER, 
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.1,
                tools=[], 
                tool_config={'function_calling_config': {'mode': 'NONE'}} # 🛑 NO TOOLS
            )
        )
        
        decision = response.text.strip().upper()
        print(f"🤖 Jarvis Decision: {decision}")
        
        if "DEPLOY" in decision:
            return "deployer"
        
        elif "CHAT" in decision:
            print("💬 Chat Mode Detected. Replying directly...")
            
            chat_prompt = f"""
            You are Jarvis, an AI Software Engineer. 
            User said: "{mission}"
            Reply nicely in Burmese (Myanmar).
            """
            
            reply = client.models.generate_content(
                model=settings.MODEL_CODER, 
                contents=chat_prompt,
                config=GenerateContentConfig(
                    temperature=0.7,
                    tools=[],
                    tool_config={'function_calling_config': {'mode': 'NONE'}}
                )
            )
            
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(notifier.send_status(f"💬 Jarvis: {reply.text}"))
            except: pass
            
            return END 
            
        else:
            return "architect"

    except Exception as e:
        print(f"⚠️ Router Error: {e}. Defaulting to Architect.")
        # Error တက်ရင် Architect ဆီပဲ လွှတ်လိုက်မယ် (System မရပ်သွားအောင်)
        return "architect"

# --- Flow Logic ---
def route_tech_lead(state: AgentState):
    """Tech Lead က ဆုံးဖြတ်မယ်: Task ကျန်သေးလား? ပြီးပြီလား?"""
    
    # 🔥 FIX: အကယ်၍ Tech Lead က 'Critical Failure' နဲ့ ပြီးသွားရင် Deploy ဆီမပို့တော့ဘဲ ဇာတ်သိမ်းမယ်
    final_report = state.get("final_report", "")
    if "Critical Failure" in final_report:
        return END

    if state.get("current_task"):
        return "coder"
    else:
        return "deployer"

def route_tester(state: AgentState):
    """Tester က Error တွေ့ရင် Tech Lead ဆီပြန်၊ မတွေ့ရင် Deployer ဆီဆက်သွား"""
    if state.get("error_logs"):
        return "tech_lead" # ❌ Fail -> Fix
    else:
        return "deployer"        

def route_deployment(state: AgentState):
    """Deployer က Error ပြန်ပို့ရင် Tech Lead ဆီပြန်သွား၊ မဟုတ်ရင် ပြီးမယ်"""
    if state.get("error_logs"):
        return "tech_lead" # 🔄 Loop Back
    else:
        return END # ✅ Finish        

# --- Graph Construction ---
workflow = StateGraph(AgentState)

# Node တွေ ထည့်မယ်
workflow.add_node("architect", architect.execute)
workflow.add_node("tech_lead", tech_lead.execute)
workflow.add_node("coder", coder.execute)
workflow.add_node("debugger", debugger.execute)
workflow.add_node("tester", tester.execute)
workflow.add_node("deployer", deployer.execute)

# လမ်းကြောင်းတွေ ဆက်မယ် (Edges)
workflow.add_node("intent_analyzer", intent_analyzer)

# 🔥 FIX: ဝင်ဝင်ချင်း Architect ဆီမသွားဘဲ Router ဆီ အရင်သွားမယ်
workflow.set_entry_point("intent_analyzer")

# Router ကနေ လမ်းခွဲမယ် (Conditional Edges)
workflow.add_conditional_edges(
    "intent_analyzer",
    route_init,
    {
        "architect": "architect", # Code ရေးစရာရှိရင် ဒီလမ်း
        "deployer": "deployer",    # Run ရုံဆိုရင် Express လမ်း
        END: END
    }
)

workflow.add_edge("architect", "tech_lead")

# ✅ ဒီလိုလေး ပြောင်းလိုက်ပါ
workflow.add_conditional_edges(
    "tech_lead",
    route_tech_lead
    # Dictionary မထည့်တော့ဘူး (Auto detect လုပ်ခိုင်းမယ်)
)

# Coder -> Debugger (ရေးပြီးရင် အမှားစစ်)
workflow.add_edge("coder", "debugger")

workflow.add_edge("debugger", "tester")

workflow.add_conditional_edges(
    "tester",
    route_tester,
    {
        "tech_lead": "tech_lead", # Error ရှိရင် ပြန်ပြင်
        "deployer": "deployer"   
    }
)

# 🔥 FIX: Deployer ပြီးရင် အခြေအနေကြည့်ပြီး လမ်းခွဲမယ်
workflow.add_conditional_edges(
    "deployer",
    route_deployment,
    {
        "tech_lead": "tech_lead", # Error တက်ရင် ပြန်သွား
        END: END                  # အဆင်ပြေရင် ပြီးမယ်
    }
)