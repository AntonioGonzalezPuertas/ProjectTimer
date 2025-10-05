#!/usr/bin/env python3
"""
Project Timer - A simple time tracking application
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
import os
import logging
from datetime import datetime
from enum import Enum
import helpers

# Data file for persistence
DATA_FILE = "projects_data.json"

class TimerStatus(Enum):
    """Enum for timer status states"""
    STOPPED = "stopped"
    PAUSED = "paused"
    RUNNING = "running"
    
# Setup logging for debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('projects_sessions.log'),
        logging.StreamHandler()  # This will still try to show in console
    ]
)
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('errors.log'),
        logging.StreamHandler()  # This will still try to show in console
    ]
)



class ProjectTimer:
    def __init__(self, root):

        logging.info(f"----------------- Project Timer Launched ----------------")
        self.root = root
        self.root.title("Project Timer")
        self.root.geometry("540x90")
        self.root.resizable(False, True)
        
        # Position window with screen detection
        root.update_idletasks()
        
        # Detect and set screen configuration
        self.set_screen()
        
        # Timer variables
        self.status = TimerStatus.STOPPED
        self.session_time = 0
        
        # Project-related variables
        self.current_project = None
        self.current_project_hours = 0
        self.projects_data = {}  # {project_name: elapsed_time}
        
        # Load previous data
        self.load_data()
        
        # Setup GUI
        self.setup_gui()

        
        # Save data when closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def project_log(self):
        """Log project message to both file and console (if available)"""
        
        try:
            message = f"{self.current_project}: {self.status}, Session: {round(self.session_time/3600,1)}h "
            if self.current_project != "CountDown":
                message = message + f"Total: {round(self.current_project_hours + self.session_time / 3600, 1)}h"

            logging.info(message)  # Try to print to console
        except:
            pass  # Ignore if console not available
    
    def error_log(self, message):
        """Log error message to both file and console (if available)"""
        
        try:
            logging.error(message)  # Try to print to console
        except:
            pass  # Ignore if console not available
    
    def set_screen(self):
        """Detect screen configuration and return screen information"""
        try:
            # Get primary screen dimensions
            primary_width = self.root.winfo_screenwidth()
            primary_height = self.root.winfo_screenheight()
            
            # Try to detect virtual screen dimensions (includes all monitors)
            # This is a simple detection method using tkinter
            screen_info = {
                'screen_count': 1,
                'primary_width': primary_width,
                'primary_height': primary_height,
                'secondary_left': False,
                'total_width': primary_width,
                'detection_method': 'tkinter_basic'
            }
            
            # Try to get more detailed screen info using Windows-specific method
            try:
                import subprocess
                import re
                
                # Use wmic to get monitor information (Windows only)
                result = subprocess.run(['wmic', 'desktopmonitor', 'get', 'screenwidth,screenheight'], 
                                        capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    screen_resolutions = []
                    for line in lines[1:]:  # Skip header
                        if line.strip():
                            parts = line.strip().split()
                            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                                screen_resolutions.append((int(parts[1]), int(parts[0])))  # width, height
                    
                    if len(screen_resolutions) > 1:
                        screen_info['screen_count'] = len(screen_resolutions)
                        screen_info['detection_method'] = 'wmic'
                        
                        # Try to determine if secondary is on left by testing window positioning
                        test_window = tk.Toplevel(root)
                        test_window.withdraw()
                        test_window.geometry("1x1+-100+0")
                        test_window.update()
                        
                        # If we can position at negative coordinates, secondary is likely on left
                        try:
                            test_x = test_window.winfo_x()
                            if test_x < 0:
                                screen_info['secondary_left'] = True
                        except:
                            pass
                        
                        test_window.destroy()
                        
            except Exception as e:
                print(f"Advanced screen detection failed: {e}")
            
            # Alternative method: Test positioning at negative coordinates
            if screen_info['screen_count'] == 1:
                try:
                    test_window = tk.Toplevel(self.root)
                    test_window.withdraw()
                    test_window.geometry("1x1+-10+0")
                    test_window.update_idletasks()
                    
                    # If this works, there might be a screen to the left
                    actual_x = test_window.winfo_x()
                    if actual_x < 0:
                        screen_info['screen_count'] = 2
                        screen_info['secondary_left'] = True
                        screen_info['detection_method'] = 'negative_coordinate_test'
                    
                    test_window.destroy()
                except Exception as e:
                    print(f"Negative coordinate test failed: {e}")
            
            if screen_info['screen_count'] == 1:
                x = 20
                y = 50
            else:
                # Multiple screens detected
                if screen_info['secondary_left']:
                    x = -screen_info['primary_width'] + 20
                    y = 50
                else:
                    x = screen_info['primary_width'] + 20
                    y = 50
            
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            
        except Exception as e:
            print(f"Screen detection error: {e}")
            return {
                'screen_count': 1,
                'primary_width': 1920,  # Default fallback
                'primary_height': 1080,
                'secondary_left': False,
                'detection_method': 'fallback'
            }
        
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Project selection frame
        selection_frame = ttk.Frame(main_frame)
        selection_frame.grid(row=0, column=0, pady=(0, 15), sticky=(tk.W, tk.E))
        
        ttk.Label(selection_frame, text="Project:").grid(row=0, column=0, sticky=( tk.W))
        
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(selection_frame, textvariable=self.project_var, 
                                         width=20, state="normal")
        self.project_combo.grid(row=1, column=0, columnspan=2,padx=(0, 5))
        self.project_combo.bind('<Return>', self.add_new_project)
        self.project_combo.bind('<<ComboboxSelected>>', self.on_project_selected)

        add_btn = ttk.Button(selection_frame, text="+", width=2,
                            command=self.add_current_project)
        add_btn.grid(row=0, column=1, sticky=(tk.E), pady=(0, 2), padx=(0,5))
        
        # Session time display
        session_frame = ttk.Frame(main_frame)
        session_frame.grid(row=0, column=2,  pady=(0, 10), padx=(20, 0), sticky=(tk.W))
        ttk.Label(session_frame, text="Session:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W)
        
        
        style = ttk.Style()
        try:
            style.theme_use('clam')  # or try 'alt', 'default', 'classic'
        except:
            pass
        style.configure("BigButton.TButton", 
                        font=("Arial", 16, "bold"), 
                        focuscolor="none", 
                        foreground="lightblue", 
                        background="darkblue")

        
        style.configure("RedButton.TButton", 
                       foreground="darkred",
                       font=("Arial", 16, "bold"))
        
        style.configure("GreenButton.TButton", 
                       foreground="darkgreen",
                       font=("Arial", 16, "bold"))
        
        self.run_btn = ttk.Button(session_frame, text="00h 00m 00", 
                            command=self.toggle_timer,
                            style="RedButton.TButton",
                            width=12)
        self.run_btn.grid(row=0, column=1, columnspan=3, pady=(0, 3))
        
        self.run_btn_plus = ttk.Button(session_frame, text="+", width=6,
                            command=lambda: self.inc_session_time(+60))
        self.run_btn_plus.grid(row=1, column=1,sticky=(tk.E))
        self.run_btn_moins = ttk.Button(session_frame, text="-", width=6,
                            command=lambda: self.inc_session_time(-60))
        self.run_btn_moins.grid(row=1, column=2, sticky=(tk.E))
        self.run_btn_reset = ttk.Button(session_frame, text="0",width=6,
                            command=lambda: self.inc_session_time(0))
        self.run_btn_reset.grid(row=1, column=3, sticky=(tk.E))
        
        # Global time display
        self.global_frame = ttk.Frame(main_frame)
        self.global_frame.grid(row=0, column=5, columnspan=2, pady=(0, 10))
        
        ttk.Label(self.global_frame, text="Total (h):", font=("Arial", 10)).grid(row=0, column=0, padx=(20, 5))
        self.total_label = ttk.Label(self.global_frame, text=self.current_project_hours, 
                 font=("Arial", 18, "bold"), foreground="darkblue", width=6)
        self.total_label.grid(row=0, column=1)
        
        # Alarm time image
        self.image_frame = ttk.Frame(main_frame)
        self.image_frame.grid(row=0, column=5, pady=(0, 10))
        self.bell_icon = tk.PhotoImage(file="bell.png")
        self.bell_icon = self.bell_icon.subsample(8, 8)  # Make half size

        image_label = ttk.Label(self.image_frame, image=self.bell_icon)
        image_label.grid(row=0, column=0, sticky=tk.W, padx=(35, 35))
        
        self.image_frame.grid_remove()  # Hide initially

        # Load project list
        self.update_project_list()
        
        # Status info
        self.update_status_info()
    
    def inc_session_time(self, delta):
        if self.status != TimerStatus.PAUSED:
            self.pause_timer()
        if delta == 0:
            self.session_time = 0
        else:
            self.session_time = self.session_time + (delta)
            if self.session_time < 0 :
                self.session_time = 0
                
        self.update_display()
    
    def add_new_project(self, event=None):
        """Add a new project from combobox input"""
        project_name = self.project_var.get().strip()
        if project_name and project_name not in self.projects_data:
            self.projects_data[project_name] = {}
            self.current_project = project_name
            self.save_data()
            self.update_project_list()
            self.project_combo.set(project_name)
            self.current_project_hours = 0
            self.total_label.config(text="0")
    
    def add_current_project(self):
        """Add the current project from combobox"""
        self.add_new_project()
    
    def on_project_selected(self, event=None):
        """Handle project selection"""
        selected = self.project_var.get()
        
        if self.session_time > 0 and self.current_project:
            self.save_data()
            
        if selected == "CountDown":
            self.current_project = "CountDown"
            self.current_project_hours = 0
            self.session_time = 3600  # Reset session time when switching projects
            self.run_btn.config(text="01h 00m 00")
            self.total_label.config(text="")
            self.global_frame.grid_remove()
            self.image_frame.grid()
                
        elif selected in self.projects_data:
            self.current_project = selected
            self.current_project_hours = self.get_project_total_time(self.current_project)
            self.total_label.config(text=round(self.current_project_hours,1))
            self.session_time = 0  # Reset session time when switching projects
            self.run_btn.config(text="00h 00m 00")
            self.global_frame.grid()
            self.image_frame.grid_remove()
        else:
            return 0
        

    
    def update_project_list(self):
        """Update the project combobox with available projects"""
        projects = ["CountDown"] + list(self.projects_data.keys())
        self.project_combo['values'] = projects
        if projects and not self.current_project:
            self.current_project = projects[0]
        
        self.project_var.set(self.current_project)

    
    def toggle_timer(self):
        # if not self.current_project:
        #     messagebox.showwarning("No Project Selected", 
        #                          "Please select or create a project first.")
        #     return
       
        if self.status == TimerStatus.RUNNING:
            self.pause_timer()
        else:
            self.resume_timer()

        self.project_log()
            
     

        
    def resume_timer(self):
        """Resume the timer"""
        print("Resuming timer...")
        self.status = TimerStatus.RUNNING
        self.run_btn.config(style="GreenButton.TButton")
        self.update_display()  # Restart the display update loop
        self.update_status_info()
    
    def pause_timer(self):
        """Pause the timer"""
        print("Pausing timer...")
        
        self.status = TimerStatus.PAUSED
        self.run_btn.config(style="RedButton.TButton")
        self.update_status_info()
    
    def get_project_total_time(self, project_name=None):
        """Get the total time for current project including active session"""
        if not self.current_project:
            return 0
        
        most_recent_project_hours = 0
        for date, hours in self.projects_data[project_name].items():
            most_recent_project_hours += hours
       
        return round(most_recent_project_hours, 1)

    def get_most_recent_project(self):
        """Get the project with the most recent access date
        
        Returns:
            str: Project name with most recent access, or None if no projects
        """
        if not self.projects_data:
            return None
        
        most_recent_project = None
        most_recent_date = None
        print(self.projects_data)
        for project_name, project_info in self.projects_data.items():
            for date in project_info:
                #print(f"Project: {project_name}, Info: {date} {project_info[date]}")
                if not most_recent_date or date > most_recent_date:
                    most_recent_date = date
                    most_recent_project = project_name

        # Fallback to first project if no dates found
        if most_recent_project is None and self.projects_data:
            most_recent_project = list(self.projects_data.keys())[1]

        return most_recent_project
    
    def update_display(self):
        """Update the time display"""
        
        if self.status != TimerStatus.PAUSED:
            if self.current_project == "CountDown":
                self.session_time -= 1
            else:
                self.session_time += 1

        if self.session_time < 0:
            self.session_time = 0
            self.pause_timer()
            self.alarm()
            
        # Update session time display in HH:MM:SS format
        hours, minutes, seconds = helpers.convert_seconds_to_hms(self.session_time)
        self.run_btn.config(text=f"{hours:02d}h {minutes:02d}m {seconds:02d}")
        
        # Update global time for current project
        total_time = round(self.current_project_hours + self.session_time / 3600, 1)
        self.total_label.config(text=round(total_time,1))
        
        # Schedule next update
        if self.status == TimerStatus.RUNNING:
            self.root.after(1000, self.update_display)
            #print(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def update_status_info(self):
        """Update status information"""
        if self.current_project:
            if self.status == TimerStatus.RUNNING:
                # Get session time components
                hours, minutes, seconds = helpers.convert_seconds_to_hms(self.session_time)
                status_text = f"Working on '{self.current_project}' - Session"
            elif self.status == TimerStatus.PAUSED:
                hours, minutes, seconds = helpers.convert_seconds_to_hms(self.session_time)
                status_text = f"Working on '{self.current_project}' - Session (paused)"
            else:
                status_text = f"Working on '{self.current_project}' (stopped)"
        else:
            status_text = "No project selected"
        self.root.title(status_text)

    def alarm(self):
        """Trigger an alarm when countdown reaches zero"""
        try:
            self.root.bell()  # Sound the system bell
            for i in range(6):
                self.root.title("⚠️ TIME'S UP! ⚠️" if i % 2 == 0 else original_title)
                self.root.update()
                time.sleep(0.5)
            self.root.title(original_title)  
        except:
            pass  # Ignore if bell not available
        messagebox.showinfo("Time's up!", "Countdown has reached zero.") 
        # Flash the window to get attention
        original_title = self.root.title()
         
        
    def save_data(self):
        """Save timer data to file"""

        print(self.projects_data, self.current_project)
        if self.current_project != "CountDown":
            self.projects_data[self.current_project][datetime.now().isoformat(timespec='seconds')] = round(self.session_time / 3600, 1)

            try:
                with open(DATA_FILE, 'w') as f:
                    json.dump(self.projects_data, f, indent=2)
            except Exception as e:
                print(f"Error saving data: {e}")
    
    def load_data(self):
        """Load timer data from file"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.projects_data = json.load(f)
                    
                    self.current_project = self.get_most_recent_project()
                    self.current_project_hours = self.get_project_total_time(self.current_project) if self.current_project else 0
                    print(f"Most recent project: {self.current_project}, Hours: {self.current_project_hours}")
                    
            except Exception as e:
                print(f"Error loading data: {e}")
                self.projects_data = {}
                self.current_project = None
        else:
            self.projects_data = {}
            self.current_project = None
    
    def on_closing(self):
        """Handle application closing"""
        if self.status == TimerStatus.RUNNING:
            self.pause_timer()
        self.save_data()
        self.project_log()
        self.root.destroy()
        logging.info(f"------------------------- Closed ------------------------")



def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = ProjectTimer(root)
    
    root.mainloop()


if __name__ == "__main__":
    main()