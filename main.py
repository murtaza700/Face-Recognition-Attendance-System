"""
Smart Face Recognition Attendance System
Main Entry Point

A professional desktop application for automated face recognition 
and attendance management system.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure appearance
import customtkinter as ctk
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Import main window
from gui.main_window import MainWindow
from utils.config import initialize_directories

def main():
    """Main application entry point"""
    try:
        # Initialize directories
        initialize_directories()
        
        # Create and run main window
        app = MainWindow()
        app.run()
        
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()