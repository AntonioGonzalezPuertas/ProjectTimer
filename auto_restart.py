#!/usr/bin/env python3
"""
Auto-restart script for Project Timer
Watches for file changes and automatically restarts the application
"""

import os
import sys
import time
import subprocess
from pathlib import Path
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AppRestartHandler(FileSystemEventHandler):
    def __init__(self, script_path):
        self.script_path = script_path
        self.process = None
        self.restart_timer = None
        self.start_app()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Only restart for Python files
        if event.src_path.endswith('.py'):
            print(f"File changed: {event.src_path}")
            self.restart_app()
    
    def start_app(self):
        """Start the application"""
        if self.process:
            self.process.terminate()
            self.process.wait()
        
        print(f"Starting {self.script_path}...")
        self.process = subprocess.Popen([sys.executable, self.script_path])
    
    def restart_app(self):
        """Restart the application with a small delay to avoid multiple restarts"""
        if self.restart_timer:
            self.restart_timer.cancel()
        
        self.restart_timer = threading.Timer(0.5, self.start_app)
        self.restart_timer.start()
    
    def stop(self):
        """Stop the application"""
        if self.restart_timer:
            self.restart_timer.cancel()
        if self.process:
            self.process.terminate()
            self.process.wait()

def main():
    script_path = Path(__file__).parent / "project_timer.py"
    
    if not script_path.exists():
        print(f"Error: {script_path} not found!")
        return
    
    print("Project Timer Auto-Restart")
    print("=" * 30)
    print(f"Watching: {script_path}")
    print("Press Ctrl+C to stop")
    print()
    
    # Create event handler and observer
    event_handler = AppRestartHandler(str(script_path))
    observer = Observer()
    observer.schedule(event_handler, str(script_path.parent), recursive=False)
    
    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping auto-restart...")
        observer.stop()
        event_handler.stop()
    
    observer.join()

if __name__ == "__main__":
    main()