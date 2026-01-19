import threading
import time
import pyperclip
from rich.console import Console

console = Console()

class ClipboardManager:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.last_text = ""

    def start_monitoring(self):
        """Starts the clipboard monitoring thread if enabled."""
        settings = self.data_manager.get("app_settings", {})
        if not settings.get("clipboard_enabled", False):
            return

        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def stop_monitoring(self):
        """Stops the monitoring thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None

    def _monitor(self):
        """Background loop to check clipboard content."""
        while self.running:
            try:
                # Check setting inside loop in case it changes
                if not self.data_manager.get("app_settings", {}).get("clipboard_enabled", False):
                    time.sleep(2.0)
                    continue

                current_text = pyperclip.paste()
                if current_text and current_text != self.last_text:
                    self.last_text = current_text
                    self.add_entry(current_text)
                
                time.sleep(1.0)
            except Exception as e:
                # Fail gracefully, maybe log debug
                time.sleep(5.0)

    def add_entry(self, text):
        """Adds text to history, maintaining max 10 items."""
        # Simple rudimentary threading safety via lock if needed, 
        # though DataManager isn't thread safe, we rely on the GIL and atomic-ish dict ops 
        # for simple cases. Better to be safe when writing to config.
        
        with self.lock:
             # Reload config to be safe? 
             # For this CLI tool, we assume we are the primary writer during runtime.
             history = self.data_manager.get("persistent_data", {}).get("clipboard_history", [])
             
             # Avoid duplicates at the top
             if history and history[0] == text:
                 return

             # Insert at front
             history.insert(0, text)
             
             # Trim
             if len(history) > 10:
                 history = history[:10]
             
             # Save
             self.data_manager.config["persistent_data"]["clipboard_history"] = history
             self.data_manager.save_config()

    def get_history(self):
        return self.data_manager.get("persistent_data", {}).get("clipboard_history", [])

    def clear_history(self):
        self.data_manager.config["persistent_data"]["clipboard_history"] = []
        self.data_manager.save_config()

    def delete_entry(self, index):
        history = self.get_history()
        if 0 <= index < len(history):
            del history[index]
            self.data_manager.config["persistent_data"]["clipboard_history"] = history
            self.data_manager.save_config()
            return True
        return False

    def copy_to_system(self, index):
        history = self.get_history()
        if 0 <= index < len(history):
            text = history[index]
            pyperclip.copy(text)
            self.last_text = text # avoid re-triggering monitor update immediately
            return True
        return False
