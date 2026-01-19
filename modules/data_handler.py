import json
import os
from datetime import datetime, date

CONFIG_PATH = "config.json"

class DataManager:
    DEFAULT_CONFIG = {
        "user_profile": {
            "city": "",
            "unit_system": "metric",  # Default to metric
            "container_size": 250, # Default 250ml
            "daily_water_goal": 2000,
            "caffeine_size": 50 # Default 50mg
        },
        "app_settings": {
            "audio_enabled": True,
            "nag_stand_up": True,
            "nag_eye_strain": True,
            "eod_journal_enabled": False,
            "history_logging": True
        },
        "daily_state": {
            "last_login_date": "",
            "current_water_intake": 0,
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
            "habits": []
        },
        "setup_complete": False
    }

    def __init__(self):
        self.config = self.load_config()
        # We don't auto-save setup here anymore to allow UI flow to handle it
        # self.check_new_day()

    def get_default_config(self):
        return self.DEFAULT_CONFIG.copy()

    def load_config(self):
        if not os.path.exists(CONFIG_PATH):
            return self.get_default_config()
        
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                
            # MIGRATION: Notes string -> list
            notes = data.get("persistent_data", {}).get("brain_dump_content", "")
            if isinstance(notes, str):
                if notes.strip():
                    # Split by newlines, clean up bullet points if they exist
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
            with open(CONFIG_PATH, 'w') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def is_new_day(self):
        """Returns True if today is different from last login date."""
        today_str = date.today().isoformat()
        last_login = self.config["daily_state"].get("last_login_date", "")
        return last_login != today_str

    def check_new_day(self):
        """Deprecated: Logic moved to is_new_day + confirm_new_day"""
        pass

    def confirm_new_day(self):
        """Commit the new day reset logic to config."""
        today_str = date.today().isoformat()
        
        self.config["daily_state"]["last_login_date"] = today_str
        self.config["daily_state"]["current_water_intake"] = 0
        self.config["daily_state"]["current_caffeine_intake"] = 0 # Reset Caffeine
        self.config["daily_state"]["tasks"] = [
            {"id": 1, "text": "", "done": False, "budget": None},
            {"id": 2, "text": "", "done": False, "budget": None},
            {"id": 3, "text": "", "done": False, "budget": None}
        ]
        
        # Reset habit statuses for the new day
        current_habits = self.config["persistent_data"].get("habits", [])
        self.config["daily_state"]["habit_status"] = {h: False for h in current_habits}
        
        self.save_config()

    def log_daily_history(self, note=None):
        """Appends or updates daily stats to daily_history.csv"""
        import csv
        
        today_str = date.today().isoformat()
        daily = self.config.get("daily_state", {})
        water = daily.get("current_water_intake", 0)
        caffeine = daily.get("current_caffeine_intake", 0)
        tasks_done = sum(1 for t in daily.get("tasks", []) if t["done"])
        
        log_file = "daily_history.csv"
        file_exists = os.path.exists(log_file)
        
        rows = []
        header = ["Date", "Water_ml", "Caffeine_mg", "Tasks_Completed", "Daily_Note"]
        
        if file_exists:
            try:
                with open(log_file, "r", newline='') as f:
                    reader = csv.DictReader(f)
                    # Use existing fieldnames if available, otherwise default
                    file_fieldnames = reader.fieldnames if reader.fieldnames else header
                    # Ensure Daily_Note is in fieldnames for writing later
                    if "Daily_Note" not in file_fieldnames:
                         file_fieldnames.append("Daily_Note")
                    
                    rows = list(reader)
            except IOError:
                # If read fails, safely assume we overwrite/start fresh or handle error
                # For now, let's just proceed with empty rows if corrupted
                pass
        
        # Check if today's entry exists
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
            
        # Write back
        try:
            with open(log_file, "w", newline='') as f:
                # Use the header we defined to ensure consistent order
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writeheader()
                for row in rows:
                    # Filter row to only include known keys
                    filtered_row = {k: row.get(k, "") for k in header}
                    writer.writerow(filtered_row)
        except IOError as e:
            print(f"Error logging history: {e}")

    def undo_water_intake(self):
        """Undo the last added container of water, min 0."""
        container = self.get("user_profile").get("container_size", 250)
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
    # Simple test
    dm = DataManager()
    print("Config loaded:")
    print(json.dumps(dm.config, indent=2))
    dm.save_config()
    print("Config saved.")
