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

Run the dashboard:
```bash
./venv/bin/python main.py
```

### First Run
You will be guided through a setup wizard to configure:
- Measurement Units (Metric/Imperial)
- Water Container Size
- City (for Weather)

### Keybindings

| Key | Action |
| --- | --- |
| **Q** | Quit |
| **W** | Add Water |
| **P** | Start/Pause Timer |
| **R** | Reset Timer |
| **N** | Toggle Brown Noise |

### Configuration
Configuration is stored in `config.json` in the root directory.

## License
MIT
