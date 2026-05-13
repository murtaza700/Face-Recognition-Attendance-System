"""
Database management for attendance records
"""

import pandas as pd
import os
from datetime import datetime
from utils.config import ATTENDANCE_FILE
from utils.helpers import get_current_datetime

class AttendanceDatabase:
    """Attendance database management class"""
    
    def __init__(self, file_path=None):
        self.file_path = file_path or ATTENDANCE_FILE
        self._initialize_file()
    
    def _initialize_file(self):
        """Initialize attendance CSV file if not exists"""
        if not os.path.exists(self.file_path):
            df = pd.DataFrame(columns=['Name', 'Date', 'Time', 'Confidence'])
            df.to_csv(self.file_path, index=False)
    
    def mark_attendance(self, name, confidence=None):
        """
        Mark attendance for a user
        
        Args:
            name: User name
            confidence: Recognition confidence (optional)
        
        Returns:
            tuple: (success, message)
        """
        try:
            # Check if already marked today
            if self.is_already_marked(name):
                return False, f"{name} already marked today"
            
            # Get current date and time
            dt = get_current_datetime()
            
            # Create new entry
            new_entry = pd.DataFrame({
                'Name': [name],
                'Date': [dt['date']],
                'Time': [dt['time']],
                'Confidence': [f"{confidence:.1f}%" if confidence else "N/A"]
            })
            
            # Read existing data
            if os.path.exists(self.file_path):
                df = pd.read_csv(self.file_path)
                df = pd.concat([df, new_entry], ignore_index=True)
            else:
                df = new_entry
            
            # Save to file
            df.to_csv(self.file_path, index=False)
            
            return True, f"Attendance marked for {name} at {dt['time']}"
            
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def is_already_marked(self, name):
        """Check if user already marked attendance today"""
        try:
            if not os.path.exists(self.file_path):
                return False
            
            df = pd.read_csv(self.file_path)
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Check for same name and date
            today_records = df[(df['Name'] == name) & (df['Date'] == today)]
            
            return len(today_records) > 0
            
        except Exception as e:
            print(f"Error checking attendance: {e}")
            return False
    
    def get_today_attendance(self):
        """Get today's attendance records"""
        try:
            if not os.path.exists(self.file_path):
                return []
            
            df = pd.read_csv(self.file_path)
            today = datetime.now().strftime("%Y-%m-%d")
            today_df = df[df['Date'] == today]
            
            return today_df.to_dict('records')
            
        except Exception as e:
            print(f"Error getting today's attendance: {e}")
            return []
    
    def get_today_count(self):
        """Get count of unique attendees today"""
        try:
            if not os.path.exists(self.file_path):
                return 0
            
            df = pd.read_csv(self.file_path)
            today = datetime.now().strftime("%Y-%m-%d")
            today_df = df[df['Date'] == today]
            
            return len(today_df['Name'].unique())
            
        except Exception as e:
            print(f"Error counting attendance: {e}")
            return 0
    
    def get_all_attendance(self):
        """Get all attendance records"""
        try:
            if not os.path.exists(self.file_path):
                return []
            
            df = pd.read_csv(self.file_path)
            # Sort by date and time (newest first)
            df = df.sort_values(['Date', 'Time'], ascending=[False, False])
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"Error getting all attendance: {e}")
            return []
    
    def get_user_attendance(self, name):
        """Get attendance records for specific user"""
        try:
            if not os.path.exists(self.file_path):
                return []
            
            df = pd.read_csv(self.file_path)
            user_df = df[df['Name'] == name]
            
            return user_df.to_dict('records')
            
        except Exception as e:
            print(f"Error getting user attendance: {e}")
            return []
    
    def get_attendance_stats(self):
        """Get attendance statistics"""
        try:
            if not os.path.exists(self.file_path):
                return {}
            
            df = pd.read_csv(self.file_path)
            
            stats = {
                'total_records': len(df),
                'unique_users': len(df['Name'].unique()),
                'today_count': self.get_today_count(),
                'dates': len(df['Date'].unique())
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def export_to_csv(self, output_path=None):
        """Export attendance to a new CSV file"""
        try:
            if not os.path.exists(self.file_path):
                return False, "No attendance data to export"
            
            if output_path is None:
                dt = get_current_datetime()
                output_path = f"attendance_export_{dt['date']}.csv"
            
            df = pd.read_csv(self.file_path)
            df.to_csv(output_path, index=False)
            
            return True, f"Exported to {output_path}"
            
        except Exception as e:
            return False, f"Export error: {str(e)}"