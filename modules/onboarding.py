from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label, Input, RadioSet, RadioButton
from textual.containers import Container, Vertical
from textual import on
from modules.ui_widgets import TimerWidget

class SetupWizard(Screen):
    CSS = """
    SetupWizard {
        align: center middle;
    }
    Container {
        width: 60;
        height: auto;
        border: solid green;
        padding: 1 2;
        background: $surface;
    }
    Label {
        width: 100%;
        text-align: center;
        margin-bottom: 2;
    }
    Input {
        margin-bottom: 2;
    }
    RadioSet {
        margin-bottom: 2;
    }
    .hidden {
        display: none;
    }
    """

    def compose(self):
        yield Header()
        
        # Step 1: Welcome
        with Container(id="step-1"):
            yield Label("[bold green]Welcome to DailyDash![/]")
            yield Label("A CLI HUD for the focus-driven developer.")
            yield Button("Begin Setup", id="start-btn")

        # Step 2: Units
        with Container(id="step-2", classes="hidden"):
            yield Label("Select your preferred unit system:")
            with RadioSet(id="unit-radio"):
                yield RadioButton("Metric (ml, Celsius)", value=True, id="metric")
                yield RadioButton("Imperial (oz, Fahrenheit)", id="imperial")
            yield Button("Next", id="next-2")

        # Step 3: Container Size
        with Container(id="step-3", classes="hidden"):
            yield Label("What is the size of your water vessel?")
            yield Input(placeholder="e.g. 250 (for ml) or 16 (for oz)", type="integer", id="container-input")
            yield Button("Next", id="next-3")

        # Step 4: Location
        with Container(id="step-4", classes="hidden"):
            yield Label("Enter your City Name for Weather:")
            yield Input(placeholder="e.g. Seattle", id="city-input")
            yield Button("Next", id="next-4")

        # Step 5: Audio
        with Container(id="step-5", classes="hidden"):
            yield Label("Setup Audio?")
            yield Label("We will play Brown Noise to help you focus.")
            yield Button("Enable Audio", id="finish-btn")
        
        yield Footer()

    def on_mount(self) -> None:
        # Pre-fill values if they exist
        try:
            profile = self.app.data_manager.get("user_profile")
            if profile:
                # Units
                unit = profile.get("unit_system", "metric")
                if unit == "imperial":
                    self.query_one("#imperial", RadioButton).value = True
                else:
                    self.query_one("#metric", RadioButton).value = True
                
                # Container
                size = profile.get("container_size")
                if size:
                    self.query_one("#container-input", Input).value = str(size)
                
                # City
                city = profile.get("city")
                if city and city != "Unknown":
                    self.query_one("#city-input", Input).value = city
        except Exception:
            pass # fallback to empty/defaults

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "start-btn":
            self.query_one("#step-1").add_class("hidden")
            self.query_one("#step-2").remove_class("hidden")
        
        elif event.button.id == "next-2":
            self.query_one("#step-2").add_class("hidden")
            self.query_one("#step-3").remove_class("hidden")
            self.query_one("#container-input").focus()

        elif event.button.id == "next-3":
            # specific validation could go here
            self.query_one("#step-3").add_class("hidden")
            self.query_one("#step-4").remove_class("hidden")
            self.query_one("#city-input").focus()

        elif event.button.id == "next-4":
            self.query_one("#step-4").add_class("hidden")
            self.query_one("#step-5").remove_class("hidden")
            self.query_one("#finish-btn").focus()

        elif event.button.id == "finish-btn":
            self.complete_setup()

    def complete_setup(self):
        # Gather data
        app = self.app
        # Retrieve widgets values
        is_metric = self.query_one("#metric").value
        container_size = int(self.query_one("#container-input").value or "250")
        city = self.query_one("#city-input").value or "Unknown"

        # Update Config
        app.data_manager.config["user_profile"]["unit_system"] = "metric" if is_metric else "imperial"
        app.data_manager.config["user_profile"]["container_size"] = container_size
        app.data_manager.config["user_profile"]["city"] = city
        app.data_manager.config["setup_complete"] = True
        app.data_manager.save_config()

        # Transition to dashboard (replace setup screen)
        # Ensure dashboard is known to the app (it should be installed in main.py)
        if not app.is_screen_installed("dashboard"):
             app.install_screen(self.app.dashboard_screen, name="dashboard")
        
        app.switch_screen("dashboard")


