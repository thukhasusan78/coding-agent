import os
import shutil

def perform_cleanup():
    """
    Permanently removes the 'hello_jarvis_v1' directory and the 
    'hello-jarvis-v1_deploy_log' file from the system.
    """
    # Define targets
    target_dir = 'hello_jarvis_v1'
    target_log = 'hello-jarvis-v1_deploy.log'

    print(f"Starting cleanup utility...")

    # Remove the directory and all its contents
    if os.path.exists(target_dir):
        try:
            if os.path.isdir(target_dir):
                shutil.rmtree(target_dir)
                print(f"Successfully removed directory: {target_dir}")
            else:
                os.remove(target_dir)
                print(f"Target '{target_dir}' was a file, removed via os.remove.")
        except Exception as e:
            print(f"Error removing directory {target_dir}: {e}")
    else:
        print(f"Directory '{target_dir}' does not exist. Skipping.")

    # Remove the deployment log file
    if os.path.exists(target_log):
        try:
            os.remove(target_log)
            print(f"Successfully removed file: {target_log}")
        except Exception as e:
            print(f"Error removing file {target_log}: {e}")
    else:
        print(f"File '{target_log}' does not exist. Skipping.")

    print("Cleanup process completed.")

if __name__ == "__main__":
    perform_cleanup()