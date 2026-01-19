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
            "history_logging": True
        },
        "daily_state": {
            "last_login_date": "",
            "current_water_intake": 0,
            "tasks": [
                {"id": 1, "text": "", "done": False},
                {"id": 2, "text": "", "done": False},
                {"id": 3, "text": "", "done": False}
            ],
            "habit_streak": {
                "code": False,
                "no_sugar": False
            }
        },
        "persistent_data": {
            "brain_dump_content": "",
            "parking_lot_links": []
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
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Backup corrupt config ?
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
            {"id": 1, "text": "", "done": False},
            {"id": 2, "text": "", "done": False},
            {"id": 3, "text": "", "done": False}
        ]
        self.config["daily_state"]["habit_streak"]["code"] = False
        self.config["daily_state"]["habit_streak"]["no_sugar"] = False
        
        self.save_config()

    def log_daily_history(self):
        """Appends daily stats to daily_history.csv"""
        today_str = date.today().isoformat()
        daily = self.config.get("daily_state", {})
        water = daily.get("current_water_intake", 0)
        caffeine = daily.get("current_caffeine_intake", 0)
        
        tasks_done = sum(1 for t in daily.get("tasks", []) if t["done"])
        
        log_file = "daily_history.csv"
        # Check if header needed
        need_header = not os.path.exists(log_file)
        
        with open(log_file, "a") as f:
            if need_header:
                f.write("Date,Water_ml,Caffeine_mg,Tasks_Completed\n")
            f.write(f"{today_str},{water},{caffeine},{tasks_done}\n")

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
