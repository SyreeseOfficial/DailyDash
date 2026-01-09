from textual.app import App, ComposeResult
from textual.widgets import Label, Header, Footer, Placeholder
from textual.screen import Screen

from modules.data_handler import DataManager
from modules.onboarding import SetupWizard
from modules.audio_manager import AudioManager
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
        ("p", "toggle_timer", "Start/Pause Timer"),
        ("r", "reset_timer", "Reset Timer"),
        ("n", "toggle_noise", "Toggle Noise"),
    ]

    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.audio_manager = AudioManager()
        self.dashboard_screen = DashboardScreen() # Keep a reference

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

    def action_toggle_noise(self):
        # We should update UI too, maybe show a toast or change an icon
        is_playing = self.audio_manager.toggle_brown_noise()
        if is_playing:
            self.notify("Brown Noise: ON")
        else:
            self.notify("Brown Noise: OFF")

    def on_mount(self) -> None:
        self.install_screen(self.dashboard_screen, name="dashboard")
        
        if not self.data_manager.get("setup_complete"):
            self.push_screen(SetupWizard())
        else:
            self.push_screen("dashboard")

if __name__ == "__main__":
    app = DailyDashApp()
    app.run()
