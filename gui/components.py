"""
Reusable GUI components
"""

import customtkinter as ctk
from utils.config import (
    GUI_BG_DARK,
    GUI_BG_MEDIUM,
    GUI_BG_LIGHT,
    GUI_ACCENT_BLUE,
    GUI_ACCENT_GREEN,
    GUI_ACCENT_RED,
    GUI_BUTTON_BG
)

class ModernButton(ctk.CTkButton):
    """Custom modern button with hover effects"""
    
    def __init__(self, parent, text, icon="", color=GUI_BUTTON_BG, 
                 hover_color=GUI_BG_MEDIUM, border_color=None, **kwargs):
        
        super().__init__(
            parent,
            text=f"{icon} {text}" if icon else text,
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color=color,
            hover_color=hover_color,
            corner_radius=15,
            border_width=2 if border_color else 0,
            border_color=border_color if border_color else "transparent",
            **kwargs
        )

class StatusBadge(ctk.CTkLabel):
    """Status indicator badge"""
    
    def __init__(self, parent, text="System Ready", color=GUI_ACCENT_GREEN, **kwargs):
        super().__init__(
            parent,
            text=f"● {text}",
            font=ctk.CTkFont(size=14),
            text_color=color,
            fg_color=GUI_BG_LIGHT,
            corner_radius=10,
            padx=20,
            pady=10,
            **kwargs
        )
    
    def set_status(self, text, color=GUI_ACCENT_GREEN):
        """Update status badge"""
        self.configure(text=f"● {text}", text_color=color)

class InfoCard(ctk.CTkFrame):
    """Information card component"""
    
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, fg_color=GUI_BG_LIGHT, corner_radius=10, **kwargs)
        
        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=GUI_ACCENT_GREEN
            )
            self.title_label.pack(pady=(10,5))
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def add_label(self, text, color="#ffffff", font_size=14):
        """Add a label to the card"""
        label = ctk.CTkLabel(
            self.content_frame,
            text=text,
            font=ctk.CTkFont(size=font_size),
            text_color=color
        )
        label.pack(pady=5)
        return label

class ProgressIndicator(ctk.CTkFrame):
    """Progress bar with label"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=GUI_BG_MEDIUM, **kwargs)
        
        self.label = ctk.CTkLabel(
            self,
            text="Progress: 0%",
            font=ctk.CTkFont(size=14),
            text_color="#ffffff"
        )
        self.label.pack(pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(padx=30, pady=10, fill="x")
        self.progress_bar.set(0)
        
        self.counter_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#a0a0a0"
        )
        self.counter_label.pack(pady=5)
    
    def update(self, current, total, message=""):
        """Update progress"""
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        
        percentage = int(progress * 100)
        self.label.configure(text=f"{message} {percentage}%")
        self.counter_label.configure(text=f"{current}/{total} completed")

class AttendanceList(ctk.CTkFrame):
    """Attendance list display component"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=GUI_BG_MEDIUM, **kwargs)
        
        title = ctk.CTkLabel(
            self,
            text="Today's Attendance List",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=GUI_ACCENT_BLUE
        )
        title.pack(pady=10)
        
        self.text_widget = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(size=14),
            fg_color=GUI_BG_LIGHT
        )
        self.text_widget.pack(fill="both", expand=True, padx=20, pady=20)
    
    def update_list(self, attendance_records):
        """Update attendance list"""
        self.text_widget.delete(1.0, "end")
        
        if not attendance_records:
            self.text_widget.insert("end", "No attendance marked today yet")
            return
        
        self.text_widget.insert("end", "✓ Today's Attendance:\n\n")
        
        # Sort by time
        sorted_records = sorted(attendance_records, key=lambda x: x['Time'])
        
        for record in sorted_records:
            self.text_widget.insert(
                "end",
                f"  • {record['Name']} - {record['Time']}\n"
            )
        
        self.text_widget.insert("end", f"\nTotal: {len(attendance_records)} students")