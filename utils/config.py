"""
Configuration settings for Face Recognition System
"""

import os
import cv2 
from pathlib import Path

# ============ SYSTEM PATHS ============
BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "data" / "dataset" / "images"
MODEL_FILE = BASE_DIR / "data" / "trainer.yml"
LABELS_FILE = BASE_DIR / "data" / "labels.pkl"
ATTENDANCE_FILE = BASE_DIR / "data" / "attendance.csv"
TRAINING_REPORT = BASE_DIR / "data" / "training_report.txt"
CASCADE_FILE = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

# ============ CAMERA SETTINGS ============
CAMERA_INDEX = 0  # 0 for built-in, 1 for external
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FACE_SIZE = (200, 200)  # Size for saved face images

# ============ FACE DETECTION ============
HAAR_SCALE_FACTOR = 1.3
HAAR_MIN_NEIGHBORS = 5

# ============ FACE RECOGNITION ============
CONFIDENCE_THRESHOLD = 70  # Lower = more strict
REGISTRATION_IMAGES_COUNT = 20

# ============ SOUND SETTINGS ============
SOUND_ENABLED = True
SOUND_SUCCESS_FILE = BASE_DIR / "assets" / "sounds" / "success.wav"
SOUND_ERROR_FILE = BASE_DIR / "assets" / "sounds" / "error.wav"

# ============ COLORS (BGR Format for OpenCV) ============
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_BLUE = (255, 0, 0)
COLOR_YELLOW = (0, 255, 255)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# ============ GUI COLORS (Hex Format) ============
GUI_BG_DARK = "#1a1a2e"
GUI_BG_MEDIUM = "#16213e"
GUI_BG_LIGHT = "#0a1628"
GUI_ACCENT_BLUE = "#00d2ff"
GUI_ACCENT_GREEN = "#00ff88"
GUI_ACCENT_ORANGE = "#ffa500"
GUI_ACCENT_RED = "#ff6b6b"
GUI_BUTTON_BG = "#0f3460"

# ============ ATTENDANCE SETTINGS ============
ATTENDANCE_DUPLICATE_CHECK = True  # Same day duplicate prevention
ATTENDANCE_SHOW_CONFIDENCE = True

# ============ LOGGING ============
LOG_ENABLED = True
LOG_FILE = BASE_DIR / "data" / "system.log"

# Create necessary directories
def initialize_directories():
    """Create all necessary directories"""
    directories = [
        DATASET_DIR,
        BASE_DIR / "data",
        BASE_DIR / "assets" / "sounds",
        BASE_DIR / "assets" / "icons",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)