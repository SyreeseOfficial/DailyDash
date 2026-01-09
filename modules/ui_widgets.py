from textual.app import ComposeResult
from textual.widgets import Static, Input, Checkbox, ProgressBar, Label
from textual.containers import Horizontal

class TaskListWidget(Static):
    """Container for the Big 3 Tasks."""
    def compose(self) -> ComposeResult:
        yield Label("Big 3 Tasks", classes="section-header")
        
        # We need to access the app's data manager to get tasks
        # Note: self.app might not be fully available during compose if not mounted? 
        # Usually it is. But to be safe, we might defer data loading or handle empty states.
        
        tasks = self.app.data_manager.get("daily_state").get("tasks", [])
        
        for i, task in enumerate(tasks):
            # i is 0-indexed, tasks usually 1-indexed in ID
            yield Horizontal(
                Checkbox(value=task["done"], id=f"task-check-{i}"),
                Input(value=task["text"], placeholder=f"Task {i+1}...", id=f"task-input-{i}"),
                classes="task-row"
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        # Update data when input changes
        if event.input.id and event.input.id.startswith("task-input-"):
            idx = int(event.input.id.split("-")[-1])
            tasks = self.app.data_manager.get("daily_state")["tasks"]
            if 0 <= idx < len(tasks):
                tasks[idx]["text"] = event.value
                self.app.data_manager.save_config()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id and event.checkbox.id.startswith("task-check-"):
            idx = int(event.checkbox.id.split("-")[-1])
            tasks = self.app.data_manager.get("daily_state")["tasks"]
            if 0 <= idx < len(tasks):
                tasks[idx]["done"] = event.value
                self.app.data_manager.save_config()
                
                # Visual strikethrough logic could be handled by updating the Input's class
                inp = self.query_one(f"#task-input-{idx}", Input)
                if event.value:
                    inp.add_class("completed-task")
                else:
                    inp.remove_class("completed-task")

class TimerWidget(Static):
    """Pomodoro Timer."""
    # 5 min increments to 60
    DURATIONS = [m * 60 for m in range(5, 65, 5)] 
    DEFAULT_IDX = 4 # 25 mins (Index 4: 5,10,15,20,25)
    
    def compose(self) -> ComposeResult:
        yield Label("Pomodoro", classes="section-header")
        yield Label("25:00", id="timer-display")
        yield ProgressBar(total=self.DURATIONS[0], show_eta=False, id="timer-progress")
        yield Label("Stopped", id="timer-status")
        yield Label("P: Start/Pause | R: Reset | D: Duration", classes="help-text")

    def on_mount(self) -> None:
        self.duration_idx = self.DEFAULT_IDX
        self.current_duration = self.DURATIONS[self.duration_idx]
        self.time_left = self.current_duration
        self.running = False
        
        self.query_one("#timer-progress", ProgressBar).total = self.current_duration
        self.query_one("#timer-progress", ProgressBar).progress = 0
        
        self.set_interval(1, self.tick)

    def tick(self) -> None:
        if self.running and self.time_left > 0:
            self.time_left -= 1
            self.update_display()
            
            # Update progress (inverse - how much time elapsed)
            elapsed = self.current_duration - self.time_left
            self.query_one("#timer-progress", ProgressBar).progress = elapsed
            
            if self.time_left == 0:
                 self.running = False
                 self.query_one("#timer-status", Label).update("TIME UP!")
                 self.styles.background = "red" 
                 # Terminal Bell
                 print('\a', end='', flush=True)
    
    def update_display(self) -> None:
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.query_one("#timer-display", Label).update(f"{minutes:02d}:{seconds:02d}")
    
    def toggle_timer(self):
        self.running = not self.running
        status = "Running" if self.running else "Paused"
        self.query_one("#timer-status", Label).update(status)
        self.styles.background = None # Reset alert color if any

    def reset_timer(self):
        self.running = False
        self.time_left = self.current_duration
        self.update_display()
        self.query_one("#timer-status", Label).update("Stopped")
        self.styles.background = None
        self.query_one("#timer-progress", ProgressBar).progress = 0

    def cycle_duration(self):
        if self.running:
            return # Don't change while running to avoid logic mess
            
        self.duration_idx = (self.duration_idx + 1) % len(self.DURATIONS)
        self.current_duration = self.DURATIONS[self.duration_idx]
        self.time_left = self.current_duration
        
        self.query_one("#timer-progress", ProgressBar).total = self.current_duration
        self.query_one("#timer-progress", ProgressBar).progress = 0
        self.update_display()
        
        self.app.notify(f"Timer set to {self.current_duration//60} mins")

from textual.widgets import TextArea, ListView, ListItem

class BrainDumpWidget(Static):
    """Notes area."""
    def compose(self) -> ComposeResult:
        yield Label("Brain Dump", classes="section-header")
        content = self.app.data_manager.get("persistent_data").get("brain_dump_content", "")
        yield TextArea(content, id="brain-dump-area")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        # Save on every keystroke? Textual events are frequent. 
        # For simplicity in this CLI, direct save is fine unless performance hit.
        content = event.text_area.text
        self.app.data_manager.get("persistent_data")["brain_dump_content"] = content
        self.app.data_manager.save_config()

import webbrowser

class ParkingLotWidget(Static):
    """Link saver."""
    def compose(self) -> ComposeResult:
        yield Label("Saved URLs", classes="section-header")
        yield Input(placeholder="Paste URL...", id="link-input")
        yield ListView(id="link-list")

    def on_mount(self) -> None:
        self.update_list()

    def update_list(self):
        links = self.app.data_manager.get("persistent_data").get("parking_lot_links", [])
        list_view = self.query_one("#link-list", ListView)
        list_view.clear()
        for link in links:
             list_view.append(ListItem(Label(link)))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        link = event.value.strip()
        if link:
            links = self.app.data_manager.get("persistent_data").get("parking_lot_links", [])
            links.append(link)
            self.app.data_manager.save_config()
            self.update_list()
            event.input.value = ""

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        # ROBUST METHOD: Use the index of the selected item to find the URL in our data.
        # This avoids all UI attribute errors.
        try:
            list_view = self.query_one("#link-list", ListView)
            if list_view.index is not None:
                links = self.app.data_manager.get("persistent_data").get("parking_lot_links", [])
                if 0 <= list_view.index < len(links):
                    url = links[list_view.index]
                    if not url.startswith("http"):
                        url = "https://" + url
                    
                    try:
                        webbrowser.open(url)
                        self.notify(f"Opening: {url}")
                    except Exception as e:
                        self.notify(f"Failed to open link: {e}", severity="error")
        except Exception as e:
             self.notify(f"Error resolving link: {e}", severity="error")

class WaterTrackerWidget(Static):
    """Water intake tracker."""
    def compose(self) -> ComposeResult:
        yield Label("Water Intake", classes="section-header")
        
        # Get goal and current
        data = self.app.data_manager.get("daily_state")
        profile = self.app.data_manager.get("user_profile")
        
        current = data.get("current_water_intake", 0)
        goal = profile.get("daily_water_goal", 2000)
        unit = profile.get("unit_system", "metric")
        unit_label = "ml" if unit == "metric" else "oz"
        
        yield Label(f"{current} / {goal} {unit_label}", id="water-label")
        yield ProgressBar(total=goal, show_eta=False, id="water-progress")
        yield Label("Press 'W' to add water", classes="help-text")
        
        # Initialize progress bar
        # We can't access query_one here easily, need on_mount to set progress
        
    def on_mount(self) -> None:
        self.update_display()

    def update_display(self):
        data = self.app.data_manager.get("daily_state")
        profile = self.app.data_manager.get("user_profile")
        
        current = data.get("current_water_intake", 0)
        goal = profile.get("daily_water_goal", 2000)
        unit = profile.get("unit_system", "metric")
        unit_label = "ml" if unit == "metric" else "oz"
        
        self.query_one("#water-label", Label).update(f"{current} / {goal} {unit_label}")
        self.query_one("#water-progress", ProgressBar).progress = current

    def add_water(self):
        container = self.app.data_manager.get("user_profile").get("container_size", 250)
        current = self.app.data_manager.get("daily_state").get("current_water_intake", 0)
        
        new_val = current + container
        self.app.data_manager.get("daily_state")["current_water_intake"] = new_val
        self.app.data_manager.save_config()
        self.update_display()

    def undo_water(self):
        self.app.data_manager.undo_water_intake()
        self.update_display()

from modules.weather_api import get_weather_for_city
import psutil
import platform
import datetime
import time

class WeatherWidget(Static):
    """Weather display & Clock."""
    def compose(self) -> ComposeResult:
        yield Label("Weather & Time", classes="section-header")
        yield Label("Loading...", id="weather-display")
    
    def on_mount(self) -> None:
        self.update_weather()
        self.set_interval(1, self.update_clock)
        self.set_interval(1800, self.update_weather) # 30 mins

    def update_clock(self):
        # We can append time to the weather string or have a separate line
        # Ideally, we store weather string in a var and re-render.
        # For now, let's just update the label if we have weather data.
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        try:
             # This is a bit hacky, overwriting the label constantly. 
             # Better: Split into two labels?
             # But compose structure is fixed.
             # Let's check if we have stored weather text
             weather = getattr(self, "last_weather", "Loading...")
             self.query_one("#weather-display", Label).update(f"{now_str}\n{weather}")
        except:
             pass

    def update_weather(self):
        # Async work ideally, but requests is blocking. 
        # For this CLI, blocking briefly on a separate thread is best, 
        # or we accept the freeze. Textual has work_worker for async.
        self.run_worker(self.fetch_weather_job, exclusive=True)

    async def fetch_weather_job(self):
        city = self.app.data_manager.get("user_profile").get("city", "Unknown")
        # Ensure we run network request in a thread so we don't block event loop
        # Textual worker wrapper handles async/thread if we specify? 
        # Actually run_worker accepts coroutine or thread function. 
        # But get_weather_for_city is sync. We should wrap it?
        # Textual: worker = self.run_worker(lambda: get_weather_for_city(city), thread=True)
        # But to update UI we need to be careful.
        
        # Simplified:
        # We can just call it in a thread worker.
        pass # Placeholder for the worker logic below
        
    def on_worker_state_changed(self, event) -> None:
        # Simplified approach: just call sync for now to avoid complexity or use standard asyncio wrapper
        # if I can.
        pass

    # Let's retry with a simpler threaded worker approach valid in Textual
    def update_weather(self):
        self.run_worker(self.async_weather_update, thread=True)

    def async_weather_update(self):
        city = self.app.data_manager.get("user_profile").get("city", "Unknown")
        unit = self.app.data_manager.get("user_profile").get("unit_system", "metric")
        weather_str = get_weather_for_city(city, unit_system=unit)
        # Store for clock updates
        self.last_weather = weather_str
        # Update UI from worker immediately
        self.update_clock()


class SystemVitalsWidget(Static):
    """CPU/RAM usage."""
    def compose(self) -> ComposeResult:
        yield Label("System Vitals", classes="section-header")
        yield Label("Initializing...", id="vitals-display")

    def on_mount(self) -> None:
        self.update_vitals()
        self.set_interval(5, self.update_vitals)

    def update_vitals(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        bat_str = f" | Bat: {int(battery.percent)}%" if battery else ""
        
        disk = psutil.disk_usage('/')
        disk_str = f" | Disk: {disk.percent}%"

        # OS Info
        os_info = f"{platform.system()} {platform.release()}"
        uptime = datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))
        
        display = f"CPU: {cpu}% | RAM: {ram}%{disk_str}{bat_str}\n{os_info} | Up: {uptime}"
        self.query_one("#vitals-display", Label).update(display)
