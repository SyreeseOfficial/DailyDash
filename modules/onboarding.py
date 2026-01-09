from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label, Input, RadioSet, RadioButton
from textual.containers import Container, Vertical
from textual import on

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

        app.pop_screen()
        # In a real app we might push the Dashboard here or ensure Main loads it
        app.install_screen(self.app.dashboard_screen, name="dashboard")
        app.push_screen("dashboard")
