import os
import cv2
import numpy as np
import pickle
from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime

class FaceTrainer:
    def __init__(self):
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
    def train_model(self, dataset_path="dataset/images"):
        """
        Train the LBPH face recognizer with images from dataset
        
        Args:
            dataset_path: Path to the dataset folder
            
        Returns:
            bool: True if training successful, False otherwise
            str: Status message
        """
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting model training...")
            
            # Check if dataset exists
            if not os.path.exists(dataset_path):
                return False, "Dataset folder not found! Please register users first."
            
            # Get all user folders
            users = os.listdir(dataset_path)
            if not users:
                return False, "No users registered! Please register at least one user first."
            
            faces = []
            labels = []
            label_map = {}
            current_label = 0
            total_images = 0
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(users)} users")
            
            # Process each user
            for user in users:
                user_folder = os.path.join(dataset_path, user)
                
                # Skip if not a directory
                if not os.path.isdir(user_folder):
                    continue
                
                # Add user to label map
                label_map[current_label] = user
                user_images = 0
                
                # Process each image for this user
                for image_name in os.listdir(user_folder):
                    if image_name.endswith(('.jpg', '.jpeg', '.png')):
                        image_path = os.path.join(user_folder, image_name)
                        
                        # Read image in grayscale
                        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                        
                        if img is not None:
                            # Check if image contains a face (quality check)
                            faces_detected = self.face_cascade.detectMultiScale(
                                img, 
                                scaleFactor=1.1, 
                                minNeighbors=5
                            )
                            
                            if len(faces_detected) > 0:
                                faces.append(img)
                                labels.append(current_label)
                                user_images += 1
                                total_images += 1
                            else:
                                print(f"  Warning: No face detected in {image_path}")
                        else:
                            print(f"  Warning: Could not read {image_path}")
                
                print(f"  User '{user}': {user_images} valid images")
                current_label += 1
            
            # Check if we have enough data
            if total_images == 0:
                return False, "No valid face images found for training!"
            
            if total_images < 10:
                return False, f"Insufficient data: Only {total_images} images found. Need at least 10."
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Training with {total_images} images...")
            
            # Train the recognizer
            self.recognizer.train(faces, np.array(labels))
            
            # Save the trained model
            self.recognizer.write("trainer.yml")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Model saved to 'trainer.yml'")
            
            # Save label mapping
            with open("labels.pkl", 'wb') as f:
                pickle.dump(label_map, f)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Labels saved to 'labels.pkl'")
            
            # Generate training report
            self.generate_training_report(label_map, total_images)
            
            success_msg = f"Training completed successfully!\n\nUsers trained: {len(label_map)}\nTotal images: {total_images}\n\nUsers: {', '.join(label_map.values())}"
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Training completed successfully!")
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Training failed: {str(e)}"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {error_msg}")
            return False, error_msg
    
    def generate_training_report(self, label_map, total_images):
        """Generate a training report file"""
        try:
            with open("training_report.txt", "w") as f:
                f.write("=" * 50 + "\n")
                f.write("FACE RECOGNITION MODEL TRAINING REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Users Trained: {len(label_map)}\n")
                f.write(f"Total Images Used: {total_images}\n\n")
                f.write("Registered Users:\n")
                f.write("-" * 30 + "\n")
                
                for label_id, user_name in label_map.items():
                    # Count images for this user
                    user_folder = f"dataset/images/{user_name}"
                    if os.path.exists(user_folder):
                        image_count = len([f for f in os.listdir(user_folder) 
                                         if f.endswith(('.jpg', '.jpeg', '.png'))])
                        f.write(f"  • {user_name} (ID: {label_id}) - {image_count} images\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("Model saved as: trainer.yml\n")
                f.write("Labels saved as: labels.pkl\n")
                f.write("=" * 50 + "\n")
                
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Training report generated")
        except Exception as e:
            print(f"Warning: Could not generate training report: {e}")
    
    def check_training_status(self):
        """Check if model is already trained"""
        if os.path.exists("trainer.yml") and os.path.exists("labels.pkl"):
            try:
                # Try to load the model
                self.recognizer.read("trainer.yml")
                with open("labels.pkl", 'rb') as f:
                    labels = pickle.load(f)
                return True, f"Model is trained with {len(labels)} users"
            except:
                return False, "Model files are corrupted"
        return False, "Model not trained yet"
    
    def get_user_list(self):
        """Get list of registered users from dataset"""
        dataset_path = "dataset/images"
        if not os.path.exists(dataset_path):
            return []
        
        users = []
        for item in os.listdir(dataset_path):
            if os.path.isdir(os.path.join(dataset_path, item)):
                users.append(item)
        return users


class TrainingGUI:
    """GUI for the training module"""
    
    def __init__(self):
        self.trainer = FaceTrainer()
        
    def show_training_window(self, parent=None):
        """Show training progress window"""
        if parent:
            train_window = ctk.CTkToplevel(parent)
        else:
            train_window = ctk.CTk()
            
        train_window.title("Training Model")
        train_window.geometry("600x500")
        
        if parent:
            train_window.grab_set()
        
        # Main container
        container = ctk.CTkFrame(train_window, fg_color="#1a1a2e")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            container,
            text="🔄 TRAINING MODEL",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffa500"
        ).pack(pady=20)
        
        # Status display
        status_frame = ctk.CTkFrame(container, fg_color="#16213e")
        status_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        status_text = ctk.CTkTextbox(
            status_frame,
            font=ctk.CTkFont(size=14),
            fg_color="#0a1628"
        )
        status_text.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Progress bar
        progress_bar = ctk.CTkProgressBar(container)
        progress_bar.pack(padx=30, pady=10, fill="x")
        progress_bar.set(0)
        progress_bar.configure(mode="indeterminate")
        progress_bar.start()
        
        # Status label
        status_label = ctk.CTkLabel(
            container,
            text="Initializing training...",
            font=ctk.CTkFont(size=14),
            text_color="#ffffff"
        )
        status_label.pack(pady=10)
        
        def start_training():
            """Start the training process"""
            # Get registered users
            users = self.trainer.get_user_list()
            
            status_text.insert("end", "Starting training process...\n")
            status_text.insert("end", f"Found {len(users)} registered users\n")
            status_text.insert("end", "-" * 40 + "\n\n")
            
            # Update status
            status_label.configure(text="Training in progress...", text_color="#ffa500")
            
            # Train the model
            success, message = self.trainer.train_model()
            
            progress_bar.stop()
            progress_bar.set(1)
            
            if success:
                status_label.configure(text="✓ Training completed!", text_color="#00ff88")
                status_text.insert("end", f"✓ {message}\n")
                
                if not parent:
                    messagebox.showinfo("Success", message)
            else:
                status_label.configure(text="✗ Training failed!", text_color="#ff6b6b")
                status_text.insert("end", f"✗ {message}\n")
                
                if not parent:
                    messagebox.showerror("Error", message)
            
            # Add close button if standalone
            if not parent:
                ctk.CTkButton(
                    container,
                    text="Close",
                    font=ctk.CTkFont(size=16),
                    fg_color="#ff6b6b",
                    hover_color="#ee5a5a",
                    command=train_window.destroy
                ).pack(pady=20)
        
        # Start training after a short delay
        train_window.after(500, start_training)
        
        if not parent:
            train_window.mainloop()


# Main execution
if __name__ == "__main__":
    # Configure appearance for standalone mode
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create and show training GUI
    training_gui = TrainingGUI()
    training_gui.show_training_window()
    
    # Alternative: Command line training (without GUI)
    # trainer = FaceTrainer()
    # success, message = trainer.train_model()
    # print(message)