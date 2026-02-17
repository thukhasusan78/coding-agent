import os
import shutil
from pathlib import Path

def cleanup_project():
    """
    Senior Developer Cleanup Utility
    Performs:
    1. Removal of zero-byte deployment logs.
    2. Removal of temporary SQLite files (-wal, -shm).
    3. Optimization of directory structure by clearing non-essential caches.
    """
    # Define the project root relative to this script's location
    # project_cleanup_utility/cleanup.py -> root is parent
    base_dir = Path(__file__).resolve().parent.parent

    print(f"Starting cleanup in: {base_dir}")

    # 1. Remove zero-byte deployment logs
    # Targets: jarvis-timer_deploy.log, background-calculator-v1_deploy.log, etc.
    for log_file in base_dir.glob("*_deploy.log"):
        if log_file.is_file() and log_file.stat().st_size == 0:
            try:
                log_file.unlink()
                print(f"Removed zero-byte log: {log_file.name}")
            except Exception as e:
                print(f"Error removing {log_file.name}: {e}")

    # 2. Remove temporary sqlite-wal and sqlite-shm files
    # Targets: checkpoints.sqlite-wal, checkpoints.sqlite-shm
    sqlite_temp_patterns = ["*.sqlite-wal", "*.sqlite-shm"]
    for pattern in sqlite_temp_patterns:
        for temp_file in base_dir.glob(pattern):
            try:
                temp_file.unlink()
                print(f"Removed SQLite temp file: {temp_file.name}")
            except Exception as e:
                print(f"Error removing {temp_file.name}: {e}")

    # 3. Optimize Project Structure (Clean __pycache__ and .pyc files)
    # We skip 'test_env' to ensure the virtual environment remains functional
    for root, dirs, files in os.walk(base_dir):
        if "test_env" in root:
            continue
            
        # Remove __pycache__ directories
        if "__pycache__" in dirs:
            pycache_path = Path(root) / "__pycache__"
            try:
                shutil.rmtree(pycache_path)
                print(f"Optimized: Removed {pycache_path.relative_to(base_dir)}")
            except Exception as e:
                print(f"Error removing pycache at {root}: {e}")

        # Remove orphaned .pyc files in the current root
        for file in files:
            if file.endswith(".pyc"):
                try:
                    (Path(root) / file).unlink()
                except Exception:
                    pass

    print("Cleanup process completed successfully.")

if __name__ == "__main__":
    cleanup_project()