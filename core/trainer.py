"""
Model training module
"""

import cv2
import os
import numpy as np
from datetime import datetime
from utils.config import (
    DATASET_DIR,
    TRAINING_REPORT,
    FACE_SIZE,
    MODEL_FILE,
    LABELS_FILE
)
from core.face_detector import FaceDetector
from core.face_recognizer import FaceRecognizer

class ModelTrainer:
    """Model training class"""
    
    def __init__(self):
        """Initialize trainer"""
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.training_log = []
        
        # Try to load existing model
        self.load_existing_model()
    
    def load_existing_model(self):
        """Load existing model if available"""
        try:
            if os.path.exists(MODEL_FILE) and os.path.exists(LABELS_FILE):
                success, message = self.face_recognizer.load_model()
                if success:
                    print(f"ModelTrainer: {message}")
                else:
                    print(f"ModelTrainer: {message}")
        except Exception as e:
            print(f"ModelTrainer: Error loading model - {e}")
    
    def get_registered_users(self):
        """
        Get list of registered users from dataset
        
        Returns:
            list: List of user names
        """
        if not os.path.exists(DATASET_DIR):
            return []
        
        users = []
        try:
            for item in os.listdir(DATASET_DIR):
                item_path = os.path.join(DATASET_DIR, item)
                if os.path.isdir(item_path):
                    has_images = False
                    for file in os.listdir(item_path):
                        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            has_images = True
                            break
                    if has_images:
                        users.append(item)
        except Exception as e:
            print(f"Error getting users: {e}")
        
        return sorted(users)
    
    def get_user_image_count(self, user_name):
        """
        Get number of images for a user
        
        Args:
            user_name: Name of the user
        
        Returns:
            int: Number of images
        """
        user_folder = os.path.join(DATASET_DIR, user_name)
        
        if not os.path.exists(user_folder):
            return 0
        
        count = 0
        try:
            for file in os.listdir(user_folder):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    count += 1
        except:
            pass
        
        return count
    
    def prepare_dataset(self):
        """
        Prepare dataset for training
        
        Returns:
            tuple: (faces, labels, label_map, success, message)
        """
        try:
            users = self.get_registered_users()
            
            if not users:
                return None, None, None, False, "No registered users found! Please register a user first."
            
            faces = []
            labels = []
            label_map = {}
            current_label = 0
            total_images = 0
            skipped_images = 0
            
            self.training_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Preparing dataset...")
            self.training_log.append(f"Found {len(users)} users: {', '.join(users)}")
            self.training_log.append("")
            
            for user in users:
                user_folder = os.path.join(DATASET_DIR, user)
                
                if not os.path.isdir(user_folder):
                    continue
                
                label_map[current_label] = user
                user_images = 0
                
                self.training_log.append(f"  Processing: {user}")
                
                image_files = [f for f in os.listdir(user_folder) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                
                if not image_files:
                    self.training_log.append(f"    WARNING: No images found for {user}")
                    current_label += 1
                    continue
                
                for image_name in image_files:
                    image_path = os.path.join(user_folder, image_name)
                    
                    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                    
                    if img is None:
                        skipped_images += 1
                        continue
                    
                    _, detected_faces = self.face_detector.detect_faces(img, draw_box=False)
                    
                    if len(detected_faces) > 0:
                        x, y, w, h = detected_faces[0]
                        face_roi = img[y:y+h, x:x+w]
                        face_roi = cv2.resize(face_roi, FACE_SIZE)
                    else:
                        face_roi = cv2.resize(img, FACE_SIZE)
                    
                    faces.append(face_roi)
                    labels.append(current_label)
                    user_images += 1
                    total_images += 1
                
                self.training_log.append(f"    {user_images} images processed")
                current_label += 1
            
            if total_images < 2:
                return None, None, None, False, f"Insufficient training data. Found only {total_images} valid images."
            
            self.training_log.append(f"\nTotal images: {total_images}")
            if skipped_images > 0:
                self.training_log.append(f"Skipped images: {skipped_images}")
            
            return faces, labels, label_map, True, "Dataset prepared successfully"
            
        except Exception as e:
            error_msg = f"Error preparing dataset: {str(e)}"
            self.training_log.append(f"ERROR: {error_msg}")
            return None, None, None, False, error_msg
    
    def train_model(self):
        """
        Train the face recognition model
        
        Returns:
            tuple: (success, message)
        """
        try:
            self.training_log = []
            self.training_log.append("="*50)
            self.training_log.append("FACE RECOGNITION MODEL TRAINING")
            self.training_log.append("="*50)
            self.training_log.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.training_log.append("")
            
            users = self.get_registered_users()
            if not users:
                msg = "No registered users found! Please register at least one user first."
                self.training_log.append(f"ERROR: {msg}")
                return False, msg
            
            faces, labels, label_map, success, message = self.prepare_dataset()
            
            if not success:
                self.training_log.append(f"ERROR: {message}")
                return False, message
            
            self.training_log.append(f"\nTraining model with {len(faces)} images...")
            self.training_log.append(f"Users to train: {len(label_map)}")
            
            success, message = self.face_recognizer.save_model(faces, labels, label_map)
            
            if success:
                self.training_log.append("Training completed successfully!")
                self.training_log.append(f"Users trained: {len(label_map)}")
                self.training_log.append(f"Users: {', '.join(label_map.values())}")
                
                print("Trainer: Forcing model reload after training...")
                reload_success, reload_msg = self.face_recognizer.load_model()
                if reload_success:
                    self.training_log.append(f"Model reloaded: {reload_msg}")
                    print(f"Trainer: {reload_msg}")
                else:
                    self.training_log.append(f"Model reload warning: {reload_msg}")
                    print(f"Trainer Warning: {reload_msg}")
                
                self._generate_report()
                
                success_msg = (
                    f"Training completed successfully!\n\n"
                    f"Users trained: {len(label_map)}\n"
                    f"Total images: {len(faces)}\n"
                    f"Users: {', '.join(label_map.values())}\n\n"
                    f"Model is now ready for attendance marking!"
                )
                
                return True, success_msg
            else:
                self.training_log.append(f"ERROR: {message}")
                return False, message
            
        except Exception as e:
            error_msg = f"Training error: {str(e)}"
            self.training_log.append(f"ERROR: {error_msg}")
            print(f"Trainer Error: {error_msg}")
            return False, error_msg
    
    def _generate_report(self):
        """Generate training report file"""
        try:
            os.makedirs(os.path.dirname(TRAINING_REPORT), exist_ok=True)
            
            clean_log = []
            for line in self.training_log:
                clean_line = line.replace('\u2713', '[OK]')
                clean_line = clean_line.replace('\u26a0', '[WARN]')
                clean_line = clean_line.replace('\u2717', '[FAIL]')
                clean_log.append(clean_line)
            
            with open(TRAINING_REPORT, 'w', encoding='utf-8') as f:
                f.write('\n'.join(clean_log))
                f.write("\n\n")
                f.write("="*50 + "\n")
                f.write(f"Model file: {MODEL_FILE}\n")
                f.write(f"Labels file: {LABELS_FILE}\n")
                f.write("="*50 + "\n")
            
            print(f"Training report saved to: {TRAINING_REPORT}")
            
        except Exception as e:
            print(f"Warning: Could not save report: {e}")
    
    def check_training_status(self):
        """
        Check if model is trained and loaded
        
        Returns:
            tuple: (is_trained, message)
        """
        if not os.path.exists(MODEL_FILE) or not os.path.exists(LABELS_FILE):
            return False, "Model files not found. Train the model first."
        
        if self.face_recognizer.is_trained():
            user_count = self.face_recognizer.get_user_count()
            return True, f"Model is loaded with {user_count} users"
        
        success, message = self.face_recognizer.load_model()
        
        if success:
            return True, message
        else:
            return False, f"Model files exist but failed to load: {message}"
    
    def get_training_log(self):
        """Get training log"""
        return self.training_log
    
    def verify_model_files(self):
        """
        Verify that model files exist and are valid
        
        Returns:
            tuple: (valid, message)
        """
        if not os.path.exists(MODEL_FILE):
            return False, f"Model file not found: {MODEL_FILE}"
        
        if not os.path.exists(LABELS_FILE):
            return False, f"Labels file not found: {LABELS_FILE}"
        
        model_size = os.path.getsize(MODEL_FILE)
        labels_size = os.path.getsize(LABELS_FILE)
        
        if model_size == 0:
            return False, "Model file is empty"
        
        if labels_size == 0:
            return False, "Labels file is empty"
        
        return True, f"Model files OK (Model: {model_size} bytes, Labels: {labels_size} bytes)"