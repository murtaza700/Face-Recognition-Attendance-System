"""
User registration window
"""

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
from tkinter import messagebox
import time
import os

from utils.config import (
    DATASET_DIR,
    REGISTRATION_IMAGES_COUNT,
    FACE_SIZE,
    COLOR_GREEN,
    COLOR_RED
)
from utils.camera import Camera
from utils.helpers import validate_name, play_sound, ensure_directory_exists
from core.face_detector import FaceDetector
from gui.components import ProgressIndicator

class RegistrationWindow:
    """Registration window for new users"""
    
    def __init__(self, parent, on_registration_complete=None):
        self.parent = parent
        self.on_registration_complete = on_registration_complete
        self.face_detector = FaceDetector()
        self.camera = None
        self.is_capturing = False
        self.capture_count = 0
        self.capture_name = ""
        
        # Create window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Register New User")
        self.window.geometry("800x600")
        self.window.grab_set()
        
        # Setup UI
        self.setup_ui()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_ui(self):
        """Setup registration window UI"""
        from utils.config import GUI_BG_DARK, GUI_BG_MEDIUM, GUI_ACCENT_BLUE
        
        # Main container
        self.container = ctk.CTkFrame(self.window, fg_color=GUI_BG_DARK)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            self.container,
            text="📸 NEW USER REGISTRATION",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=GUI_ACCENT_BLUE
        ).pack(pady=20)
        
        # Name input section
        self.create_name_section()
        
        # Progress section
        self.create_progress_section()
        
        # Camera preview
        self.preview_label = ctk.CTkLabel(self.container, text="")
        self.preview_label.pack(pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.container,
            text="Enter name and click Start Capture",
            font=ctk.CTkFont(size=14),
            text_color="#ffffff"
        )
        self.status_label.pack(pady=5)
        
        # Control buttons
        self.create_buttons()
    
    def create_name_section(self):
        """Create name input section"""
        from utils.config import GUI_BG_MEDIUM, GUI_BG_LIGHT, GUI_ACCENT_BLUE
        
        input_frame = ctk.CTkFrame(self.container, fg_color=GUI_BG_MEDIUM)
        input_frame.pack(fill="x", padx=30, pady=20)
        
        ctk.CTkLabel(
            input_frame,
            text="Enter Full Name:",
            font=ctk.CTkFont(size=16),
            text_color="#ffffff"
        ).pack(pady=(20,10))
        
        self.name_entry = ctk.CTkEntry(
            input_frame,
            font=ctk.CTkFont(size=16),
            height=45,
            placeholder_text="e.g., Ali Ahmed",
            fg_color=GUI_BG_LIGHT,
            border_color=GUI_ACCENT_BLUE
        )
        self.name_entry.pack(padx=30, pady=(0,20), fill="x")
    
    def create_progress_section(self):
        """Create progress tracking section"""
        self.progress_indicator = ProgressIndicator(self.container)
        self.progress_indicator.pack(fill="x", padx=30, pady=10)
    
    def create_buttons(self):
        """Create control buttons"""
        btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        # Start button
        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="🎥 Start Capture",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color="#0f3460",
            hover_color="#16213e",
            border_width=2,
            border_color="#00d2ff",
            command=self.start_capture
        )
        self.start_btn.pack(side="left", padx=10)
        
        # Stop button
        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ Stop",
            font=ctk.CTkFont(size=16),
            height=50,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.stop_capture,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=10)
        
        # Close button
        self.close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            font=ctk.CTkFont(size=16),
            height=50,
            fg_color="#ff6b6b",
            hover_color="#ee5a5a",
            command=self.on_close
        )
        self.close_btn.pack(side="left", padx=10)
    
    def start_capture(self):
        """Start image capture process"""
        # Validate name
        name = self.name_entry.get().strip()
        is_valid, result = validate_name(name)
        
        if not is_valid:
            messagebox.showerror("Invalid Name", result)
            return
        
        name = result
        
        # Create user directory
        user_folder = os.path.join(DATASET_DIR, name)
        ensure_directory_exists(user_folder)
        
        # Initialize camera
        self.camera = Camera()
        success, message = self.camera.start()
        
        if not success:
            messagebox.showerror("Camera Error", message)
            return
        
        # Update UI state
        self.is_capturing = True
        self.capture_count = 0
        self.capture_name = name
        
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.name_entry.configure(state="disabled")
        
        self.status_label.configure(
            text=f"Capturing images for: {name}",
            text_color="#00ff88"
        )
        
        # Start capture process
        self.process_frame()
    
    def process_frame(self):
        """Process each frame for face capture"""
        if not self.is_capturing:
            return
        
        # Get frame from camera
        success, frame = self.camera.get_frame()
        
        if not success:
            self.status_label.configure(text="Camera error!", text_color="#ff6b6b")
            self.window.after(10, self.process_frame)
            return
        
        # Default values
        faces = []
        box_color = COLOR_RED
        
        try:
            # Detect faces
            processed_frame, faces = self.face_detector.detect_faces(
                frame, 
                draw_box=False
            )
            
            # Set box color based on face detection
            box_color = COLOR_GREEN if len(faces) > 0 else COLOR_RED
            
            # Draw rectangles manually
            for (x, y, w, h) in faces:
                cv2.rectangle(processed_frame, (x, y), (x+w, y+h), box_color, 2)
            
            # Save face if detected and still capturing
            if len(faces) > 0 and self.capture_count < REGISTRATION_IMAGES_COUNT:
                # Extract and save face
                face_roi = self.face_detector.extract_face_roi(frame, faces[0])
                
                save_path = os.path.join(DATASET_DIR, self.capture_name, f"{self.capture_count}.jpg")
                cv2.imwrite(save_path, face_roi)
                
                self.capture_count += 1
                
                # Update progress
                self.progress_indicator.update(
                    self.capture_count,
                    REGISTRATION_IMAGES_COUNT,
                    "Capturing"
                )
                
                # Small delay for different angles
                time.sleep(0.05)
            
            # Add "No Face" text if no face detected
            if len(faces) == 0:
                cv2.putText(
                    processed_frame, 
                    "No Face Detected!", 
                    (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    COLOR_RED, 
                    2
                )
            
            # Display frame
            frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.resize(frame_rgb, (400, 300))
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=img_tk)
            self.preview_label.image = img_tk
            
        except Exception as e:
            print(f"Frame processing error: {e}")
        
        # Check if capture is complete
        if self.capture_count >= REGISTRATION_IMAGES_COUNT:
            self.capture_complete()
            return
        
        # Continue processing
        self.window.after(10, self.process_frame)
    
    def capture_complete(self):
        """Handle capture completion"""
        self.stop_camera()
        
        # Update UI
        self.status_label.configure(
            text=f"✓ DONE! Registration Complete! {self.capture_count} images captured for {self.capture_name}",
            text_color="#00ff88"
        )
        
        # Clear preview
        self.preview_label.configure(image="")
        self.preview_label.image = None
        
        # Play success sound
        play_sound('success')
        
        # Show success message
        messagebox.showinfo(
            "Registration Complete",
            f"Successfully registered {self.capture_name}!\n\n"
            f"Total images captured: {self.capture_count}\n\n"
            f"Please train the model to enable recognition."
        )
        
        # Call callback if provided
        if self.on_registration_complete:
            self.on_registration_complete(self.capture_name)
        
        # Reset buttons
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.name_entry.configure(state="normal")
        self.is_capturing = False
        
        # Auto close window after short delay
        self.window.after(500, self.on_close)
    
    def stop_capture(self):
        """Stop the capture process"""
        self.is_capturing = False
        self.stop_camera()
        
        self.status_label.configure(
            text="Capture stopped by user",
            text_color="#ffa500"
        )
        
        # Clear preview
        self.preview_label.configure(image="")
        self.preview_label.image = None
        
        # Reset UI
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.name_entry.configure(state="normal")
        
        self.capture_count = 0
    
    def stop_camera(self):
        """Stop and release camera"""
        if self.camera:
            self.camera.stop()
            self.camera = None
    
    def on_close(self):
        """Handle window close"""
        self.is_capturing = False
        self.stop_camera()
        self.window.destroy()