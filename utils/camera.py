"""
Camera management module
"""

import cv2
import time
from threading import Lock

class Camera:
    """Camera management class"""
    
    def __init__(self, camera_index=0, width=640, height=480):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None
        self.is_running = False
        self.lock = Lock()
        
    def start(self):
        """Start camera capture"""
        try:
            # Release any existing camera
            if self.cap is not None:
                self.cap.release()
            
            # Try different camera indices
            for index in [self.camera_index, 0, 1]:
                self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # CAP_DSHOW for Windows
                
                if self.cap.isOpened():
                    # Set resolution
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # Warm up camera
                    time.sleep(1.0)  # Increased warm-up time
                    
                    # Test read
                    ret, _ = self.cap.read()
                    if ret:
                        self.is_running = True
                        print(f"Camera opened successfully on index {index}")
                        return True, f"Camera started on index {index}"
                    else:
                        self.cap.release()
            
            return False, "Cannot open any camera. Check if webcam is connected and not used by another app."
            
        except Exception as e:
            return False, f"Camera error: {str(e)}"
    
    def get_frame(self, flip=True):
        """Get a single frame from camera"""
        if not self.is_running or self.cap is None:
            return False, None
        
        try:
            with self.lock:
                if not self.cap.isOpened():
                    self.is_running = False
                    return False, None
                
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    return False, None
                
                if flip:
                    frame = cv2.flip(frame, 1)
                
                return True, frame
                
        except Exception as e:
            print(f"Frame capture error: {e}")
            return False, None
    
    def stop(self):
        """Stop camera and release resources"""
        self.is_running = False
        
        if self.cap is not None:
            try:
                with self.lock:
                    if self.cap.isOpened():
                        self.cap.release()
                    self.cap = None
            except:
                pass
        
        cv2.destroyAllWindows()
    
    def is_opened(self):
        """Check if camera is opened"""
        return self.is_running and self.cap is not None and self.cap.isOpened()
    
    def __del__(self):
        """Destructor to ensure camera is released"""
        self.stop()