"""
Face recognition module using LBPH
"""

import cv2
import numpy as np
import pickle
import os
from utils.config import (
    MODEL_FILE,
    LABELS_FILE,
    CONFIDENCE_THRESHOLD,
    FACE_SIZE
)

class FaceRecognizer:
    """Face recognition class using LBPH"""
    
    def __init__(self):
        """Initialize face recognizer"""
        self.recognizer = None
        self.labels = {}
        self.is_model_loaded = False
        self.init_recognizer()
    
    def init_recognizer(self):
        """Initialize LBPH recognizer"""
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            print("FaceRecognizer: LBPH recognizer created")
        except Exception as e:
            print(f"FaceRecognizer: Error creating recognizer - {e}")
            # Fallback
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    def load_model(self):
        """
        Load trained model from files
        
        Returns:
            tuple: (success, message)
        """
        try:
            if not os.path.exists(MODEL_FILE):
                return False, f"Model file not found: {MODEL_FILE}"
            
            if not os.path.exists(LABELS_FILE):
                return False, f"Labels file not found: {LABELS_FILE}"
            
            # Check file sizes
            if os.path.getsize(MODEL_FILE) == 0:
                return False, "Model file is empty"
            
            if os.path.getsize(LABELS_FILE) == 0:
                return False, "Labels file is empty"
            
            # Read model
            self.recognizer.read(str(MODEL_FILE))
            print(f"FaceRecognizer: Model read from {MODEL_FILE}")
            
            # Read labels
            with open(LABELS_FILE, 'rb') as f:
                self.labels = pickle.load(f)
            print(f"FaceRecognizer: Labels loaded - {len(self.labels)} users: {list(self.labels.values())}")
            
            self.is_model_loaded = True
            return True, f"Model loaded with {len(self.labels)} users"
            
        except Exception as e:
            self.is_model_loaded = False
            error_msg = f"Error loading model: {str(e)}"
            print(f"FaceRecognizer: {error_msg}")
            return False, error_msg
    
    def predict(self, face_roi):
        """
        Predict/recognize a face
        
        Args:
            face_roi: Face image ROI (grayscale)
        
        Returns:
            tuple: (name, confidence, label_id)
        """
        if not self.is_model_loaded:
            print("FaceRecognizer: Model not loaded, cannot predict")
            return "Unknown", 100, -1
        
        if face_roi is None:
            return "Unknown", 100, -1
        
        try:
            # Ensure correct size
            if face_roi.shape[:2] != FACE_SIZE:
                face_roi = cv2.resize(face_roi, FACE_SIZE)
            
            # Predict
            label_id, confidence = self.recognizer.predict(face_roi)
            
            # Check confidence threshold
            # LBPH returns distance (lower = better match)
            if confidence < CONFIDENCE_THRESHOLD:
                name = self.labels.get(label_id, "Unknown")
                if name == "Unknown":
                    print(f"FaceRecognizer: Label {label_id} not found in labels map")
                return name, confidence, label_id
            else:
                return "Unknown", confidence, -1
                
        except Exception as e:
            print(f"FaceRecognizer: Prediction error - {e}")
            return "Unknown", 100, -1
    
    def save_model(self, faces, labels, label_map):
        """
        Train and save the model
        
        Args:
            faces: List of face images
            labels: List of corresponding labels
            label_map: Dictionary mapping label_id to name
        
        Returns:
            tuple: (success, message)
        """
        try:
            if not faces or not labels:
                return False, "No training data provided"
            
            if len(faces) != len(labels):
                return False, "Faces and labels count mismatch"
            
            print(f"FaceRecognizer: Training with {len(faces)} images, {len(label_map)} users")
            
            # Create new recognizer
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            
            # Train
            self.recognizer.train(faces, np.array(labels))
            print("FaceRecognizer: Training completed")
            
            # Save model
            os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
            self.recognizer.write(str(MODEL_FILE))
            print(f"FaceRecognizer: Model saved to {MODEL_FILE}")
            
            # Save labels
            with open(LABELS_FILE, 'wb') as f:
                pickle.dump(label_map, f)
            print(f"FaceRecognizer: Labels saved to {LABELS_FILE}")
            
            # Update current instance
            self.labels = label_map
            self.is_model_loaded = True
            
            return True, "Model trained and saved successfully"
            
        except Exception as e:
            error_msg = f"Error saving model: {str(e)}"
            print(f"FaceRecognizer: {error_msg}")
            return False, error_msg
    
    def get_user_count(self):
        """Get number of trained users"""
        return len(self.labels) if self.labels else 0
    
    def get_user_list(self):
        """Get list of trained user names"""
        return list(self.labels.values()) if self.labels else []
    
    def is_trained(self):
        """Check if model is trained and loaded"""
        return self.is_model_loaded and len(self.labels) > 0