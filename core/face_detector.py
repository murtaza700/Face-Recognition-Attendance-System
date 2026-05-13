"""
Face detection module using Haar Cascade
"""

import cv2
import numpy as np
from utils.config import (
    HAAR_SCALE_FACTOR,
    HAAR_MIN_NEIGHBORS,
    FACE_SIZE,
    COLOR_GREEN,
    COLOR_RED
)
from utils.helpers import play_sound

class FaceDetector:
    """Face detection class"""
    
    def __init__(self):
        """Initialize face detector with Haar Cascade"""
        self.face_cascade = None
        self.load_cascade()
    
    def load_cascade(self):
        """Load Haar Cascade classifier"""
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                raise Exception("Failed to load cascade classifier")
            
            return True, "Cascade loaded successfully"
            
        except Exception as e:
            return False, f"Error loading cascade: {str(e)}"
    
    def detect_faces(self, image, draw_box=True, box_color=COLOR_GREEN):
        """
        Detect faces in an image
        
        Args:
            image: Input image (BGR or Grayscale)
            draw_box: Whether to draw bounding boxes
            box_color: Color for bounding boxes (BGR)
        
        Returns:
            tuple: (processed_image, faces_list)
            faces_list: List of (x, y, w, h) tuples
        """
        if self.face_cascade is None:
            return image, []
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=HAAR_SCALE_FACTOR,
            minNeighbors=HAAR_MIN_NEIGHBORS,
            minSize=(50, 50),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Draw bounding boxes if requested
        if draw_box and len(faces) > 0:
            for (x, y, w, h) in faces:
                cv2.rectangle(image, (x, y), (x+w, y+h), box_color, 2)
        
        return image, faces
    
    def extract_face_roi(self, image, face_coords):
        """
        Extract face region of interest
        
        Args:
            image: Grayscale image
            face_coords: (x, y, w, h) tuple
        
        Returns:
            numpy array: Face ROI resized to FACE_SIZE
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        x, y, w, h = face_coords
        
        # Extract face region
        face_roi = gray[y:y+h, x:x+w]
        
        # Resize to standard size
        face_roi = cv2.resize(face_roi, FACE_SIZE)
        
        return face_roi
    
    def validate_face(self, face_roi):
        """
        Validate if the extracted ROI is a good face sample
        
        Args:
            face_roi: Face image ROI
        
        Returns:
            bool: True if valid face
        """
        # Check size
        if face_roi.shape[0] < 50 or face_roi.shape[1] < 50:
            return False
        
        # Check if image is too dark or too bright
        mean_intensity = np.mean(face_roi)
        if mean_intensity < 50 or mean_intensity > 200:
            return False
        
        return True
    
    def detect_largest_face(self, image):
        """
        Detect and return the largest face in image
        
        Args:
            image: Input image
        
        Returns:
            tuple: (x, y, w, h) of largest face or None
        """
        _, faces = self.detect_faces(image, draw_box=False)
        
        if len(faces) == 0:
            return None
        
        # Return the largest face (by area)
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        
        return largest_face