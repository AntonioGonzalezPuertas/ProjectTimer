# Project Timer

A simple Python application for tracking time spent on projects with a clean GUI interface.

## Requirements

- Python 3.6 or higher
- tkinter (included with most Python installations)

## Installation

1. Make sure you have Python installed on your system
2. No additional packages need to be installed (uses built-in tkinter)

## Usage

### Running the Application

**Standard Mode:**

```bash
python project_timer.py
```

**Development Mode with Auto-Restart:**

For development, you can use auto-restart functionality that automatically restarts the app when you save code changes:

```bash
python auto_restart.py
```

### Using the Timer

1. **Start Timing**: Click the "Start" button to begin tracking time
2. **Stop Timing**: Click the "Stop" button to pause the timer
3. **Reset Timer**: Click "Reset" to clear all accumulated time (requires confirmation)
4. **Automatic Saving**: Your time data is automatically saved when you change project or close the application

### Data Storage

- Timer data is saved in `projects_data.json` in the same directory as the script
- The application automatically loads your previous time when started

## Interface Elements

- **Large Time Display**: Shows current total time in blue
- **Start/Stop Button**: Toggle between starting and stopping the timer
- **Reset Button**: Clears all accumulated time
- **Session Info**: Shows when the current session started (if active)
- **Total Time**: Shows total accumulated time when timer is stopped

## Tips

- Keep the application running in the background while working on your project
- The timer automatically saves your progress when closes
- The small window size allows it to stay visible alongside other applications
