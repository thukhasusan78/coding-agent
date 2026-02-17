import tkinter as tk
from tkinter import messagebox
import threading
import sys
import os
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis Calculator")
        self.root.geometry("320x450")
        self.root.resizable(False, False)
        
        # Background Service State
        self.is_hidden = False
        
        # Calculator Logic Variables
        self.expression = ""
        self.display_var = tk.StringVar(value="0")
        
        self._setup_ui()
        self._setup_tray()
        
        # Handle window close button
        self.root.protocol("WM_DELETE_WINDOW", self.withdraw_window)

    def _setup_ui(self):
        """Initialize the Tkinter GUI components."""
        # Display Screen
        display_frame = tk.Frame(self.root, bg="#2c3e50", bd=10)
        display_frame.pack(expand=True, fill="both")
        
        display_label = tk.Entry(
            display_frame, 
            textvariable=self.display_var, 
            font=("Arial", 24, "bold"), 
            bg="#ecf0f1", 
            fg="#2c3e50", 
            justify="right", 
            bd=0
        )
        display_label.pack(expand=True, fill="both", padx=5, pady=5)

        # Buttons Grid
        buttons_frame = tk.Frame(self.root, bg="#34495e")
        buttons_frame.pack(expand=True, fill="both")

        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            'C', '0', '=', '+'
        ]

        row = 0
        col = 0
        for button in buttons:
            action = lambda x=button: self.on_button_click(x)
            tk.Button(
                buttons_frame, 
                text=button, 
                width=5, 
                height=2, 
                font=("Arial", 14, "bold"),
                bg="#95a5a6" if not button.isdigit() else "#ecf0f1",
                command=action
            ).grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            
            col += 1
            if col > 3:
                col = 0
                row += 1

        for i in range(4):
            buttons_frame.grid_columnconfigure(i, weight=1)
        for i in range(4):
            buttons_frame.grid_rowconfigure(i, weight=1)

    def on_button_click(self, char):
        """Handle calculator button logic."""
        if char == 'C':
            self.expression = ""
            self.display_var.set("0")
        elif char == '=':
            try:
                # Basic sanitization and evaluation
                result = str(eval(self.expression.lstrip('0')))
                self.display_var.set(result)
                self.expression = result
            except ZeroDivisionError:
                messagebox.showerror("Error", "Cannot divide by zero")
                self.expression = ""
                self.display_var.set("0")
            except Exception:
                messagebox.showerror("Error", "Invalid Expression")
                self.expression = ""
                self.display_var.set("0")
        else:
            self.expression += str(char)
            self.display_var.set(self.expression)

    def _create_tray_icon(self):
        """Generate a simple icon for the system tray."""
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color=(52, 152, 219))
        dc = ImageDraw.Draw(image)
        dc.rectangle([16, 16, 48, 48], fill=(236, 240, 241))
        return image

    def _setup_tray(self):
        """Initialize the system tray icon and menu."""
        menu = (
            item('Show Calculator', self.show_window),
            item('Hide to Tray', self.withdraw_window),
            item('Exit', self.quit_app)
        )
        self.icon = pystray.Icon("CalculatorService", self._create_tray_icon(), "Jarvis Calculator", menu)
        
        # Run tray icon in a separate thread
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()

    def withdraw_window(self):
        """Hide the main window to the background."""
        self.root.withdraw()
        self.is_hidden = True

    def show_window(self):
        """Restore the main window from the background."""
        self.root.after(0, self.root.deiconify)
        self.is_hidden = False

    def quit_app(self):
        """Cleanly exit the application and stop the tray service."""
        self.icon.stop()
        self.root.after(0, self.root.destroy)
        sys.exit(0)

if __name__ == "__main__":
    # Ensure the script can run even if no display is attached (service mode)
    try:
        root = tk.Tk()
        app = CalculatorApp(root)
        root.mainloop()
    except Exception as e:
        # Log error if GUI fails to initialize
        with open("app.log", "a") as f:
            f.write(f"Critical Error: {str(e)}\n")