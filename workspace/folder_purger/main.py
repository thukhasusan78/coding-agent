import os
import shutil
import logging

# Configure logging to track the deletion process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def purge_directories(target_names, start_path='.'):
    """
    Recursively searches for and deletes directories matching the target names.
    
    Args:
        target_names (list): List of directory names to identify and remove.
        start_path (str): The root directory to start the search from.
    """
    abs_start_path = os.path.abspath(start_path)
    logging.info(f"Starting purge operation in: {abs_start_path}")

    # Walk through the filesystem
    # topdown=True allows us to modify 'dirs' in-place to prevent os.walk 
    # from attempting to visit subdirectories of a folder we just deleted.
    for root, dirs, files in os.walk(abs_start_path, topdown=True):
        for dir_name in list(dirs):
            if dir_name in target_names:
                full_path = os.path.join(root, dir_name)
                
                try:
                    logging.info(f"Attempting to delete: {full_path}")
                    shutil.rmtree(full_path)
                    
                    # Remove from dirs list so os.walk doesn't try to traverse it
                    dirs.remove(dir_name)
                    logging.info(f"Successfully removed: {full_path}")
                    
                except PermissionError:
                    logging.error(f"Permission denied: Could not delete {full_path}")
                except OSError as e:
                    logging.error(f"OS Error occurred while deleting {full_path}: {e}")
                except Exception as e:
                    logging.error(f"Unexpected error deleting {full_path}: {e}")

if __name__ == "__main__":
    # Define the specific directories to be purged based on the task requirements
    TARGET_DIRECTORIES = [
        'container_killer_v1',
        'hello_jarvis_v1'
    ]

    # Execute the purge starting from the current working directory
    purge_directories(TARGET_DIRECTORIES)
    logging.info("Cleanup operation completed.")