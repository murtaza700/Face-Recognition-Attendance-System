"""
Attendance marking window with confirmation dialog
"""

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
from tkinter import messagebox
import os
import time

from utils.config import (
    COLOR_GREEN,
    COLOR_RED,
    COLOR_YELLOW,
    FACE_SIZE,
    CONFIDENCE_THRESHOLD,
    MODEL_FILE,
    LABELS_FILE
)
from utils.camera import Camera
from utils.database import AttendanceDatabase
from utils.helpers import play_sound, format_confidence
from core.face_detector import FaceDetector
from core.face_recognizer import FaceRecognizer

class AttendanceWindow:
    """Attendance marking window"""
    
    def __init__(self, parent):
        self.parent = parent
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.database = AttendanceDatabase()
        self.camera = None
        self.is_running = False
        self.attendance_marked_today = set()
        
        # Confirmation state
        self.is_confirming = False
        self.pending_confirmation = False
        self.last_detected_name = None
        self.last_confidence = None
        
        # LOAD MODEL
        print("AttendanceWindow: Loading model...")
        success, msg = self.face_recognizer.load_model()
        print(f"AttendanceWindow: Load result - {msg}")
        
        if not success:
            messagebox.showerror(
                "Model Not Trained",
                "Please train the model first before marking attendance.\n\n"
                "Click 'Train Model' button on main window."
            )
            self.window = None
            return
        
        # Load today's already marked attendance
        self.load_today_attendance()
        
        # Create window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Mark Attendance")
        self.window.geometry("900x700")
        self.window.grab_set()
        
        # Setup UI
        self.setup_ui()
        
        # Start camera
        self.start_camera()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def load_today_attendance(self):
        """Load today's already marked attendance"""
        today_records = self.database.get_today_attendance()
        for record in today_records:
            self.attendance_marked_today.add(record['Name'])
        print(f"AttendanceWindow: Already marked today - {self.attendance_marked_today}")
    
    def setup_ui(self):
        """Setup attendance window UI"""
        from utils.config import GUI_BG_DARK, GUI_BG_MEDIUM, GUI_ACCENT_GREEN, GUI_ACCENT_BLUE
        
        # Main container
        self.container = ctk.CTkFrame(self.window, fg_color=GUI_BG_DARK)
        self.container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header
        ctk.CTkLabel(
            self.container,
            text="📋 ATTENDANCE MARKING",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=GUI_ACCENT_GREEN
        ).pack(pady=20)
        
        # Camera preview - fixed size
        self.preview_label = ctk.CTkLabel(self.container, text="", height=400)
        self.preview_label.pack(pady=10)
        
        # Recognition info
        self.create_info_section()
        
        # Confirmation status
        self.confirmation_label = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffa500"
        )
        self.confirmation_label.pack(pady=5)
        
        # Attendance list with scrollbar
        self.create_attendance_list()
        
        # Update initial list
        self.update_attendance_display()
        
        # Stop button
        ctk.CTkButton(
            self.container,
            text="⏹ Stop Attendance",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.on_close
        ).pack(pady=20)
    
    def create_info_section(self):
        """Create recognition info section"""
        from utils.config import GUI_BG_MEDIUM
        
        info_frame = ctk.CTkFrame(self.container, fg_color=GUI_BG_MEDIUM)
        info_frame.pack(fill="x", padx=30, pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            info_frame,
            text="Camera active - Waiting for faces...",
            font=ctk.CTkFont(size=16),
            text_color="#ffffff"
        )
        self.status_label.pack(side="left", padx=20, pady=10)
        
        # Recognition result
        self.recognition_label = ctk.CTkLabel(
            info_frame,
            text="Waiting for face...",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        )
        self.recognition_label.pack(side="right", padx=20, pady=10)
    
    def create_attendance_list(self):
        """Create scrollable attendance list"""
        from utils.config import GUI_BG_MEDIUM, GUI_BG_LIGHT, GUI_ACCENT_BLUE
        
        # Frame for attendance list - NOW EXPANDABLE
        att_frame = ctk.CTkFrame(self.container, fg_color=GUI_BG_MEDIUM)
        att_frame.pack(fill="both", expand=True, padx=30, pady=(10, 0))
        
        # Title
        ctk.CTkLabel(
            att_frame,
            text="Today's Attendance List",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=GUI_ACCENT_BLUE
        ).pack(pady=(10,5))
        
        # Scrollable frame for attendance entries - REMOVED fixed height
        self.att_scroll_frame = ctk.CTkScrollableFrame(
            att_frame,
            fg_color=GUI_BG_LIGHT,
            scrollbar_fg_color=GUI_BG_MEDIUM,
            scrollbar_button_color=GUI_ACCENT_BLUE,
            scrollbar_button_hover_color="#00ff88",
            # Height will be auto-managed by fill="both", expand=True
        )
        self.att_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def start_camera(self):
        """Start camera for attendance"""
        self.camera = Camera()
        success, message = self.camera.start()
        
        if not success:
            messagebox.showerror("Camera Error", message)
            self.on_close()
            return
        
        self.is_running = True
        print("AttendanceWindow: Camera started, beginning face recognition...")
        self.process_frame()
    
    def process_frame(self):
        """Process each frame for face recognition"""
        if not self.is_running:
            return
        
        # Get frame (always get frame even when confirming to keep camera active)
        success, frame = self.camera.get_frame()
        
        if not success:
            self.window.after(10, self.process_frame)
            return
        
        # Default values
        recognized_name = "Unknown"
        box_color = COLOR_RED
        confidence_value = 100
        
        try:
            # Make a copy for display
            display_frame = frame.copy()
            
            # Only do face detection/recognition if not confirming
            if not self.is_confirming:
                # Detect faces
                _, faces = self.face_detector.detect_faces(frame, draw_box=False)
                
                if len(faces) > 0:
                    # Take the largest face
                    largest_face = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = largest_face
                    
                    # Extract face ROI
                    if len(frame.shape) == 3:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    else:
                        gray = frame
                    
                    face_roi = gray[y:y+h, x:x+w]
                    face_roi = cv2.resize(face_roi, FACE_SIZE)
                    
                    # Recognize face
                    name, confidence, label_id = self.face_recognizer.predict(face_roi)
                    
                    print(f"AttendanceWindow: Detected - {name}, Confidence: {confidence:.1f}")
                    
                    if name != "Unknown" and confidence < CONFIDENCE_THRESHOLD:
                        recognized_name = name
                        confidence_value = confidence
                        
                        # Check if already marked today
                        if name in self.attendance_marked_today:
                            box_color = COLOR_YELLOW
                            self.recognition_label.configure(
                                text=f"{name} - Already Marked Today!",
                                text_color="#ffa500"
                            )
                            self.confirmation_label.configure(
                                text=f"⚠️ {name}, aapki aaj ki attendance pehle hi lag chuki hai!\nNext attendance kal lag sakti hai.",
                                text_color="#ffa500"
                            )
                            # Clear warning after 3 seconds
                            self.window.after(3000, lambda: self.confirmation_label.configure(text=""))
                        else:
                            box_color = COLOR_GREEN
                            # SHOW CONFIRMATION DIALOG
                            self.show_confirmation_dialog(name, confidence)
                            self.is_confirming = True
                            # Don't return - continue to update display
                    else:
                        recognized_name = "Unknown"
                        box_color = COLOR_RED
                    
                    # Draw rectangle and name
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), box_color, 2)
                    
                    # Add name label
                    label_text = recognized_name
                    if recognized_name != "Unknown":
                        label_text += f" ({format_confidence(confidence_value)})"
                    
                    # Background for text
                    (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                    cv2.rectangle(display_frame, (x, y-text_h-10), (x+text_w, y), box_color, -1)
                    cv2.putText(
                        display_frame, label_text,
                        (x, y-5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 0),
                        2
                    )
                    
                    # Update recognition status
                    if recognized_name != "Unknown":
                        if recognized_name in self.attendance_marked_today:
                            self.recognition_label.configure(
                                text=f"{recognized_name} - Already Marked",
                                text_color="#ffa500"
                            )
                        else:
                            self.recognition_label.configure(
                                text=f"Detected: {recognized_name}",
                                text_color="#00ff88"
                            )
                else:
                    self.recognition_label.configure(
                        text="No face detected",
                        text_color="#ffffff"
                    )
            else:
                # While confirming, show waiting message on frame
                cv2.putText(
                    display_frame,
                    "Waiting for confirmation...",
                    (50, 200),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (255, 165, 0),
                    2
                )
            
            # Always display the frame (whether confirming or not)
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.resize(frame_rgb, (600, 400))
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=img_tk)
            self.preview_label.image = img_tk
            
        except Exception as e:
            print(f"AttendanceWindow: Frame processing error - {e}")
        
        # Always continue processing (key fix - moved outside if/else)
        if self.is_running:
            self.window.after(10, self.process_frame)
    
    def show_confirmation_dialog(self, name, confidence):
        """
        Show confirmation dialog to verify if this is the correct person
        
        Args:
            name: Recognized name
            confidence: Recognition confidence
        """
        # Create custom confirmation dialog
        confirm_window = ctk.CTkToplevel(self.window)
        confirm_window.title("Confirm Identity")
        confirm_window.geometry("500x300")
        confirm_window.grab_set()
        confirm_window.focus_force()
        
        # Center the window
        confirm_window.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - 250
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - 150
        confirm_window.geometry(f"+{x}+{y}")
        
        # Container
        container = ctk.CTkFrame(confirm_window, fg_color="#1a1a2e")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Question
        ctk.CTkLabel(
            container,
            text="🤔 IDENTITY CONFIRMATION",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#00d2ff"
        ).pack(pady=(20,10))
        
        ctk.CTkLabel(
            container,
            text=f"Kya aap {name} hain?",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=10)
        
        ctk.CTkLabel(
            container,
            text=f"Confidence: {format_confidence(confidence)}",
            font=ctk.CTkFont(size=14),
            text_color="#a0a0a0"
        ).pack(pady=5)
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        def on_yes():
            """User confirmed YES"""
            self.is_confirming = False  # Set to False BEFORE destroying dialog
            confirm_window.destroy()
            
            self.confirmation_label.configure(
                text=f"✓ Welcome {name}! Attendance marked successfully.",
                text_color="#00ff88"
            )
            
            # Mark attendance
            self.mark_attendance(name, confidence)
            
            # Play success sound
            play_sound('success')
            
            # Clear confirmation after 3 seconds and resume
            self.window.after(3000, self.clear_confirmation_and_resume)
        
        def on_no():
            """User said NO"""
            self.is_confirming = False  # Set to False BEFORE destroying dialog
            confirm_window.destroy()
            
            self.confirmation_label.configure(
                text=f"✗ Not {name}. Please scan again...",
                text_color="#ff6b6b"
            )
            
            # Play error sound
            play_sound('error')
            
            # Clear confirmation after 2 seconds and resume
            self.window.after(2000, self.clear_confirmation_and_resume)
        
        # Yes button
        ctk.CTkButton(
            btn_frame,
            text="✅ YES, That's Me!",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            corner_radius=10,
            command=on_yes
        ).pack(side="left", padx=10)
        
        # No button
        ctk.CTkButton(
            btn_frame,
            text="❌ NO, Scan Again",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            corner_radius=10,
            command=on_no
        ).pack(side="left", padx=10)
        
        # Handle window close (X button)
        def on_close_dialog():
            self.is_confirming = False  # Set to False BEFORE destroying dialog
            confirm_window.destroy()
            self.confirmation_label.configure(
                text="Confirmation cancelled. Please scan again...",
                text_color="#ffa500"
            )
            self.window.after(2000, self.clear_confirmation_and_resume)
        
        confirm_window.protocol("WM_DELETE_WINDOW", on_close_dialog)
        
        # Auto-close after 15 seconds if no response
        self.window.after(15000, lambda: self.auto_close_confirmation(confirm_window, name))
    
    def auto_close_confirmation(self, confirm_window, name):
        """Auto close confirmation if no response"""
        if confirm_window.winfo_exists():
            self.is_confirming = False  # Set to False BEFORE destroying dialog
            confirm_window.destroy()
            self.confirmation_label.configure(
                text=f"⏰ Timeout! Please scan again...",
                text_color="#ffa500"
            )
            self.window.after(2000, self.clear_confirmation_and_resume)
    
    def clear_confirmation_and_resume(self):
        """Clear confirmation message and resume scanning"""
        self.confirmation_label.configure(text="")
        self.recognition_label.configure(
            text="Waiting for face...",
            text_color="#ffffff"
        )
        print("AttendanceWindow: Resuming face recognition...")
    
    def mark_attendance(self, name, confidence):
        """
        Mark attendance with duplicate prevention
        
        Args:
            name: Recognized user name
            confidence: Recognition confidence
        """
        # Triple-check duplicate prevention
        if name in self.attendance_marked_today:
            print(f"AttendanceWindow: DUPLICATE PREVENTED - {name} already in memory set")
            return
        
        if self.database.is_already_marked(name):
            print(f"AttendanceWindow: DUPLICATE PREVENTED - {name} already in database")
            self.attendance_marked_today.add(name)
            return
        
        # Mark attendance
        success, message = self.database.mark_attendance(name, confidence)
        
        if success:
            self.attendance_marked_today.add(name)
            
            print(f"AttendanceWindow: ✓ Attendance marked - {name}")
            
            # Update status
            self.status_label.configure(
                text=f"✓ Attendance marked: {name}",
                text_color="#00ff88"
            )
            
            # Flash effect
            self.recognition_label.configure(
                text=f"✓ {name} - Present!",
                text_color="#00ff88"
            )
            
            # Update attendance list
            self.update_attendance_display()
            
            # Reset status after 3 seconds
            self.window.after(3000, lambda: self.status_label.configure(
                text="Camera active - Waiting for faces...",
                text_color="#ffffff"
            ))
        else:
            print(f"AttendanceWindow: Failed to mark - {message}")
    
    def update_attendance_display(self):
        """Update the attendance list display"""
        # Clear existing content
        for widget in self.att_scroll_frame.winfo_children():
            widget.destroy()
        
        today_records = self.database.get_today_attendance()
        
        if not today_records:
            no_records_label = ctk.CTkLabel(
                self.att_scroll_frame,
                text="No attendance marked today yet",
                font=ctk.CTkFont(size=14),
                text_color="#a0a0a0"
            )
            no_records_label.pack(pady=20)
            return
        
        # Sort by time
        sorted_records = sorted(today_records, key=lambda x: x['Time'])
        
        # Header
        header_text = f"✓ Today's Attendance ({len(sorted_records)} students):"
        header_label = ctk.CTkLabel(
            self.att_scroll_frame,
            text=header_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00ff88"
        )
        header_label.pack(pady=(10,5), anchor="w", padx=10)
        
        # Each attendance entry
        for record in sorted_records:
            entry_text = f"  • {record['Name']} - {record['Time']}"
            entry_label = ctk.CTkLabel(
                self.att_scroll_frame,
                text=entry_text,
                font=ctk.CTkFont(size=13),
                text_color="#ffffff"
            )
            entry_label.pack(pady=3, anchor="w", padx=20)
    
    def on_close(self):
        """Handle window close"""
        self.is_running = False
        self.is_confirming = False
        
        if self.camera:
            self.camera.stop()
            self.camera = None
        
        if self.window:
            self.window.destroy()
        
        print("AttendanceWindow: Closed")