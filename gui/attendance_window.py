"""
Attendance marking window
"""

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
from tkinter import messagebox
import os

from utils.config import (
    COLOR_GREEN,
    COLOR_RED,
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
from gui.components import AttendanceList

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
        
        # LOAD MODEL - IMPORTANT: Pehle model load karo
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
        from utils.config import GUI_BG_DARK, GUI_BG_MEDIUM, GUI_ACCENT_GREEN
        
        # Main container
        self.container = ctk.CTkFrame(self.window, fg_color=GUI_BG_DARK)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(
            self.container,
            text="📋 ATTENDANCE MARKING",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=GUI_ACCENT_GREEN
        ).pack(pady=20)
        
        # Camera preview
        self.preview_label = ctk.CTkLabel(self.container, text="")
        self.preview_label.pack(pady=10)
        
        # Recognition info
        self.create_info_section()
        
        # Attendance list
        self.attendance_list = AttendanceList(self.container)
        self.attendance_list.pack(fill="both", expand=True, padx=30, pady=20)
        
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
        
        # Get frame
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
                    box_color = COLOR_GREEN
                    confidence_value = confidence
                    
                    # Mark attendance if not already marked today
                    if name not in self.attendance_marked_today:
                        self.mark_attendance(name, confidence)
                else:
                    recognized_name = "Unknown"
                    box_color = COLOR_RED
                
                # Draw rectangle and name
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), box_color, 2)
                
                # Add name label
                label_text = recognized_name
                if recognized_name != "Unknown":
                    label_text += f" ({format_confidence(confidence_value)})"
                
                cv2.putText(
                    display_frame, label_text,
                    (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    box_color,
                    2
                )
                
                # Update recognition status
                self.recognition_label.configure(
                    text=f"Detected: {recognized_name}",
                    text_color="#00ff88" if recognized_name != "Unknown" else "#ff6b6b"
                )
            else:
                self.recognition_label.configure(
                    text="No face detected",
                    text_color="#ffffff"
                )
            
            # Display frame
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.resize(frame_rgb, (600, 400))
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=img_tk)
            self.preview_label.image = img_tk
            
        except Exception as e:
            print(f"AttendanceWindow: Frame processing error - {e}")
        
        # Continue processing
        if self.is_running:
            self.window.after(10, self.process_frame)
    
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
            
            # Play success sound
            play_sound('success')
            
            # Flash effect
            self.flash_recognition_label(name)
            
            # Update attendance list
            self.update_attendance_display()
            
            # Reset status after 2 seconds
            self.window.after(2000, lambda: self.status_label.configure(
                text="Camera active - Waiting for faces...",
                text_color="#ffffff"
            ))
        else:
            print(f"AttendanceWindow: Failed to mark - {message}")
    
    def flash_recognition_label(self, name):
        """Flash effect when attendance is marked"""
        # Flash green
        self.recognition_label.configure(
            text=f"✓ {name} - Present!",
            text_color="#00ff88"
        )
        
        # Reset after 1.5 seconds
        self.window.after(1500, lambda: self.recognition_label.configure(
            text=f"Detected: {name}",
            text_color="#00ff88"
        ))
    
    def update_attendance_display(self):
        """Update the attendance list display"""
        today_records = self.database.get_today_attendance()
        self.attendance_list.update_list(today_records)
    
    def on_close(self):
        """Handle window close"""
        self.is_running = False
        
        if self.camera:
            self.camera.stop()
            self.camera = None
        
        if self.window:
            self.window.destroy()
        
        print("AttendanceWindow: Closed")