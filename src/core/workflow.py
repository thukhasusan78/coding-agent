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
from src.agents.reviewer import ReviewerAgent
from src.agents.tester import TesterAgent

# Agent Instance တွေ ဆောက်မယ်
architect = ArchitectAgent()
tech_lead = TechLeadAgent()
coder = CoderAgent()
debugger = DebuggerAgent()
deployer = DeployerAgent()
reviewer = ReviewerAgent()
tester = TesterAgent()

# --- Router Logic (New) ---
def intent_analyzer(state: AgentState):
    """Entry Node: User ရဲ့ ရည်ရွယ်ချက်ကို သုံးသပ်မည့် နေရာ"""
    print(f"🚦 Analyzing Intent: '{state['mission']}'")
    return state

def route_init(state: AgentState):
    """
    Jarvis Router: User ရည်ရွယ်ချက်ကို Gemini Flash သုံးပြီး ခွဲခြားမယ်။
    Categories:
    - DEPLOY: Run, Start, Link တောင်းတာ (Deployer ဆီသွားမယ်)
    - ARCHITECT: Code ရေး, ပြင်, ရှာဖွေ, စကားပြော (Architect ဆီသွားမယ်)
    """
    mission = state['mission']
    print(f"🚦 Jarvis Router: Analyzing '{mission}'...")

    try:
        # 🔥 Gemini 3 Flash (Coder Model) ကိုသုံးမယ် (Speed & Smart)
        client = llm_engine.get_gemini_client()
        
        prompt = f"""
        You are the intelligent router for an AI Agent. 
        Analyze the User Input and classify it into ONE of these actions:

        1. [DEPLOY]
           - Keywords: "run", "start", "restart", "launch", "give me link", "is it running?"
           - Intent: User wants to execute/view the existing app. NO changes to code.

        2. [ARCHITECT]
           - Keywords: "create", "write", "fix", "change", "update", "debug"
           - Intent: Modifying code or creating new files.
           - Keywords: "search", "research", "browse", "find info"
           - Intent: Gathering information.
           - Keywords: "hello", "hi", "explain", "how are you"
           - Intent: General conversation.

        User Input: "{mission}"

        Instruction: Output ONLY the category name (DEPLOY or ARCHITECT).
        """
        
        # API Call (Fast Sync Call)
        response = client.models.generate_content(
            model=settings.MODEL_CODER, # gemini-3-flash-preview
            contents=prompt
        )
        
        decision = response.text.strip().upper()
        print(f"🤖 Jarvis Decision: {decision}")
        
        # လမ်းကြောင်းခွဲမယ်
        if "DEPLOY" in decision:
            return "deployer"
        else:
            return "architect"

    except Exception as e:
        print(f"⚠️ Router Error: {e}. Defaulting to Architect.")
        return "architect"

# --- Flow Logic ---
def route_tech_lead(state: AgentState):
    """Tech Lead က ဆုံးဖြတ်မယ်: Task ကျန်သေးလား? ပြီးပြီလား?"""
    if state.get("current_task"):
        return "coder"
    else:
        # 🔥 FIX: Task အကုန်ပြီးမှ Reviewer ဆီသွားမယ် (Credit သက်သာအောင်)
        # အရင်က deployer ကိုတန်းသွားတာ၊ အခု reviewer ကိုအရင်ဖြတ်မယ်
        return "reviewer"

def route_tester(state: AgentState):
    """Tester က Error တွေ့ရင် Tech Lead ဆီပြန်၊ မတွေ့ရင် Reviewer ဆီဆက်သွား"""
    if state.get("error_logs"):
        return "tech_lead" # ❌ Fail -> Fix
    else:
        return "reviewer"        

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
workflow.add_node("reviewer", reviewer.execute) 

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
        "deployer": "deployer"    # Run ရုံဆိုရင် Express လမ်း
    }
)

workflow.add_edge("architect", "tech_lead")

workflow.add_conditional_edges(
    "tech_lead",
    route_tech_lead,
    {
        "coder": "coder",
        "reviewer": "reviewer" # 🔥 လမ်းကြောင်းပြောင်းလိုက်သည် (Deployer မဟုတ်တော့ပါ)
    }
)

# Coder -> Debugger (ရေးပြီးရင် အမှားစစ်)
workflow.add_edge("coder", "debugger")

workflow.add_edge("debugger", "tester")

workflow.add_conditional_edges(
    "tester",
    route_tester,
    {
        "tech_lead": "tech_lead", # Error ရှိရင် ပြန်ပြင်
        "reviewer": "reviewer"    # အောင်မြင်ရင် Review ဆက်လုပ်
    }
)

# Reviewer -> Deployer
workflow.add_edge("reviewer", "deployer")

# 🔥 FIX: Deployer ပြီးရင် အခြေအနေကြည့်ပြီး လမ်းခွဲမယ်
workflow.add_conditional_edges(
    "deployer",
    route_deployment,
    {
        "tech_lead": "tech_lead", # Error တက်ရင် ပြန်သွား
        END: END                  # အဆင်ပြေရင် ပြီးမယ်
    }
)