import os
import glob

class FileTools:
    def __init__(self, work_dir="/app/workspace"):
        self.work_dir = work_dir
        os.makedirs(self.work_dir, exist_ok=True)

    def write_file(self, filename: str, content: str) -> str:
        try:
            filepath = os.path.join(self.work_dir, filename)
            # Folder မရှိရင် ဆောက်မယ်
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            # Memory Update (Optional hook)
            return f"✅ File created: {filename}"
        except Exception as e:
            return f"❌ Write Error: {str(e)}"

    def read_file(self, filename: str) -> str:
        try:
            filepath = os.path.join(self.work_dir, filename)
            if not os.path.exists(filepath):
                return "❌ File not found."
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            return f"❌ Read Error: {str(e)}"

    def delete_file(self, filename: str) -> str:
        """စမ်းပြီးရင် ပြန်ဖျက်ဖို့ သုံးမည့် Tool"""
        try:
            filepath = os.path.join(self.work_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return f"🗑️ Deleted: {filename}"
            return "⚠️ File not found to delete."
        except Exception as e:
            return f"❌ Delete Error: {str(e)}"

    def get_project_structure(self) -> str:
        """
        Context ကိုင်နိုင်အောင် Project တစ်ခုလုံးကို Scan ဖတ်ပေးမည့် Tool.
        ဖိုင်နာမည်တွေတင်မကဘဲ File Size ပါ ထည့်ပေးမယ်။
        """
        structure = []
        # Walk through directory
        for root, dirs, files in os.walk(self.work_dir):
            for file in files:
                if file.startswith('.'): continue # hidden files ကျော်မယ်
                
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, self.work_dir)
                
                try:
                    size = os.path.getsize(path)
                    structure.append(f"- {rel_path} ({size} bytes)")
                except:
                    structure.append(f"- {rel_path} (Unknown size)")
                    
        return "\n".join(structure) if structure else "Empty Workspace"

# Helper instance
file_tools = FileTools()