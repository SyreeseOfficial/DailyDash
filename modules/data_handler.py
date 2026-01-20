import json
import os
import shutil
from pathlib import Path
from datetime import datetime, date, timedelta

# User Config Directory
def get_config_dir():
    """Returns the user config directory (e.g. ~/.config/dailydash)"""
    home = Path.home()
    if os.name == 'nt':
        base = home / "AppData" / "Roaming"
    else:
        base = home / ".config"
        
    path = base / "dailydash"
    path.mkdir(parents=True, exist_ok=True)
    return path

CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "daily_history.csv"

# Legacy check (for local development or old installs)
LOCAL_CONFIG = Path("config.json")
if LOCAL_CONFIG.exists() and not CONFIG_FILE.exists():
    try:
        shutil.copy(LOCAL_CONFIG, CONFIG_FILE)
        print(f"Migrated local config to {CONFIG_FILE}")
    except Exception as e:
        print(f"Migration error: {e}")

class DataManager:
    DEFAULT_CONFIG = {
        "user_profile": {
            "city": "",
            "unit_system": "metric",  # Default to metric
            "container_size": 250, # Default 250ml
            "daily_water_goal": 2000,
            "caffeine_size": 50, # Default 50mg
            "day_reset_hour": 0 # Default midnight
        },
        "app_settings": {
            "audio_enabled": True,
            "nag_stand_up": True,
            "nag_eye_strain": True,
            "eod_journal_enabled": False,
            "clipboard_enabled": False,
            "history_logging": True,
            "theme": "default"
        },
        "daily_state": {
            "last_login_date": "",
            "current_water_intake": 0,
            "current_caffeine_intake": 0,
            "tasks": [
                {"id": 1, "text": "", "done": False, "budget": None},
                {"id": 2, "text": "", "done": False, "budget": None},
                {"id": 3, "text": "", "done": False, "budget": None}
            ],
            "habit_status": {}
        },
        "persistent_data": {
            "brain_dump_content": [],
            "parking_lot_links": [],
            "clipboard_history": [],
            "habits": []
        },
        "setup_complete": False
    }

    def __init__(self):
        self.config = self.load_config()

    def get_default_config(self):
        return self.DEFAULT_CONFIG.copy()

    def load_config(self):
        if not CONFIG_FILE.exists():
            return self.get_default_config()
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                
            # MIGRATION: Notes string -> list
            notes = data.get("persistent_data", {}).get("brain_dump_content", "")
            if isinstance(notes, str):
                if notes.strip():
                    lines = [line.strip().lstrip("- ").strip() for line in notes.split('\n') if line.strip()]
                    data["persistent_data"]["brain_dump_content"] = lines
                else:
                    data["persistent_data"]["brain_dump_content"] = []

            # MIGRATION: Ensure Tasks have 'budget'
            tasks = data.get("daily_state", {}).get("tasks", [])
            for t in tasks:
                 if "budget" not in t:
                     t["budget"] = None
                     
            return data
            
        except (json.JSONDecodeError, IOError):
            return self.get_default_config()

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def _get_effective_date(self):
        """Calculates the effective date based on reset hour."""
        reset_hour = self.config.get("user_profile", {}).get("day_reset_hour", 0)
        now = datetime.now()
        if now.hour < reset_hour:
             effective_now = now - timedelta(days=1)
             return effective_now.date().isoformat()
        return now.date().isoformat()

    def is_new_day(self):
        today_str = self._get_effective_date()
        last_login = self.config["daily_state"].get("last_login_date", "")
        return last_login != today_str

    def confirm_new_day(self):
        today_str = self._get_effective_date()
        
        self.config["daily_state"]["last_login_date"] = today_str
        self.config["daily_state"]["current_water_intake"] = 0
        self.config["daily_state"]["current_caffeine_intake"] = 0
        self.config["daily_state"]["tasks"] = [
            {"id": 1, "text": "", "done": False, "budget": None},
            {"id": 2, "text": "", "done": False, "budget": None},
            {"id": 3, "text": "", "done": False, "budget": None}
        ]
        
        current_habits = self.config["persistent_data"].get("habits", [])
        self.config["daily_state"]["habit_status"] = {h: False for h in current_habits}
        
        self.save_config()

    def log_daily_history(self, note=None):
        import csv
        
        today_str = date.today().isoformat()
        daily = self.config.get("daily_state", {})
        water = daily.get("current_water_intake", 0)
        caffeine = daily.get("current_caffeine_intake", 0)
        tasks_done = sum(1 for t in daily.get("tasks", []) if t["done"])
        
        file_exists = HISTORY_FILE.exists()
        
        rows = []
        header = ["Date", "Water_ml", "Caffeine_mg", "Tasks_Completed", "Daily_Note"]
        
        if file_exists:
            try:
                with open(HISTORY_FILE, "r", newline='') as f:
                    reader = csv.DictReader(f)
                    file_fieldnames = reader.fieldnames if reader.fieldnames else header
                    if "Daily_Note" not in file_fieldnames:
                         file_fieldnames.append("Daily_Note")
                    rows = list(reader)
            except IOError:
                pass
        
        updated = False
        for row in rows:
            if row.get("Date") == today_str:
                row["Water_ml"] = water
                row["Caffeine_mg"] = caffeine
                row["Tasks_Completed"] = tasks_done
                if note is not None:
                     row["Daily_Note"] = note
                elif "Daily_Note" not in row:
                     row["Daily_Note"] = ""
                updated = True
                break
        
        if not updated:
            new_row = {
                "Date": today_str,
                "Water_ml": water,
                "Caffeine_mg": caffeine,
                "Tasks_Completed": tasks_done,
                "Daily_Note": note if note else ""
            }
            rows.append(new_row)
            
        try:
            with open(HISTORY_FILE, "w", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writeheader()
                for row in rows:
                    filtered_row = {k: row.get(k, "") for k in header}
                    writer.writerow(filtered_row)
        except IOError as e:
            print(f"Error logging history: {e}")

    def undo_water_intake(self):
        container = self.get("user_profile", {}).get("container_size", 250)
        current = self.get("daily_state").get("current_water_intake", 0)
        
        new_val = max(0, current - container)
        self.config["daily_state"]["current_water_intake"] = new_val
        self.save_config()
        return new_val

    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()

if __name__ == "__main__":
    dm = DataManager()
    print(f"Config loaded from {CONFIG_FILE}")
