import threading
import time
from datetime import datetime

def print_jarvis_status():
    """
    Background task that prints a greeting and the current timestamp every 5 seconds.
    """
    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Hello Jarvis | Current Time: {current_time}")
        time.sleep(5)

def main():
    """
    Initializes and starts the background thread.
    """
    # Initialize the background thread
    # daemon=True ensures the thread exits when the main program terminates
    timer_thread = threading.Thread(target=print_jarvis_status, daemon=True)
    
    print("Starting Jarvis Timer Service (Press Ctrl+C to stop)...")
    timer_thread.start()

    try:
        # Keep the main thread alive while the background thread runs
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nJarvis Timer Service stopped.")

if __name__ == "__main__":
    main()