class DailyWizard(Screen):
    """Wizard for daily routine check-in."""
    CSS = """
    DailyWizard {
        align: center middle;
    }
    Container {
        width: 60;
        height: auto;
        border: solid blue;
        padding: 1 2;
        background: $surface;
    }
    Label {
        width: 100%;
        text-align: center;
        margin-bottom: 2;
    }
    Input {
        margin-bottom: 1;
    }
    .hidden {
        display: none;
    }
    """

    def compose(self):
        yield Header()

        # Step 1: Big 3 Tasks
        with Container(id="daily-step-1"):
            yield Label("[bold blue]Good Morning![/]")
            yield Label("Identify your 'Big 3' tasks for today:")
            yield Input(placeholder="Task 1", id="task-1")
            yield Input(placeholder="Task 2", id="task-2")
            yield Input(placeholder="Task 3", id="task-3")
            yield Button("Next", id="daily-next-1")

        # Step 2: Water Goal
        with Container(id="daily-step-2", classes="hidden"):
            yield Label("Your Water Goal for today:")
            yield Input(value="2000", id="daily-water-goal") # Will pre-fill in on_mount
            yield Button("Confirm Goal", id="daily-next-2")

        # Step 3: Momentum
        with Container(id="daily-step-3", classes="hidden"):
            yield Label("Start your day with momentum?")
            yield Label("Would you like to start a Pomodoro timer now?")
            with Container(classes="horizontal"):
                yield Button("Yes, Start Focus", id="daily-finish-yes", variant="success")
                yield Button("No, Just Dashboard", id="daily-finish-no", variant="primary")
        
        yield Footer()

    def on_mount(self):
        # Pre-fill water goal
        goal = self.app.data_manager.get("user_profile").get("daily_water_goal", 2000)
        self.query_one("#daily-water-goal", Input).value = str(goal)
        self.query_one("#task-1").focus()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "daily-next-1":
            self.query_one("#daily-step-1").add_class("hidden")
            self.query_one("#daily-step-2").remove_class("hidden")
            self.query_one("#daily-water-goal").focus()
        
        elif event.button.id == "daily-next-2":
            # Save water goal if changed? 
            # Or just proceed.
            self.query_one("#daily-step-2").add_class("hidden")
            self.query_one("#daily-step-3").remove_class("hidden")
            self.query_one("#daily-finish-yes").focus()
        
        elif event.button.id == "daily-finish-yes":
            self.complete_daily(start_timer=True)
        
        elif event.button.id == "daily-finish-no":
            self.complete_daily(start_timer=False)

    def complete_daily(self, start_timer=False):
        # 1. Gather Tasks
        t1 = self.query_one("#task-1").value
        t2 = self.query_one("#task-2").value
        t3 = self.query_one("#task-3").value
        
        # 2. Update DataManager
        # We need to manually update the DAILY state now.
        # But wait, confirm_new_day() resets tasks to empty. 
        # So we should call confirm_new_day() FIRST to clear old data, THEN set new tasks.
        
        self.app.data_manager.confirm_new_day()
        
        tasks = self.app.data_manager.config["daily_state"]["tasks"]
        # Assuming tasks list has 3 items
        if len(tasks) >= 3:
            tasks[0]["text"] = t1
            tasks[1]["text"] = t2
            tasks[2]["text"] = t3
            tasks[0]["done"] = False
            tasks[1]["done"] = False
            tasks[2]["done"] = False # Reset status just in case
        
        # 3. Update Water Goal
        goal = int(self.query_one("#daily-water-goal").value or "2000")
        self.app.data_manager.config["user_profile"]["daily_water_goal"] = goal
        
        self.app.data_manager.save_config()

        # 4. Switch to Dashboard
        if not self.app.is_screen_installed("dashboard"):
             self.app.install_screen(self.app.dashboard_screen, name="dashboard")
        
        self.app.switch_screen("dashboard")
        
        # 5. Start Timer if requested
        # We need to access the timer widget on the dashboard.
        if start_timer:
            # We can use call_later because switch_screen might take a tick
            self.set_timer(0.5, self.start_timer_on_dash)

    def start_timer_on_dash(self):
        try:
             # We can access widgets on the dashboard screen directly if we have reference
             self.app.dashboard_screen.query_one("#timer", TimerWidget).toggle_timer()
             self.app.notify("Momentum! Timer Started.")
        except Exception as e:
            self.app.notify(f"Could not start timer: {e}")
