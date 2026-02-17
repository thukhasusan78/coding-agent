import json
from src.core.state import AgentState
from src.core.llm import llm_engine
from config.settings import settings
from src.tools.files import file_tools

class ReviewerAgent:
    async def execute(self, state: AgentState):
        """
        Code Quality & Security Check (Batch Mode)
        API Call သက်သာအောင် ဖိုင်အားလုံးပေါင်းပြီး တစ်ခါတည်းစစ်မယ်
        """
        logs = state.get('logs', [])
        # Architect/Coder ဖန်တီးခဲ့တဲ့ ဖိုင်စာရင်းကို ယူမယ်
        created_files = state.get('created_files', [])
        
        # ဖိုင်မရှိရင် ဘာမှလုပ်စရာမလို
        if not created_files:
            logs.append("⚠️ Reviewer: No created files found to review.")
            return {"logs": logs}

        print(f"🧐 Reviewer: Batch auditing {len(created_files)} files...")
        logs.append(f"🧐 Reviewer: Started batch audit for {len(created_files)} files.")
        
        # ၁။ ဖိုင်အားလုံးကို ဖတ်ပြီး စာတစ်စောင်တည်းဖြစ်အောင် ပေါင်းမယ်
        combined_code_context = ""
        for file_path in created_files:
            content = file_tools.read_file(file_path)
            # ဖိုင်တစ်ခုချင်းစီကို ခေါင်းစဉ်တပ်ပြီး ပေါင်းထည့်
            combined_code_context += f"\n\n=== START FILE: {file_path} ===\n{content}\n=== END FILE: {file_path} ===\n"

        # ၂။ Prompt (Claude အတွက်)
        prompt = f"""
        You are a Senior Code Reviewer & Security Auditor.
        Review the following codebase containing multiple files.
        
        Your Goals:
        1. SECURITY: Detect hardcoded API keys, SQL Injection, RCE vulnerabilities.
        2. CRITICAL BUGS: Detect syntax errors, infinite loops, or logic flaws.
        3. QUALITY: Briefly comment on code structure.
        
        CODEBASE:
        {combined_code_context[:80000]} 
        (Note: Context limited to first 80k chars to prevent overload)
        
        INSTRUCTIONS:
        - Return a JSON summary of issues.
        - DO NOT rewrite the code unless there is a CRITICAL Security Risk.
        - If everything is safe, return status "PASS".
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "status": "PASS" or "FAIL",
            "critical_issues": ["filename.py: line X - Issue description"],
            "summary": "Brief review summary..."
        }}
        """

        try:
            # Reviewer အတွက် Claude (OpenRouter) ကိုသုံးမယ်
            client = llm_engine.get_openrouter_client()
            response = await client.chat.completions.create(
                model=settings.MODEL_ARCHITECT, # Architect Model (Sonnet) is best for reviewing
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            # JSON result ကို ခွဲထုတ်မယ်
            content = response.choices[0].message.content
            result = json.loads(content)
            
            status = result.get("status", "UNKNOWN")
            issues = result.get("critical_issues", [])
            summary = result.get("summary", "No summary provided.")

            # Logs ထဲမှတ်တမ်းတင်မယ်
            logs.append(f"✨ Review Complete. Status: {status}")
            logs.append(f"📝 Summary: {summary}")
            
            if issues:
                logs.append("⚠️ Critical Issues Found:")
                for issue in issues:
                    logs.append(f" - {issue}")
            else:
                logs.append("✅ No critical issues found. Code is safe.")

            # Note: Batch Review မှာ Code ကို Auto Fix မလုပ်တော့ပါဘူး (API Key မပေါက်ရင် ပြီးရော)
            # လိုအပ်ရင် Coder ကို ပြန်ပြင်ခိုင်းတဲ့ Logic နောက်မှထည့်လို့ရပါတယ်

        except Exception as e:
            error_msg = f"❌ Reviewer Error: {str(e)}"
            print(error_msg)
            logs.append(error_msg)

        # State ပြန်ပို့
        return {
            "logs": logs,
            "error_logs": "" 
        }