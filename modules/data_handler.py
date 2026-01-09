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
            "daily_water_goal": 2000
        },
        "app_settings": {
            "audio_enabled": True,
            "nag_stand_up": True,
            "nag_eye_strain": True
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
        self.check_new_day()

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

    def check_new_day(self):
        """Checks if today is a new day compared to last_login_date."""
        today_str = date.today().isoformat()
        last_login = self.config["daily_state"].get("last_login_date", "")

        if last_login != today_str:
            # It's a new day! Reset counters
            self.config["daily_state"]["last_login_date"] = today_str
            self.config["daily_state"]["current_water_intake"] = 0
            # Reset tasks? PRD says "Tasks persist only for the current date. They do not roll over"
            self.config["daily_state"]["tasks"] = [
                {"id": 1, "text": "", "done": False},
                {"id": 2, "text": "", "done": False},
                {"id": 3, "text": "", "done": False}
            ]
            self.config["daily_state"]["habit_streak"]["code"] = False
            self.config["daily_state"]["habit_streak"]["no_sugar"] = False
            
            self.save_config()

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
