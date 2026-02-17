import subprocess
import os
import signal
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class ProcessManager:
    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}

    def run_script(self, command: str, name: str, cwd: str = "./workspace"):
        """
        Runs a local shell command/script in background
        """
        try:
            # Stop existing if any
            self.stop_process(name)

            log_file = open(f"{cwd}/{name}.log", "w")
            
            # Spawn Process
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid # Create new session group
            )
            
            self.active_processes[name] = process
            logger.info(f"⚙️ Process started: {name} (PID: {process.pid})")
            return f"✅ Script '{name}' running in background (PID: {process.pid})"

        except Exception as e:
            return f"❌ Process Start Error: {e}"

    def stop_process(self, name: str):
        if name in self.active_processes:
            proc = self.active_processes[name]
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                del self.active_processes[name]
                return f"🛑 Process {name} stopped."
            except Exception as e:
                return f"⚠️ Error killing process: {e}"
        return "Process not found."

process_mgr = ProcessManager()