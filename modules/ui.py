from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich import box
from rich.progress import BarColumn, Progress, TextColumn
import time
from datetime import datetime

class DailyDashUI:
    def __init__(self, console: Console):
        self.console = console
        self.layout = Layout()

    def render_dashboard(self, data_manager, weather_info, system_vitals, timer_status):
        """
        Renders the full dashboard using a grid layout.
        """
        self.make_layout()
        theme = self.get_theme(data_manager)
        
        # Populate Header
        self.layout["header"].update(self.make_header(data_manager, theme))
        
        # Populate Columns
        self.layout["planning"].update(self.make_planning_panel(data_manager, theme))
        self.layout["focus"].update(self.make_focus_panel(data_manager, theme, timer_status))
        self.layout["vitals"].update(self.make_vitals_panel(data_manager, weather_info, system_vitals, theme))
        
        # Populate Footer
        self.layout["footer"].update(self.make_footer(theme))
        
        self.console.print(self.layout)

    def make_layout(self):
        """Define the grid layout."""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        self.layout["main"].split_row(
            Layout(name="planning", ratio=1),
            Layout(name="focus", ratio=2),
            Layout(name="vitals", ratio=1),
        )

    def get_theme(self, data_manager):
        from modules.themes import get_theme
        t_name = data_manager.get("app_settings", {}).get("theme", "default")
        return get_theme(t_name)

    def make_header(self, data_manager, theme):
        profile = data_manager.get("user_profile", {})
        name = profile.get("name", "User")
        
        # Date & Time
        now = datetime.now()
        date_str = now.strftime("%A, %B %d")
        time_str = now.strftime("%H:%M")
        
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right", ratio=1)
        
        grid.add_row(
            f"[{theme['primary']}]Welcome, {name}[/]",
            f"[{theme['accent']}]DAILY DASH[/]",
            f"[{theme['secondary']}]{date_str} | {time_str}[/]"
        )
        return Panel(grid, style=f"{theme['box']}")

    def make_planning_panel(self, data_manager, theme):
        """Big 3 Tasks & Habits"""
        daily = data_manager.get("daily_state", {})
        tasks = daily.get("tasks", [])
        
        # Tasks Table
        t_table = Table(box=None, expand=True, show_header=False, padding=(0,0))
        t_table.add_column("State", width=3)
        t_table.add_column("Content")
        
        for t in tasks:
            icon = f"[{theme['success']}]✔[/]" if t["done"] else f"[{theme['error']}]☐[/]"
            
            # Strikethrough if done
            txt = t["text"] if t["text"] else "[dim]Empty...[/dim]"
            if t["done"]:
                txt = f"[strike {theme['dim']}]{txt}[/strike {theme['dim']}]"
            elif not t["text"]:
                txt = f"[{theme['dim']}]{txt}[/]"
            
            if t.get("budget"):
                 txt += f" [{theme['dim']}]({t['budget']})[/]"

            t_table.add_row(icon, txt)
            t_table.add_row("", "") # Spacer
            
        # Habits Section
        h_table = Table(box=None, expand=True, show_header=False, padding=(0,0))
        habits = data_manager.get("persistent_data", {}).get("habits", [])
        habit_status = daily.get("habit_status", {})
        
        if habits:
            h_table.add_row(f"[{theme['secondary']}]HABITS[/]")
            for h in habits:
                checked = habit_status.get(h, False)
                icon = f"[{theme['success']}]✔[/]" if checked else f"[{theme['dim']}]○[/]"
                h_table.add_row(f"{icon} {h}")
        
        # Combine
        master_grid = Table.grid(expand=True)
        
        # Big 3 Panel
        master_grid.add_row(Panel(t_table, title="[b]Big 3 Tasks[/]", border_style=theme['box'], box=box.ROUNDED))
        
        # Habits Panel (if any)
        if habits:
            master_grid.add_row(Panel(h_table, title="[b]Habits[/]", border_style=theme['dim'], box=box.SIMPLE))
            
        return Panel(
            master_grid,
            title=f"[{theme['primary']}]PLANNING[/]", 
            border_style=theme['box']
        )

    def make_focus_panel(self, data_manager, theme, timer_status):
        """Timer, Notes, Parking Lot"""
        # Timer
        timer_text = Text(timer_status, justify="center", style=f"{theme['accent']} bold")
        
        # Brain Dump
        notes = data_manager.get("persistent_data", {}).get("brain_dump_content", [])
        if isinstance(notes, str): notes = [notes] # Fallback
        
        note_text = ""
        # Show last 5 notes
        recent_notes = notes[-8:] if notes else []
        if not recent_notes:
            note_text = f"[{theme['dim']}]No thoughts...[/]"
        else:
            for i, n in enumerate(recent_notes):
                # We can't easily get real index here without passing full list logic, 
                # but for display relative is fine. Actually users might want IDs to delete.
                # Let's show bullet points for now as dashboard is for viewing.
                note_text += f"- {n}\n"
        
        note_panel = Panel(note_text.strip(), title="Brain Dump", border_style=theme['dim'], box=box.SIMPLE)
        
        # Parking Lot
        links = data_manager.get("persistent_data", {}).get("parking_lot_links", [])
        link_text = ""
        if not links:
            link_text = f"[{theme['dim']}]Empty[/]"
        else:
            for l in links[-3:]: # Last 3
                link_text += f"• {l}\n"
        
        link_panel = Panel(link_text.strip(), title="Parking Lot", border_style=theme['dim'], box=box.SIMPLE)

        # Assemble
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_row(Panel(timer_text, title="TIMER", border_style=theme['accent'], box=box.ROUNDED))
        grid.add_row(note_panel)
        grid.add_row(link_panel)
        
        return Panel(grid, title=f"[{theme['primary']}]FOCUS ZONE[/]", border_style=theme['box'])

    def make_vitals_panel(self, data_manager, weather, vitals, theme):
        """Water, Weather, System"""
        
        # Weather
        w_panel = Panel(weather, title="Weather", border_style=theme['secondary'], box=box.SIMPLE)
        
        # System
        sys_panel = Panel(vitals, title="System", border_style=theme['dim'], box=box.SIMPLE)
        
        # Water
        daily = data_manager.get("daily_state", {})
        user = data_manager.get("user_profile", {})
        
        current = daily.get("current_water_intake", 0)
        goal = user.get("daily_water_goal", 2000)
        coffee = daily.get("current_caffeine_intake", 0)
        
        percent = min(100, int((current / goal) * 100))
        
        # Custom ASCII Bar
        bar_len = 10
        filled = int((percent / 100) * bar_len)
        bar_str = "█" * filled + "░" * (bar_len - filled)
        
        water_text = f"[{theme['secondary']}]{bar_str}[/]\n"
        water_text += f"{current}/{goal}ml"
        if coffee > 0:
            water_text += f"\n\n[yellow]☕ {coffee}mg[/]"
            
        water_panel = Panel(Align.center(water_text), title="Hydration", border_style=theme['secondary'], box=box.SIMPLE)
        
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_row(w_panel)
        grid.add_row(water_panel)
        grid.add_row(sys_panel)

        return Panel(grid, title=f"[{theme['primary']}]VITALS[/]", border_style=theme['box'])

    def make_footer(self, theme):
        text = " [bold]w[/]: Water | [bold]t[/]: Task | [bold]k[/]: Timer | [bold]b[/]: Brain Dump | [bold]q[/]: Quit "
        return Panel(Align.center(text), style=f"{theme['dim']} on black", box=box.ROUNDED)
