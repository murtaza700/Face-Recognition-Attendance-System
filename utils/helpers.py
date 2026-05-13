"""
Helper utility functions
"""

import os
import sys
import platform
from datetime import datetime
from pathlib import Path

def get_current_datetime():
    """Get current date and time"""
    now = datetime.now()
    return {
        'date': now.strftime("%Y-%m-%d"),
        'time': now.strftime("%H:%M:%S"),
        'datetime': now.strftime("%Y-%m-%d %H:%M:%S"),
        'day': now.strftime("%A"),
        'month': now.strftime("%B"),
        'year': now.strftime("%Y"),
        'timestamp': now.timestamp()
    }

def format_date_display():
    """Format date for display"""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y")

def validate_name(name):
    """Validate person name"""
    if not name or not name.strip():
        return False, "Name cannot be empty"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    
    if len(name) > 50:
        return False, "Name must be less than 50 characters"
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in name:
            return False, f"Name cannot contain character: {char}"
    
    return True, name

def ensure_directory_exists(directory_path):
    """Ensure directory exists, create if not"""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False

def get_file_count(directory, extensions=None):
    """Count files in directory with optional extension filter"""
    if not os.path.exists(directory):
        return 0
    
    if extensions is None:
        extensions = ['.jpg', '.jpeg', '.png']
    
    count = 0
    for file in os.listdir(directory):
        if any(file.lower().endswith(ext) for ext in extensions):
            count += 1
    
    return count

def play_sound(sound_type='success'):
    """Play system sound"""
    try:
        if platform.system() == 'Windows':
            import winsound
            if sound_type == 'success':
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            elif sound_type == 'error':
                winsound.MessageBeep(winsound.MB_ICONHAND)
            elif sound_type == 'notification':
                winsound.MessageBeep(winsound.MB_OK)
        else:
            # For Linux/Mac
            print('\a')  # System bell
    except Exception as e:
        print(f"Sound error: {e}")
        print('\a')  # Fallback to system bell

def format_confidence(confidence):
    """Format confidence score for display"""
    return f"{100 - confidence:.1f}%"

def get_system_info():
    """Get system information"""
    return {
        'os': platform.system(),
        'python_version': sys.version.split()[0],
        'platform': platform.platform()
    }

def clean_old_files(directory, days=30):
    """Clean files older than specified days"""
    # Optional: For future use
    pass