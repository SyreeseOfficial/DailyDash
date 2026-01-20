import time
import subprocess
import webbrowser
import threading
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from modules.themes import get_theme

class CommandProcessor:
    def __init__(self, console: Console, data_manager, audio_manager):
        self.console = console
        self.dm = data_manager
        self.am = audio_manager
        
        # Timer state
        self.timer_end_timestamp = None
        self.current_timer_id = None

    def get_theme(self):
        t_name = self.dm.get("app_settings", {}).get("theme", "default")
        return get_theme(t_name)

    # --- WATER ---
    def water_add(self):
        profile = self.dm.get("user_profile", {})
        container = profile.get("container_size", 250)
        unit = profile.get("unit_system", "metric")
        unit_str = "ml" if unit == "metric" else "oz"
        
        daily = self.dm.get("daily_state")
        current = daily.get("current_water_intake", 0)
        
        new_val = current + container
        daily["current_water_intake"] = new_val
        self.dm.save_config()
        
        T = self.get_theme()
        self.console.print(f"[{T['secondary']}]Glug glug![/] Added {container}{unit_str}. Total: {new_val}{unit_str}")

    def water_undo(self):
        new_val = self.dm.undo_water_intake()
        T = self.get_theme()
        self.console.print(f"[{T['warning']}]Undid last water.[/] Total: {new_val}")

    def coffee_add(self):
        profile = self.dm.get("user_profile", {})
        size = profile.get("caffeine_size", 50)
        
        daily = self.dm.get("daily_state")
        current = daily.get("current_caffeine_intake", 0)
        
        new_val = current + size
        daily["current_caffeine_intake"] = new_val
        self.dm.save_config()
        
        T = self.get_theme()
        self.console.print(f"[{T['accent']}]Coffee time![/] Added {size}mg. Total: {new_val}mg")

    # --- TASKS ---
    def task_add(self):
        T = self.get_theme()
        daily = self.dm.get("daily_state", {})
        tasks = daily.get("tasks", [])
        
        # Find empty slot
        slot = next((t for t in tasks if not t["text"]), None)
        if not slot:
            self.console.print(f"[{T['warning']}]All 3 slots full. Finish or delete one first.[/]")
            return

        text = Prompt.ask("Task Description")
        budget = Prompt.ask("Time Budget (e.g. 30m) [Optional]", default="")
        
        slot["text"] = text
        slot["done"] = False
        slot["budget"] = budget if budget else None
        
        self.dm.save_config()
        self.console.print(f"[{T['success']}]Task added![/]")

    def task_toggle(self):
        T = self.get_theme()
        daily = self.dm.get("daily_state", {})
        tasks = daily.get("tasks", [])
        
        # Simple menu to toggle
        # Filter non-empty
        active_tasks = [t for t in tasks if t["text"]]
        if not active_tasks:
            self.console.print(f"[{T['dim']}]No active tasks.[/]")
            return

        self.console.print(f"[{T['primary']}]Select task to toggle:[/]")
        for t in active_tasks:
            status = "[green]DONE[/green]" if t["done"] else "[red]TODO[/red]"
            self.console.print(f" {t['id']}. {status} {t['text']}")
            
        choice = IntPrompt.ask("Task ID", choices=[str(t['id']) for t in active_tasks], show_choices=False)
        
        for t in tasks:
            if t['id'] == choice:
                t['done'] = not t['done']
                state = "DONE" if t['done'] else "TODO"
                self.console.print(f"[{T['success']}]Task {choice} marked as {state}[/]")
                self.dm.save_config()
                return

    def task_delete(self):
        T = self.get_theme()
        daily = self.dm.get("daily_state", {})
        tasks = daily.get("tasks", [])
        
        # Filter non-empty
        active_tasks = [t for t in tasks if t["text"]]
        if not active_tasks:
            self.console.print(f"[{T['dim']}]No tasks to delete.[/]")
            return
            
        choice = IntPrompt.ask("Delete Task ID", choices=[str(t['id']) for t in active_tasks], show_choices=False)
        
        for t in tasks:
            if t['id'] == choice:
                t['text'] = ""
                t["done"] = False
                t["budget"] = None
                self.console.print(f"[{T['warning']}]Task {choice} cleared.[/]")
                self.dm.save_config()
                return

    # --- TIMER ---
    def timer_start(self):
        T = self.get_theme()
        
        if self.timer_end_timestamp and self.timer_end_timestamp > time.time():
             remaining = int((self.timer_end_timestamp - time.time()) / 60)
             if not Confirm.ask(f"Timer running ({remaining}m). Restart?", default=False):
                 return

        mins = IntPrompt.ask("Duration (min)", default=25)
        self.timer_end_timestamp = time.time() + mins * 60
        
        # Timer thread
        self.current_timer_id = time.time()
        threading.Thread(target=self._timer_worker, args=(self.current_timer_id, mins), daemon=True).start()
        
        self.console.print(f"[{T['success']}]Timer set for {mins} minutes.[/]")

    def _timer_worker(self, timer_id, mins):
        time.sleep(mins * 60)
        if self.current_timer_id == timer_id:
            self.am.play_chime()
            # Try notify
            try:
                subprocess.Popen(['notify-send', 'DailyDash', 'Time is up!'])
            except: pass

    def get_timer_status(self):
        if self.timer_end_timestamp and self.timer_end_timestamp > time.time():
            remaining_sec = int(self.timer_end_timestamp - time.time())
            m, s = divmod(remaining_sec, 60)
            return f"{m:02}:{s:02}"
        return "IDLE"

    # --- BRAIN DUMP ---
    def note_add(self):
        T = self.get_theme()
        note = Prompt.ask("Enter note")
        if note:
            notes = self.dm.get("persistent_data", {}).get("brain_dump_content", [])
            notes.append(note)
            self.dm.config["persistent_data"]["brain_dump_content"] = notes
            self.dm.save_config()
            self.console.print(f"[{T['success']}]Note added.[/]")

    def note_manage(self):
        T = self.get_theme()
        notes = self.dm.get("persistent_data", {}).get("brain_dump_content", [])
        if not notes:
             self.console.print(f"[{T['dim']}]No notes.[/]")
             return
             
        self.console.print(f"[{T['primary']}]Recent Notes:[/]")
        for i, n in enumerate(notes):
            self.console.print(f"{i+1}. {n}")
            
        action = Prompt.ask("[d]elete, [c]lear all, [b]ack", choices=["d", "c", "b"], default="b")
        
        if action == "c":
            if Confirm.ask("Clear ALL notes?"):
                self.dm.config["persistent_data"]["brain_dump_content"] = []
                self.dm.save_config()
                self.console.print("Cleared.")
        elif action == "d":
            idx = IntPrompt.ask("Delete ID", default=0)
            if 1 <= idx <= len(notes):
                notes.pop(idx-1)
                self.dm.config["persistent_data"]["brain_dump_content"] = notes
                self.dm.save_config()
                self.console.print("Deleted.")

    # --- PARKING LOT ---
    def link_add(self):
        T = self.get_theme()
        url = Prompt.ask("URL")
        links = self.dm.get("persistent_data", {}).get("parking_lot_links", [])
        links.append(url)
        self.dm.config["persistent_data"]["parking_lot_links"] = links
        self.dm.save_config()
        self.console.print(f"[{T['success']}]Saved.[/]")

    def link_open(self):
        T = self.get_theme()
        links = self.dm.get("persistent_data", {}).get("parking_lot_links", [])
        if not links:
            self.console.print("No links.")
            return
            
        for i, l in enumerate(links):
            self.console.print(f"{i+1}. {l}")
            
        choice = IntPrompt.ask("Open ID (0 to cancel)", default=0)
        if 1 <= choice <= len(links):
            webbrowser.open(links[choice-1])
            self.console.print("Opening...")

    # --- HABITS ---
    def toggle_habit(self):
        T = self.get_theme()
        habits = self.dm.get("persistent_data", {}).get("habits", [])
        status = self.dm.get("daily_state", {}).get("habit_status", {})
        
        if not habits:
            self.console.print("No habits configured.")
            return
            
        self.console.print(f"[{T['primary']}]Toggle Habit:[/]")
        for i, h in enumerate(habits):
            s = "[green]YES[/]" if status.get(h) else "[red]NO[/]"
            self.console.print(f"{i+1}. {s} {h}")
            
        choice = IntPrompt.ask("ID", default=0)
        if 1 <= choice <= len(habits):
            h_name = habits[choice-1]
            status[h_name] = not status.get(h_name, False)
            self.dm.save_config()
            self.console.print(f"[{T['success']}]Updated habit.[/]")

    def setup_habits(self):
        T = self.get_theme()
        habits = []
        self.console.print(f"[{T['primary']}]Configure Habits (Max 5)[/]")
        while len(habits) < 5:
            h = Prompt.ask(f"Habit #{len(habits)+1} Name (Enter to finish)")
            if not h: break
            habits.append(h)
            
        self.dm.config["persistent_data"]["habits"] = habits
        # Reset status
        self.dm.config["daily_state"]["habit_status"] = {h: False for h in habits}
        self.dm.save_config()

    # --- NOISE ---
    def noise_toggle(self):
        playing = self.am.toggle_brown_noise()
        T = self.get_theme()
        if playing:
            self.console.print(f"[{T['accent']}]Noise ON 🔈[/]")
        else:
            self.console.print(f"[{T['dim']}]Noise OFF 🔇[/]")

    # --- SETUP ---
    def run_setup_wizard(self):
        T = self.get_theme()
        self.console.print(f"[bold {T['primary']}]Welcome to DailyDash Setup[/]")
        
        name = Prompt.ask("Your Name", default="User")
        city = Prompt.ask("City for Weather", default="New York")
        is_metric = Confirm.ask("Use Metric? (ml/C)", default=True)
        
        container = IntPrompt.ask("Water Container Size", default=250 if is_metric else 8)
        goal = IntPrompt.ask("Daily Water Goal", default=2000 if is_metric else 64)
        
        self.dm.config["user_profile"] = {
            "name": name,
            "city": city,
            "unit_system": "metric" if is_metric else "imperial",
            "container_size": container,
            "daily_water_goal": goal,
            "caffeine_size": 50,
            "day_reset_hour": 0
        }
        
        # Habits
        if Confirm.ask("Setup Habits now?", default=True):
            self.setup_habits()
            
        self.dm.config["setup_complete"] = True
        self.dm.save_config()
        self.console.print(f"[{T['success']}]Setup Complete![/]")


