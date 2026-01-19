# DailyDash

A terminal-based "Head-Up Display" (HUD) for focus-driven developers.
Combines Task Management (The "Big 3"), Pomodoro Timer, Water Tracking, and Ambient Noise into a single TUI.

## Features
- **Big 3 Tasks**: Focus on your 3 most important daily tasks.
- **Pomodoro Timer**: 25m Focus / 5m Break cycle.
- **Water Tracker**: Track hydration with a single keypress.
- **Ambient Noise**: Built-in Brown Noise generator.
- **Environment**: Local Weather (OpenMeteo) and System Vitals (CPU/RAM).
- **Brain Dump & Parking Lot**: Quick notes and link saving.

## Installation

Requirements: Python 3.10+

1. Clone or download the repository.
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

**DailyDash** is now a pure CLI tool. 

### Quick Start
View your dashboard status:
```bash
python main.py
```

### Setup
If this is your first time, run the setup wizard:
```bash
python main.py setup
```

### Commands

| Command | Action |
| --- | --- |
| `task list` | Show tasks |
| `task add "..."` | Add task |
| `water add` | Log water |
| `timer 25` | Start Focus Timer |
| `noise play` | Play Brown Noise |
| `note add "..."` | add a note | 
| `help` | Show full guide |

See `python main.py help` for details.

## License
MIT
