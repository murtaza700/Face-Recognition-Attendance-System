import customtkinter as ctk
import cv2
import os
import numpy as np
import pandas as pd
import pickle
from datetime import datetime
from PIL import Image, ImageTk
import threading
from tkinter import messagebox
import time

# Import training module
from train import FaceTrainer

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FaceRecognitionSystem:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Smart Face Recognition System")
        self.root.geometry("1200x700")
        
        # Load Haar Cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Initialize recognizer and trainer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.trainer = FaceTrainer()
        
        # Load trained model if exists
        self.model_loaded = False
        self.labels = {}
        
        if os.path.exists("trainer.yml") and os.path.exists("labels.pkl"):
            try:
                self.recognizer.read("trainer.yml")
                with open("labels.pkl", 'rb') as f:
                    self.labels = pickle.load(f)
                self.model_loaded = True
                print("Model loaded successfully!")
            except Exception as e:
                print(f"Error loading model: {e}")
        
        # Initialize attendance file
        if not os.path.exists("attendance.csv"):
            df = pd.DataFrame(columns=['Name', 'Date', 'Time'])
            df.to_csv("attendance.csv", index=False)
        
        # Create dataset folder
        if not os.path.exists("dataset/images"):
            os.makedirs("dataset/images")
        
        # Setup UI
        self.setup_ui()
        
        # Variables for webcam control
        self.is_capturing = False
        self.attendance_marked = set()  # Track today's attendance
        
    def setup_ui(self):
        """Setup the main user interface"""
        # Main container
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#1a1a2e")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header Section
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="#16213e", height=100)
        header_frame.pack(fill="x", padx=10, pady=(10,20))
        
        # Title with icon
        ctk.CTkLabel(
            header_frame, 
            text="🎓 Smart Face Recognition System",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#00d2ff"
        ).pack(pady=20)
        
        # Status Label
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="● System Ready",
            font=ctk.CTkFont(size=14),
            text_color="#00ff88",
            fg_color="#0a1628",
            corner_radius=10,
            padx=20,
            pady=10
        )
        self.status_label.pack(pady=10)
        
        # Content Area
        content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=50, pady=20)
        
        # Left Panel - Main Buttons
        left_panel = ctk.CTkFrame(content_frame, fg_color="#16213e")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0,10))
        
        ctk.CTkLabel(
            left_panel,
            text="MAIN CONTROLS",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00d2ff"
        ).pack(pady=(30,20))
        
        # Register Button
        self.register_btn = ctk.CTkButton(
            left_panel,
            text="📸 Register User",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color="#0f3460",
            hover_color="#16213e",
            corner_radius=15,
            border_width=2,
            border_color="#00d2ff",
            command=self.open_registration_window
        )
        self.register_btn.pack(pady=15, padx=30, fill="x")
        
        # Attendance Button
        self.attendance_btn = ctk.CTkButton(
            left_panel,
            text="✓ Mark Attendance",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color="#0f3460",
            hover_color="#16213e",
            corner_radius=15,
            border_width=2,
            border_color="#00ff88",
            command=self.start_attendance
        )
        self.attendance_btn.pack(pady=15, padx=30, fill="x")
        
        # Train Model Button
        self.train_btn = ctk.CTkButton(
            left_panel,
            text="🔄 Train Model",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color="#0f3460",
            hover_color="#16213e",
            corner_radius=15,
            border_width=2,
            border_color="#ffa500",
            command=self.train_model
        )
        self.train_btn.pack(pady=15, padx=30, fill="x")
        
        # View Attendance Button
        self.view_btn = ctk.CTkButton(
            left_panel,
            text="📊 View Attendance",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color="#0f3460",
            hover_color="#16213e",
            corner_radius=15,
            border_width=2,
            border_color="#ff6b6b",
            command=self.view_attendance
        )
        self.view_btn.pack(pady=15, padx=30, fill="x")
        
        # Check Training Status Button
        self.check_btn = ctk.CTkButton(
            left_panel,
            text="🔍 Check Status",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color="#0f3460",
            hover_color="#16213e",
            corner_radius=15,
            border_width=2,
            border_color="#9b59b6",
            command=self.check_system_status
        )
        self.check_btn.pack(pady=15, padx=30, fill="x")
        
        # Right Panel - Info & Preview
        right_panel = ctk.CTkFrame(content_frame, fg_color="#16213e")
        right_panel.pack(side="right", fill="both", expand=True, padx=(10,0))
        
        ctk.CTkLabel(
            right_panel,
            text="SYSTEM INFORMATION",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00d2ff"
        ).pack(pady=(30,20))
        
        # Clock Display
        self.clock_label = ctk.CTkLabel(
            right_panel,
            text="",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        )
        self.clock_label.pack(pady=10)
        self.update_clock()
        
        # Date Display
        date_frame = ctk.CTkFrame(right_panel, fg_color="#0a1628", corner_radius=10)
        date_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            date_frame,
            text=f"📅 {datetime.now().strftime('%A, %B %d, %Y')}",
            font=ctk.CTkFont(size=16),
            text_color="#00d2ff"
        ).pack(pady=10)
        
        # Stats Frame
        stats_frame = ctk.CTkFrame(right_panel, fg_color="#0a1628", corner_radius=10)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            stats_frame,
            text="SYSTEM STATS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00ff88"
        ).pack(pady=(10,5))
        
        # Get registered users count
        reg_users = len(self.trainer.get_user_list())
        
        self.users_label = ctk.CTkLabel(
            stats_frame,
            text=f"Registered Users: {reg_users}",
            font=ctk.CTkFont(size=14),
            text_color="#ffffff"
        )
        self.users_label.pack(pady=5)
        
        # Today's attendance count
        today_att = self.get_today_attendance_count()
        
        self.att_count_label = ctk.CTkLabel(
            stats_frame,
            text=f"Today's Attendance: {today_att}",
            font=ctk.CTkFont(size=14),
            text_color="#ffffff"
        )
        self.att_count_label.pack(pady=(5,10))
        
        # Model Status Frame
        model_frame = ctk.CTkFrame(right_panel, fg_color="#0a1628", corner_radius=10)
        model_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            model_frame,
            text="MODEL STATUS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffa500"
        ).pack(pady=(10,5))
        
        # Check model status using trainer
        model_trained, model_msg = self.trainer.check_training_status()
        model_status_text = "✓ Trained & Ready" if model_trained else "✗ Not Trained"
        model_color = "#00ff88" if model_trained else "#ff6b6b"
        
        self.model_status_label = ctk.CTkLabel(
            model_frame,
            text=model_status_text,
            font=ctk.CTkFont(size=14),
            text_color=model_color
        )
        self.model_status_label.pack(pady=(5,5))
        
        # Additional model info
        self.model_info_label = ctk.CTkLabel(
            model_frame,
            text=model_msg if model_trained else "Train model to start",
            font=ctk.CTkFont(size=12),
            text_color="#a0a0a0"
        )
        self.model_info_label.pack(pady=(0,10))
        
        # Quick Tips Frame
        tips_frame = ctk.CTkFrame(right_panel, fg_color="#0a1628", corner_radius=10)
        tips_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            tips_frame,
            text="⚡ QUICK TIPS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f39c12"
        ).pack(pady=(10,5))
        
        tips_text = "• Ctrl+R: Register User\n• Ctrl+A: Mark Attendance\n• Ctrl+T: Train Model"
        ctk.CTkLabel(
            tips_frame,
            text=tips_text,
            font=ctk.CTkFont(size=12),
            text_color="#a0a0a0",
            justify="left"
        ).pack(pady=(5,10), padx=10)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-r>', lambda e: self.open_registration_window())
        self.root.bind('<Control-a>', lambda e: self.start_attendance())
        self.root.bind('<Control-t>', lambda e: self.train_model())
        self.root.bind('<Control-s>', lambda e: self.check_system_status())
        
    def update_clock(self):
        """Update the real-time clock display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.configure(text=f"🕐 {current_time}")
        self.root.after(1000, self.update_clock)
        
    def get_today_attendance_count(self):
        """Get today's attendance count"""
        if os.path.exists("attendance.csv"):
            try:
                df = pd.read_csv("attendance.csv")
                today = datetime.now().strftime("%Y-%m-%d")
                return len(df[df['Date'] == today]['Name'].unique())
            except:
                return 0
        return 0
        
    def open_registration_window(self):
        """Open the registration window"""
        reg_window = ctk.CTkToplevel(self.root)
        reg_window.title("Register New User")
        reg_window.geometry("800x600")
        reg_window.grab_set()  # Make window modal
        
        # Main container
        container = ctk.CTkFrame(reg_window, fg_color="#1a1a2e")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            container,
            text="📸 NEW USER REGISTRATION",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#00d2ff"
        ).pack(pady=20)
        
        # Name Entry Frame
        input_frame = ctk.CTkFrame(container, fg_color="#16213e")
        input_frame.pack(fill="x", padx=30, pady=20)
        
        ctk.CTkLabel(
            input_frame,
            text="Enter Full Name:",
            font=ctk.CTkFont(size=16),
            text_color="#ffffff"
        ).pack(pady=(20,10))
        
        name_entry = ctk.CTkEntry(
            input_frame,
            font=ctk.CTkFont(size=16),
            height=45,
            placeholder_text="e.g., Ali Ahmed",
            fg_color="#0a1628",
            border_color="#00d2ff"
        )
        name_entry.pack(padx=30, pady=(0,20), fill="x")
        
        # Progress Frame
        progress_frame = ctk.CTkFrame(container, fg_color="#16213e")
        progress_frame.pack(fill="x", padx=30, pady=20)
        
        progress_label = ctk.CTkLabel(
            progress_frame,
            text="Waiting to start capture...",
            font=ctk.CTkFont(size=14),
            text_color="#ffa500"
        )
        progress_label.pack(pady=10)
        
        progress_bar = ctk.CTkProgressBar(progress_frame)
        progress_bar.pack(padx=30, pady=10, fill="x")
        progress_bar.set(0)
        
        # Image counter label
        counter_label = ctk.CTkLabel(
            progress_frame,
            text="0/20 images captured",
            font=ctk.CTkFont(size=12),
            text_color="#a0a0a0"
        )
        counter_label.pack(pady=5)
        
        # Camera Preview
        preview_label = ctk.CTkLabel(container, text="")
        preview_label.pack(pady=10)
        
        # Control Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        # Variable to store capture state
        capture_state = {'is_running': False}
        
        def capture_images():
            """Capture 20 face images for registration"""
            name = name_entry.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Please enter a name")
                return
            
            # Check if user already exists
            existing_users = self.trainer.get_user_list()
            if name in existing_users:
                result = messagebox.askyesno(
                    "User Exists",
                    f"User '{name}' already exists. Do you want to add more images?"
                )
                if not result:
                    return
            
            # Create user folder
            user_folder = f"dataset/images/{name}"
            os.makedirs(user_folder, exist_ok=True)
            
            # Initialize webcam
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                messagebox.showerror("Error", "Cannot access webcam")
                return
            
            capture_state['is_running'] = True
            count = 0
            
            progress_label.configure(
                text=f"🎥 Capturing images for: {name}",
                text_color="#00ff88"
            )
            
            def process_frame():
                nonlocal count
                
                if not capture_state['is_running']:
                    cap.release()
                    cv2.destroyAllWindows()
                    return
                
                if count >= 20:
                    cap.release()
                    cv2.destroyAllWindows()
                    progress_label.configure(
                        text=f"✓ Registration Complete! {count} images saved for {name}",
                        text_color="#00ff88"
                    )
                    counter_label.configure(text=f"{count}/20 images captured")
                    
                    # Update system stats
                    self.update_stats()
                    
                    # Ask if user wants to train the model
                    if messagebox.askyesno(
                        "Train Model",
                        f"Registration complete for {name}!\n\nDo you want to train the model now?"
                    ):
                        reg_window.destroy()
                        self.train_model()
                    else:
                        messagebox.showinfo(
                            "Success",
                            f"Successfully registered {name} with {count} images.\n\nPlease train the model before using attendance."
                        )
                    return
                
                ret, frame = cap.read()
                if not ret:
                    return
                
                frame = cv2.flip(frame, 1)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                if len(faces) > 0:
                    for (x, y, w, h) in faces:
                        # Draw bounding box
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
                        # Save face image
                        if count < 20:
                            face_roi = gray[y:y+h, x:x+w]
                            face_roi = cv2.resize(face_roi, (200, 200))
                            cv2.imwrite(f"{user_folder}/{count}.jpg", face_roi)
                            count += 1
                            
                            # Update progress
                            progress = count / 20
                            progress_bar.set(progress)
                            progress_label.configure(
                                text=f"Capturing: Image {count}/20"
                            )
                            counter_label.configure(text=f"{count}/20 images captured")
                            
                            # Small delay to get different angles
                            time.sleep(0.1)
                else:
                    cv2.putText(
                        frame, "No Face Detected!",
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2
                    )
                
                # Display frame in GUI
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_rgb = cv2.resize(frame_rgb, (400, 300))
                img = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(img)
                preview_label.configure(image=img_tk)
                preview_label.image = img_tk
                
                # Continue capturing
                if count < 20:
                    reg_window.after(10, process_frame)
            
            # Start capture process
            process_frame()
        
        def stop_capture():
            """Stop the capture process"""
            capture_state['is_running'] = False
            progress_label.configure(
                text="Capture stopped by user",
                text_color="#ff6b6b"
            )
        
        start_btn = ctk.CTkButton(
            btn_frame,
            text="🎥 Start Capture (20 Images)",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color="#0f3460",
            hover_color="#16213e",
            command=capture_images
        )
        start_btn.pack(side="left", padx=10)
        
        stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ Stop",
            font=ctk.CTkFont(size=16),
            height=50,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=stop_capture
        )
        stop_btn.pack(side="left", padx=10)
        
        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            font=ctk.CTkFont(size=16),
            height=50,
            fg_color="#ff6b6b",
            hover_color="#ee5a5a",
            command=reg_window.destroy
        )
        close_btn.pack(side="left", padx=10)
        
    def train_model(self):
        """Train the LBPH face recognizer using train module"""
        self.update_status("Training model...", "#ffa500")
        
        # Disable train button during training
        self.train_btn.configure(state="disabled", text="Training...")
        
        def train():
            try:
                # Use the FaceTrainer class from train.py
                success, message = self.trainer.train_model()
                
                if success:
                    # Reload the trained model
                    self.recognizer.read("trainer.yml")
                    with open("labels.pkl", 'rb') as f:
                        self.labels = pickle.load(f)
                    self.model_loaded = True
                    
                    # Update model status in GUI
                    self.model_status_label.configure(
                        text="✓ Trained & Ready",
                        text_color="#00ff88"
                    )
                    
                    # Update model info
                    trained, model_msg = self.trainer.check_training_status()
                    self.model_info_label.configure(text=model_msg)
                    
                    self.update_status("Model trained successfully!", "#00ff88")
                    
                    # Show success message
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Training Complete",
                        message
                    ))
                    
                    # Update stats
                    self.update_stats()
                    
                else:
                    self.update_status(f"Training failed!", "#ff6b6b")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Training Failed",
                        message
                    ))
                
                # Re-enable train button
                self.train_btn.configure(state="normal", text="🔄 Train Model")
                
            except Exception as e:
                error_msg = f"Error during training: {str(e)}"
                self.update_status(error_msg, "#ff6b6b")
                self.train_btn.configure(state="normal", text="🔄 Train Model")
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        
        # Run training in separate thread
        thread = threading.Thread(target=train)
        thread.daemon = True
        thread.start()
        
    def check_system_status(self):
        """Check and display system status"""
        # Get registered users
        users = self.trainer.get_user_list()
        
        # Check model status
        model_trained, model_msg = self.trainer.check_training_status()
        
        # Get dataset info
        total_images = 0
        if os.path.exists("dataset/images"):
            for user in users:
                user_folder = f"dataset/images/{user}"
                if os.path.exists(user_folder):
                    total_images += len([f for f in os.listdir(user_folder) 
                                       if f.endswith(('.jpg', '.jpeg', '.png'))])
        
        # Check today's attendance
        today_att = self.get_today_attendance_count()
        
        # Create status message
        status_msg = f"""
SYSTEM STATUS REPORT
{'='*50}

📊 DATASET INFORMATION:
• Registered Users: {len(users)}
• Total Images: {total_images}
• Users List: {', '.join(users) if users else 'No users registered'}

🤖 MODEL STATUS:
• Trained: {'Yes' if model_trained else 'No'}
• {model_msg}

📋 TODAY'S ATTENDANCE:
• Marked: {today_att} students
• Date: {datetime.now().strftime('%Y-%m-%d')}

💾 FILES STATUS:
• Dataset Folder: {'✓' if os.path.exists('dataset/images') else '✗'}
• Model File (trainer.yml): {'✓' if os.path.exists('trainer.yml') else '✗'}
• Labels File (labels.pkl): {'✓' if os.path.exists('labels.pkl') else '✗'}
• Attendance File: {'✓' if os.path.exists('attendance.csv') else '✗'}

⚡ RECOMMENDATIONS:
{f"• System is ready for attendance marking" if model_trained else "• Train the model before marking attendance"}
{f"• {len(users)} users available for recognition" if users else "• Register at least one user first"}
"""
        
        # Show status in a new window
        status_window = ctk.CTkToplevel(self.root)
        status_window.title("System Status")
        status_window.geometry("600x500")
        status_window.grab_set()
        
        container = ctk.CTkFrame(status_window, fg_color="#1a1a2e")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            container,
            text="🔍 SYSTEM STATUS",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#00d2ff"
        ).pack(pady=20)
        
        status_text = ctk.CTkTextbox(
            container,
            font=ctk.CTkFont(size=13, family="Courier"),
            fg_color="#0a1628"
        )
        status_text.pack(fill="both", expand=True, padx=30, pady=20)
        status_text.insert("1.0", status_msg)
        status_text.configure(state="disabled")  # Make read-only
        
        ctk.CTkButton(
            container,
            text="Close",
            font=ctk.CTkFont(size=16),
            fg_color="#ff6b6b",
            hover_color="#ee5a5a",
            command=status_window.destroy
        ).pack(pady=20)
        
    def start_attendance(self):
        """Start attendance marking with face recognition"""
        if not self.model_loaded:
            messagebox.showerror(
                "Model Not Trained",
                "Please train the model first!\n\nClick 'Train Model' button or press Ctrl+T"
            )
            return
        
        # Clear today's attendance set for new session
        self.attendance_marked.clear()
        
        # Create attendance window
        att_window = ctk.CTkToplevel(self.root)
        att_window.title("Mark Attendance")
        att_window.geometry("900x700")
        att_window.grab_set()
        
        # Main container
        container = ctk.CTkFrame(att_window, fg_color="#1a1a2e")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(
            container,
            text="📋 ATTENDANCE MARKING",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#00ff88"
        ).pack(pady=20)
        
        # Camera preview
        preview_label = ctk.CTkLabel(container, text="")
        preview_label.pack(pady=10)
        
        # Recognition info
        info_frame = ctk.CTkFrame(container, fg_color="#16213e")
        info_frame.pack(fill="x", padx=30, pady=10)
        
        self.recognition_label = ctk.CTkLabel(
            info_frame,
            text="Initializing camera...",
            font=ctk.CTkFont(size=16),
            text_color="#ffffff"
        )
        self.recognition_label.pack(pady=10)
        
        # Today's attendance list
        att_frame = ctk.CTkFrame(container, fg_color="#16213e")
        att_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        ctk.CTkLabel(
            att_frame,
            text="Today's Attendance List",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#00d2ff"
        ).pack(pady=10)
        
        att_text = ctk.CTkTextbox(
            att_frame,
            font=ctk.CTkFont(size=14),
            fg_color="#0a1628"
        )
        att_text.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Load existing today's attendance
        self.update_attendance_display(att_text)
        
        # Control buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ Stop Attendance",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=lambda: self.stop_attendance(att_window)
        )
        stop_btn.pack(side="left", padx=10)
        
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Cannot access webcam")
            att_window.destroy()
            return
        
        # Store cap in window for cleanup
        att_window.cap = cap
        att_window.is_running = True
        
        def recognize_faces():
            """Process webcam feed for face recognition"""
            if not att_window.is_running:
                return
            
            ret, frame = cap.read()
            if not ret:
                return
            
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            recognized_name = "Unknown"
            color = (0, 0, 255)  # Red for unknown
            
            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (200, 200))
                
                try:
                    # Predict
                    label, confidence = self.recognizer.predict(face_roi)
                    
                    if confidence < 70:  # Confidence threshold
                        recognized_name = self.labels.get(label, "Unknown")
                        color = (0, 255, 0)  # Green for recognized
                        
                        # Mark attendance if not already marked today
                        if recognized_name not in self.attendance_marked:
                            self.mark_attendance(recognized_name)
                            
                            # Update attendance display
                            self.update_attendance_display(att_text)
                    else:
                        recognized_name = "Unknown"
                        color = (0, 0, 255)
                
                except Exception as e:
                    recognized_name = "Error"
                    color = (0, 0, 255)
                
                # Draw rectangle and name
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(
                    frame, recognized_name,
                    (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    color,
                    2
                )
                
                # Show confidence if recognized
                if recognized_name != "Unknown" and recognized_name != "Error":
                    cv2.putText(
                        frame, f"Conf: {100-confidence:.1f}%",
                        (x, y+h+25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )
            
            # Update recognition label
            self.recognition_label.configure(
                text=f"Detected: {recognized_name}",
                text_color="#00ff88" if recognized_name not in ["Unknown", "Error"] else "#ff6b6b"
            )
            
            # Display frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.resize(frame_rgb, (600, 400))
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(img)
            preview_label.configure(image=img_tk)
            preview_label.image = img_tk
            
            # Continue processing
            att_window.after(10, recognize_faces)
        
        # Handle window close
        att_window.protocol("WM_DELETE_WINDOW", lambda: self.stop_attendance(att_window))
        
        # Start recognition
        recognize_faces()
        
    def stop_attendance(self, window):
        """Stop attendance marking"""
        if hasattr(window, 'cap'):
            window.cap.release()
        window.is_running = False
        window.destroy()
        self.update_status("System Ready", "#00ff88")
        
    def mark_attendance(self, name):
        """Mark attendance in CSV file"""
        if name in self.attendance_marked:
            return
        
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        
        # Add new entry
        new_entry = pd.DataFrame({
            'Name': [name],
            'Date': [date],
            'Time': [time]
        })
        
        if os.path.exists("attendance.csv"):
            try:
                df = pd.read_csv("attendance.csv")
                df = pd.concat([df, new_entry], ignore_index=True)
            except:
                df = new_entry
        else:
            df = new_entry
        
        df.to_csv("attendance.csv", index=False)
        self.attendance_marked.add(name)
        
        # Update main stats
        self.update_stats()
        
        print(f"✓ Attendance marked: {name} at {time}")  # Console log
        
    def update_attendance_display(self, text_widget):
        """Update the attendance display in real-time"""
        if not os.path.exists("attendance.csv"):
            text_widget.delete(1.0, "end")
            text_widget.insert("end", "No attendance records found")
            return
        
        try:
            df = pd.read_csv("attendance.csv")
            today = datetime.now().strftime("%Y-%m-%d")
            today_df = df[df['Date'] == today]
            
            text_widget.delete(1.0, "end")
            
            if today_df.empty:
                text_widget.insert("end", "No attendance marked today yet")
            else:
                # Sort by time
                today_df = today_df.sort_values('Time')
                
                text_widget.insert("end", "✓ Today's Attendance:\n\n")
                for idx, row in today_df.iterrows():
                    text_widget.insert(
                        "end",
                        f"  • {row['Name']} - {row['Time']}\n"
                    )
                
                text_widget.insert("end", f"\nTotal: {len(today_df)} students")
        except Exception as e:
            text_widget.delete(1.0, "end")
            text_widget.insert("end", f"Error loading attendance: {e}")
        
    def view_attendance(self):
        """View attendance records"""
        view_window = ctk.CTkToplevel(self.root)
        view_window.title("Attendance Records")
        view_window.geometry("1000x600")
        view_window.grab_set()
        
        container = ctk.CTkFrame(view_window, fg_color="#1a1a2e")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            container,
            text="📊 ATTENDANCE RECORDS",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#00d2ff"
        ).pack(pady=20)
        
        # Load attendance data
        if os.path.exists("attendance.csv"):
            try:
                df = pd.read_csv("attendance.csv")
                
                # Create a frame for table-like display
                table_frame = ctk.CTkFrame(container, fg_color="#16213e")
                table_frame.pack(fill="both", expand=True, padx=30, pady=20)
                
                # Headers
                headers_frame = ctk.CTkFrame(table_frame, fg_color="#0f3460")
                headers_frame.pack(fill="x")
                
                for col, width in [("Name", 200), ("Date", 150), ("Time", 150)]:
                    ctk.CTkLabel(
                        headers_frame,
                        text=col,
                        font=ctk.CTkFont(size=14, weight="bold"),
                        width=width,
                        text_color="#ffffff"
                    ).pack(side="left", padx=5, pady=10)
                
                # Scrollable content
                content_frame = ctk.CTkScrollableFrame(
                    table_frame,
                    fg_color="#0a1628"
                )
                content_frame.pack(fill="both", expand=True)
                
                if df.empty:
                    ctk.CTkLabel(
                        content_frame,
                        text="No attendance records found",
                        font=ctk.CTkFont(size=16),
                        text_color="#ff6b6b"
                    ).pack(pady=20)
                else:
                    # Sort by date and time (newest first)
                    df = df.sort_values(['Date', 'Time'], ascending=[False, False])
                    
                    for _, row in df.iterrows():
                        row_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                        row_frame.pack(fill="x", pady=2)
                        
                        for value, width in [(row['Name'], 200), (row['Date'], 150), (row['Time'], 150)]:
                            ctk.CTkLabel(
                                row_frame,
                                text=str(value),
                                font=ctk.CTkFont(size=13),
                                width=width,
                                text_color="#a0a0a0"
                            ).pack(side="left", padx=5, pady=5)
            except Exception as e:
                ctk.CTkLabel(
                    container,
                    text=f"Error loading attendance: {str(e)}",
                    font=ctk.CTkFont(size=16),
                    text_color="#ff6b6b"
                ).pack()
        else:
            ctk.CTkLabel(
                container,
                text="No attendance records found",
                font=ctk.CTkFont(size=16),
                text_color="#ff6b6b"
            ).pack(pady=50)
        
        # Close button
        ctk.CTkButton(
            container,
            text="Close",
            font=ctk.CTkFont(size=16),
            fg_color="#ff6b6b",
            hover_color="#ee5a5a",
            command=view_window.destroy
        ).pack(pady=20)
        
    def update_status(self, message, color):
        """Update the status label"""
        self.status_label.configure(text=message, text_color=color)
        
    def update_stats(self):
        """Update system statistics"""
        # Update registered users count
        reg_users = len(self.trainer.get_user_list())
        self.users_label.configure(text=f"Registered Users: {reg_users}")
        
        # Update today's attendance count
        today_att = self.get_today_attendance_count()
        self.att_count_label.configure(text=f"Today's Attendance: {today_att}")
        
        # Update model status
        model_trained, model_msg = self.trainer.check_training_status()
        model_status_text = "✓ Trained & Ready" if model_trained else "✗ Not Trained"
        model_color = "#00ff88" if model_trained else "#ff6b6b"
        
        self.model_status_label.configure(text=model_status_text, text_color=model_color)
        self.model_info_label.configure(text=model_msg if model_trained else "Train model to start")
        
    def run(self):
        """Run the main application"""
        self.update_stats()  # Initial stats update
        self.root.mainloop()

if __name__ == "__main__":
    app = FaceRecognitionSystem()
    app.run()