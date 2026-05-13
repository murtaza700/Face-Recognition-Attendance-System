"""
Core modules package
"""

from core.face_detector import FaceDetector
from core.face_recognizer import FaceRecognizer
from core.trainer import ModelTrainer

__all__ = [
    'FaceDetector',
    'FaceRecognizer',
    'ModelTrainer',
]