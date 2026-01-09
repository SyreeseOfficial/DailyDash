from textual.app import App, ComposeResult
from textual.widgets import Label, Header, Footer, Placeholder
from textual.screen import Screen

from modules.data_handler import DataManager
from modules.onboarding import SetupWizard, DailyWizard, SettingsScreen
from modules.audio_manager import AudioManager
import time
from modules.ui_widgets import (
    TaskListWidget, TimerWidget, BrainDumpWidget, WaterTrackerWidget, 
    WeatherWidget, ParkingLotWidget, SystemVitalsWidget
)

class DashboardScreen(Screen):
    """The main dashboard screen."""
    def compose(self) -> ComposeResult:
        yield Header()
        
        # We need a Container for the grid? Textual Screen can be the grid container if layout: grid is set on it locally or via CSS.
        # In CSS I set DashboardScreen { layout: grid; ... }
        
        # Col 1
        yield TaskListWidget(id="task-list")
        
        # Col 2
        yield TimerWidget(id="timer")
        yield BrainDumpWidget(id="brain-dump")
        yield ParkingLotWidget(id="parking-lot")
        
        # Col 3
        yield WaterTrackerWidget(id="water")
        yield WeatherWidget(id="weather")
        yield SystemVitalsWidget(id="vitals")

        yield Footer()

class DailyDashApp(App):
    CSS_PATH = "layout.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("w", "add_water", "Add Water"),
        ("W", "undo_water", "Undo Water"),
        ("p", "toggle_timer", "Start/Pause Timer"),
        ("d", "cycle_timer_duration", "Cycle Duration"),
        ("r", "reset_timer", "Reset Timer"),
        ("n", "toggle_noise", "Toggle Noise"),
        ("s", "open_settings", "Settings"),
    ]

    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.audio_manager = AudioManager()
        self.dashboard_screen = DashboardScreen() # Keep a reference
        self.start_time = time.time()
        self.last_stand_check = self.start_time
        self.last_eye_check = self.start_time

    def check_health_nags(self):
        # Only nag if enabled in settings
        settings = self.data_manager.get("app_settings", {})
        now = time.time()

        # Stand Up: Every 60 mins (3600s)
        if settings.get("nag_stand_up", True):
            if now - self.last_stand_check > 3600:
                self.push_screen_stand_up()
                self.last_stand_check = now
        
        # Eye Strain: Every 20 mins (1200s)
        if settings.get("nag_eye_strain", True):
            if now - self.last_eye_check > 1200:
                self.notify("👀 20-20-20 Rule! Look away at something 20ft away.", title="Health Alert", severity="warning", timeout=10)
                self.last_eye_check = now

    def push_screen_stand_up(self):
        # Simple modal or just a notification? PRD says "Modal or flashing text"
        # Let's do a strong notification for now, or a simple modal.
        # Ideally, a dedicated Screen. For simplicity/speed -> Notify with high duration or a simple function
        self.notify("🚶 STAND UP! Stretch your legs.", title="Health Alert", severity="error", timeout=20)

    def action_undo_water(self):
        try:
            self.dashboard_screen.query_one("#water", WaterTrackerWidget).undo_water()
            self.notify("Water intake undone.")
        except:
            pass

    def action_open_settings(self):
        # Open the new settings screen
        self.switch_screen(SettingsScreen())

    def action_add_water(self):
        try:
            self.dashboard_screen.query_one("#water", WaterTrackerWidget).add_water()
        except:
            pass

    def action_toggle_timer(self):
        try:
            self.dashboard_screen.query_one("#timer", TimerWidget).toggle_timer()
        except:
            pass

    def action_reset_timer(self):
        try:
            self.dashboard_screen.query_one("#timer", TimerWidget).reset_timer()
        except:
            pass

    def action_cycle_timer_duration(self):
        try:
            self.dashboard_screen.query_one("#timer", TimerWidget).cycle_duration()
        except:
            pass


    def action_toggle_noise(self):
        # We should update UI too, maybe show a toast or change an icon
        is_playing = self.audio_manager.toggle_brown_noise()
        if is_playing:
            self.notify("Brown Noise: ON")
        else:
            self.notify("Brown Noise: OFF")

    def on_mount(self) -> None:
        self.install_screen(self.dashboard_screen, name="dashboard")
        
        # Start health monitor
        self.set_interval(60, self.check_health_nags)

        if not self.data_manager.get("setup_complete"):
            self.push_screen(SetupWizard())
        elif self.data_manager.is_new_day():
            self.push_screen(DailyWizard())
        else:
            self.push_screen("dashboard")

if __name__ == "__main__":
    app = DailyDashApp()
    app.run()
