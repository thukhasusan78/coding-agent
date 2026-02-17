import subprocess
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class GitTools:
    def __init__(self, work_dir="/app"):
        self.work_dir = work_dir
        self.token = os.getenv("GITHUB_TOKEN")
        self.username = os.getenv("GITHUB_USERNAME")
        self.repo_name = os.getenv("GITHUB_REPO_NAME")
        self._run_git(["git", "config", "--global", "--add", "safe.directory", self.work_dir])

    def _run_git(self, command: list) -> str:
        """Internal helper to run git commands safely."""
        try:
            # Git config global ပြင်စရာမလိုအောင် command line ကနေပဲ config ထည့်မယ်
            env = os.environ.copy()
            if self.token:
                # Password prompt မတက်အောင် terminal ကိုပြောမယ်
                env["GIT_TERMINAL_PROMPT"] = "0"

            result = subprocess.run(
                command,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                env=env,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"
        except Exception as e:
            return f"Exception: {str(e)}"

    def setup_remote(self):
        """Configures the remote URL with the Token for password-less push."""
        if not self.token or not self.username or not self.repo_name:
            return "⚠️ GitHub Token/Username missing in .env"

        # Construct Secure URL: https://TOKEN@github.com/user/repo.git
        auth_url = f"https://{self.username}:{self.token}@github.com/{self.username}/{self.repo_name}.git"
        
        # Remove existing origin to avoid duplicates
        self._run_git(["git", "remote", "remove", "origin"])
        
        # Add new authenticated origin
        res = self._run_git(["git", "remote", "add", "origin", auth_url])
        
        # Ensure we are on main branch
        self._run_git(["git", "branch", "-M", "main"])
        
        return "✅ Remote configured with Token."

    def auto_push(self, message: str = "Auto-update by Jarvis") -> str:
        """
        Stages, commits, and pushes code to GitHub automatically.
        """
        # 1. Setup Remote (Just in case)
        self.setup_remote()

        # 2. Check status
        status = self._run_git(["git", "status", "--porcelain"])
        if not status:
            return "✅ Git: No changes to push."

        # 3. Add all changes
        self._run_git(["git", "add", "."])
        
        # 4. Commit
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"{message} [{timestamp}]"
        self._run_git(["git", "config", "user.email", "jarvis@ironman.ai"])
        self._run_git(["git", "config", "user.name", "Jarvis Agent"])
        
        commit_res = self._run_git(["git", "commit", "-m", commit_msg])
        
        # 5. Push (Token URL will be used)
        push_res = self._run_git(["git", "push", "-u", "origin", "main"])
        
        if "Error" in push_res:
             # Sometimes 'everything up-to-date' is returned as error or info
             if "up-to-date" in push_res:
                 return "✅ Git: Everything up-to-date."
             return f"⚠️ Push failed:\n{push_res}"
             
        return f"🚀 Git Push Success!\nCommit: {commit_msg}"