import subprocess
import os

class SystemTools:
    def __init__(self, work_dir="/app/workspace"):
        self.work_dir = work_dir
        # Workspace folder မရှိရင် အလိုအလျောက်ဆောက်မယ်
        os.makedirs(self.work_dir, exist_ok=True)

    def execute_command(self, command: str) -> str:
        """
        Runs a shell command safely.
        
        Args:
            command (str): The shell command to run.
        """
        try:
            # Security Block: အန္တရာယ်ရှိတဲ့ Command တွေကို ပိတ်ပင်မယ်
            if any(x in command for x in ["rm -rf /", ":(){ :|:& };:"]):
                return "❌ Command blocked for security reasons."

            # Command ကို Run မယ် (Timeout 60 စက္ကန့်)
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=60,
                cwd=self.work_dir
            )
            
            # Result ပြန်ပို့မယ်
            if result.returncode == 0:
                return f"✅ Output:\n{result.stdout}"
            else:
                return f"❌ Error:\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "❌ Error: Command timed out after 60 seconds."
        except Exception as e:
            return f"System Error: {str(e)}"