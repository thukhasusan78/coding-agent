import sys
import time

class JarvisGreetingApp:
    """
    Main application class for the Jarvis Greeting Application.
    Handles the interactive loop, user input processing, and system responses.
    """
    
    def __init__(self):
        self.identity = "Jarvis"
        self.version = "1.0.0"
        self.is_active = True
        self.start_time = time.time()

    def _simulate_processing(self, duration: float = 0.5):
        """Simulates a brief delay to mimic AI processing."""
        print(f"{self.identity}: Thinking...", end="\r")
        time.sleep(duration)
        # Clear the thinking line
        sys.stdout.write("\033[K")

    def startup_sequence(self):
        """Displays the initial startup message."""
        print("=" * 50)
        print(f"{self.identity} Greeting System v{self.version}")
        print("Status: ONLINE")
        print("=" * 50)
        time.sleep(0.5)
        print(f"\n{self.identity}: At your service, sir. How may I help you today?")

    def process_command(self, user_input: str):
        """
        Logic to handle various user inputs.
        
        Args:
            user_input (str): The raw string input from the user.
        """
        cmd = user_input.lower().strip()

        # Exit conditions
        if cmd in ["exit", "quit", "shutdown", "bye", "goodbye"]:
            print(f"{self.identity}: Very well. Powering down systems. Goodbye, sir.")
            self.is_active = False
            return

        self._simulate_processing()

        # Response logic
        if any(greet in cmd for greet in ["hello", "hi", "greetings"]):
            print(f"{self.identity}: Hello! I am fully operational and ready for your instructions.")
        
        elif "who are you" in cmd:
            print(f"{self.identity}: I am {self.identity}, a greeting application designed to provide a sophisticated interface experience.")
            
        elif "status" in cmd or "system" in cmd:
            uptime = round(time.time() - self.start_time, 2)
            print(f"{self.identity}: All systems are nominal. Uptime: {uptime} seconds.")
            
        elif "time" in cmd:
            current_time = time.strftime("%H:%M:%S")
            print(f"{self.identity}: The current system time is {current_time}.")
            
        elif not cmd:
            pass
            
        else:
            print(f"{self.identity}: I'm afraid my current protocols don't cover that request. I can handle greetings, status checks, and time requests.")

    def run(self):
        """The main interactive loop."""
        self.startup_sequence()
        
        while self.is_active:
            try:
                # Prompt for user input
                user_input = input("\nUser > ")
                
                if not user_input.strip():
                    continue
                    
                self.process_command(user_input)
                
            except KeyboardInterrupt:
                print(f"\n\n{self.identity}: Manual override detected. Emergency shutdown initiated.")
                self.is_active = False
            except Exception as e:
                print(f"\n{self.identity}: An internal error has occurred: {e}")
                self.is_active = False

        print("\n[System Terminated]")

if __name__ == "__main__":
    # Initialize and run the application
    app = JarvisGreetingApp()
    app.run()