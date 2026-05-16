"""
Main dashboard window
"""

import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
import threading
import os

from utils.config import (
    GUI_BG_DARK,
    GUI_BG_MEDIUM,
    GUI_BG_LIGHT,
    GUI_ACCENT_BLUE,
    GUI_ACCENT_GREEN,
    GUI_ACCENT_ORANGE,
    GUI_ACCENT_RED,
    GUI_BUTTON_BG,
    MODEL_FILE,
    LABELS_FILE
)
from utils.database import AttendanceDatabase
from utils.helpers import format_date_display, play_sound
from core.trainer import ModelTrainer
from gui.registration_window import RegistrationWindow
from gui.attendance_window import AttendanceWindow
from gui.components import StatusBadge, InfoCard

class MainWindow:
    """Main application window"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Smart Face Recognition System")
        self.root.geometry("1200x700")
        
        # Initialize components
        self.trainer = ModelTrainer()
        self.database = AttendanceDatabase()
        
        # Load model if exists
        self.model_loaded = False
        self.check_and_load_model()
        
        # Setup UI
        self.setup_ui()
        
        # Bind keyboard shortcuts
        self.bind_shortcuts()
    
    def check_and_load_model(self):
        """Check if model exists and load it"""
        try:
            if os.path.exists(MODEL_FILE) and os.path.exists(LABELS_FILE):
                success, message = self.trainer.face_recognizer.load_model()
                self.model_loaded = success
                
                if success:
                    print(f"Model loaded: {message}")
                else:
                    print(f"Model load failed: {message}")
            else:
                self.model_loaded = False
                print("Model files not found")
        except Exception as e:
            self.model_loaded = False
            print(f"Error checking model: {e}")
    
    def setup_ui(self):
        """Setup main window UI"""
        # Main container
        self.main_frame = ctk.CTkFrame(self.root, fg_color=GUI_BG_DARK)
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header
        self.create_header()
        
        # Status bar
        self.status_badge = StatusBadge(self.main_frame)
        self.status_badge.pack(pady=10)
        
        # Content area
        content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=50, pady=20)
        
        # Left panel - Controls
        self.create_left_panel(content_frame)
        
        # Right panel - Information (Scrollable)
        self.create_right_panel(content_frame)
    
    def create_header(self):
        """Create header section"""
        header_frame = ctk.CTkFrame(self.main_frame, fg_color=GUI_BG_MEDIUM, height=100)
        header_frame.pack(fill="x", padx=10, pady=(10,20))
        
        ctk.CTkLabel(
            header_frame,
            text="🎓 Smart Face Recognition System",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=GUI_ACCENT_BLUE
        ).pack(pady=20)
    
    def create_left_panel(self, parent):
        """Create left panel with control buttons"""
        left_panel = ctk.CTkFrame(parent, fg_color=GUI_BG_MEDIUM)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0,10))
        
        ctk.CTkLabel(
            left_panel,
            text="MAIN CONTROLS",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=GUI_ACCENT_BLUE
        ).pack(pady=(30,20))
        
        # Register button
        ctk.CTkButton(
            left_panel,
            text="📸 Register User",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color=GUI_BUTTON_BG,
            hover_color=GUI_BG_MEDIUM,
            corner_radius=15,
            border_width=2,
            border_color=GUI_ACCENT_BLUE,
            command=self.open_registration
        ).pack(pady=15, padx=30, fill="x")
        
        # Attendance button
        ctk.CTkButton(
            left_panel,
            text="✓ Mark Attendance",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color=GUI_BUTTON_BG,
            hover_color=GUI_BG_MEDIUM,
            corner_radius=15,
            border_width=2,
            border_color=GUI_ACCENT_GREEN,
            command=self.open_attendance
        ).pack(pady=15, padx=30, fill="x")
        
        # Train button
        self.train_btn = ctk.CTkButton(
            left_panel,
            text="🔄 Train Model",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color=GUI_BUTTON_BG,
            hover_color=GUI_BG_MEDIUM,
            corner_radius=15,
            border_width=2,
            border_color=GUI_ACCENT_ORANGE,
            command=self.train_model
        )
        self.train_btn.pack(pady=15, padx=30, fill="x")
        
        # View attendance button
        ctk.CTkButton(
            left_panel,
            text="📊 View Attendance",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color=GUI_BUTTON_BG,
            hover_color=GUI_BG_MEDIUM,
            corner_radius=15,
            border_width=2,
            border_color=GUI_ACCENT_RED,
            command=self.view_attendance
        ).pack(pady=15, padx=30, fill="x")
    
    def create_right_panel(self, parent):
        """Create right panel with scrollable information"""
        # Right panel container
        right_panel = ctk.CTkFrame(parent, fg_color=GUI_BG_MEDIUM)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10,0))
        
        # Title
        ctk.CTkLabel(
            right_panel,
            text="SYSTEM INFORMATION",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=GUI_ACCENT_BLUE
        ).pack(pady=(30,20))
        
        # Scrollable frame for all info cards
        scroll_frame = ctk.CTkScrollableFrame(
            right_panel,
            fg_color="transparent",
            scrollbar_fg_color=GUI_BG_LIGHT,
            scrollbar_button_color=GUI_ACCENT_BLUE,
            scrollbar_button_hover_color=GUI_ACCENT_GREEN
        )
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        
        # Clock
        self.clock_label = ctk.CTkLabel(
            scroll_frame,
            text="",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        )
        self.clock_label.pack(pady=10)
        self.update_clock()
        
        # Date card
        date_card = InfoCard(scroll_frame)
        date_card.pack(fill="x", padx=10, pady=10)
        self.date_label = date_card.add_label(
            f"📅 {format_date_display()}",
            color=GUI_ACCENT_BLUE,
            font_size=16
        )
        
        # Stats card
        stats_card = InfoCard(scroll_frame, "SYSTEM STATS")
        stats_card.pack(fill="x", padx=10, pady=10)
        
        self.users_label = stats_card.add_label("Registered Users: 0")
        self.att_count_label = stats_card.add_label("Today's Attendance: 0")
        
        # Model status card
        model_card = InfoCard(scroll_frame, "MODEL STATUS")
        model_card.pack(fill="x", padx=10, pady=10)
        
        model_status = "✓ Trained & Ready" if self.model_loaded else "✗ Not Trained"
        model_color = GUI_ACCENT_GREEN if self.model_loaded else GUI_ACCENT_RED
        
        self.model_status_label = model_card.add_label(model_status, color=model_color)
        
        # Get model info
        if self.model_loaded:
            user_count = self.trainer.face_recognizer.get_user_count()
            model_info = f"Model loaded with {user_count} users"
        else:
            model_info = "Train model to start"
        
        self.model_info_label = model_card.add_label(
            model_info,
            color="#a0a0a0",
            font_size=12
        )
        
        # Quick tips card
        tips_card = InfoCard(scroll_frame, "⚡ QUICK TIPS")
        tips_card.pack(fill="x", padx=10, pady=10)
        
        tips_text = "• Ctrl+R: Register User\n• Ctrl+A: Mark Attendance\n• Ctrl+T: Train Model"
        tips_card.add_label(tips_text, color="#a0a0a0", font_size=12)
        
        # App info card
        app_card = InfoCard(scroll_frame, "ℹ️ ABOUT")
        app_card.pack(fill="x", padx=10, pady=10)
        
        about_text = "Face Recognition Attendance System\nVersion: 1.0.0\nPython + OpenCV + CustomTkinter"
        app_card.add_label(about_text, color="#a0a0a0", font_size=12)
        
        # Update stats
        self.update_stats()
    
    def update_clock(self):
        """Update real-time clock"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.configure(text=f"🕐 {current_time}")
        self.root.after(1000, self.update_clock)
    
    def update_stats(self):
        """Update system statistics"""
        # Registered users
        users = self.trainer.get_registered_users()
        self.users_label.configure(text=f"Registered Users: {len(users)}")
        
        # Today's attendance
        today_count = self.database.get_today_count()
        self.att_count_label.configure(text=f"Today's Attendance: {today_count}")
        
        # Model status
        self.check_and_load_model()
        
        model_status = "✓ Trained & Ready" if self.model_loaded else "✗ Not Trained"
        model_color = GUI_ACCENT_GREEN if self.model_loaded else GUI_ACCENT_RED
        
        self.model_status_label.configure(text=model_status, text_color=model_color)
        
        if self.model_loaded:
            user_count = self.trainer.face_recognizer.get_user_count()
            model_info = f"Model loaded with {user_count} users"
        else:
            model_info = "Train model to start"
        
        self.model_info_label.configure(text=model_info)
    
    def open_registration(self):
        """Open registration window"""
        def on_complete(name):
            self.status_badge.set_status(f"User {name} registered successfully", GUI_ACCENT_GREEN)
            self.update_stats()
            
            # Ask to train model
            if messagebox.askyesno(
                "Train Model",
                f"Registration complete for {name}!\n\nDo you want to train the model now?"
            ):
                self.train_model()
        
        RegistrationWindow(self.root, on_registration_complete=on_complete)
    
    def open_attendance(self):
        """Open attendance window"""
        self.check_and_load_model()
        self.update_stats()
        
        if not self.model_loaded:
            messagebox.showerror(
                "Model Not Trained",
                "Please train the model first before marking attendance.\n\n"
                "Click 'Train Model' button or press Ctrl+T\n\n"
                "Make sure you have registered at least one user."
            )
            return
        
        # Create attendance window
        AttendanceWindow(self.root)
    
    def train_model(self):
        """Train the recognition model"""
        self.status_badge.set_status("Training model...", GUI_ACCENT_ORANGE)
        self.train_btn.configure(state="disabled", text="Training...")
        
        def train():
            success, message = self.trainer.train_model()
            
            # After training, reload model
            self.check_and_load_model()
            
            if success:
                self.root.after(0, lambda: self.status_badge.set_status(
                    "Model trained successfully!", GUI_ACCENT_GREEN
                ))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Training Complete", 
                    f"{message}\n\nModel is now ready for attendance marking!"
                ))
                play_sound('success')
            else:
                self.root.after(0, lambda: self.status_badge.set_status(
                    "Training failed!", GUI_ACCENT_RED
                ))
                self.root.after(0, lambda: messagebox.showerror("Training Failed", message))
                play_sound('error')
            
            self.root.after(0, self.update_stats)
            self.root.after(0, lambda: self.train_btn.configure(
                state="normal", text="🔄 Train Model"
            ))
        
        thread = threading.Thread(target=train)
        thread.daemon = True
        thread.start()
    
    def view_attendance(self):
        """View attendance records"""
        view_window = ctk.CTkToplevel(self.root)
        view_window.title("Attendance Records")
        view_window.geometry("1000x600")
        view_window.grab_set()
        
        container = ctk.CTkFrame(view_window, fg_color=GUI_BG_DARK)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            container,
            text="📊 ATTENDANCE RECORDS",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=GUI_ACCENT_BLUE
        ).pack(pady=20)
        
        # Attendance data
        records = self.database.get_all_attendance()
        
        if not records:
            ctk.CTkLabel(
                container,
                text="No attendance records found",
                font=ctk.CTkFont(size=16),
                text_color=GUI_ACCENT_RED
            ).pack(pady=50)
        else:
            # Create scrollable frame
            scroll_frame = ctk.CTkScrollableFrame(
                container,
                fg_color=GUI_BG_LIGHT
            )
            scroll_frame.pack(fill="both", expand=True, padx=30, pady=20)
            
            # Headers
            header_frame = ctk.CTkFrame(scroll_frame, fg_color="#0f3460")
            header_frame.pack(fill="x")
            
            for col, width in [("Name", 200), ("Date", 150), ("Time", 150), ("Confidence", 150)]:
                ctk.CTkLabel(
                    header_frame,
                    text=col,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    width=width,
                    text_color="#ffffff"
                ).pack(side="left", padx=5, pady=10)
            
            # Records
            for record in records:
                row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)
                
                for value, width in [
                    (record.get('Name', ''), 200),
                    (record.get('Date', ''), 150),
                    (record.get('Time', ''), 150),
                    (record.get('Confidence', 'N/A'), 150)
                ]:
                    ctk.CTkLabel(
                        row_frame,
                        text=str(value),
                        font=ctk.CTkFont(size=13),
                        width=width,
                        text_color="#a0a0a0"
                    ).pack(side="left", padx=5, pady=5)
        
        # Close button
        ctk.CTkButton(
            container,
            text="Close",
            font=ctk.CTkFont(size=16),
            fg_color=GUI_ACCENT_RED,
            hover_color="#ee5a5a",
            command=view_window.destroy
        ).pack(pady=20)
    
    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Control-r>', lambda e: self.open_registration())
        self.root.bind('<Control-a>', lambda e: self.open_attendance())
        self.root.bind('<Control-t>', lambda e: self.train_model())
    
    def run(self):
        """Run the application"""
        self.root.mainloop()