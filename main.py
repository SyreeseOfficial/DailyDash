import argparse
import time
import sys
import os
import threading
try:
    from plyer import notification
except ImportError:
    notification = None

# Hide Pygame support prompt
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    from rich.layout import Layout
    from rich.live import Live
    from rich.align import Align
    from rich import box
    from rich.prompt import Prompt, IntPrompt, Confirm

    from modules.data_handler import DataManager
    from modules.audio_manager import AudioManager
    from modules.clipboard_manager import ClipboardManager
    from modules.weather_api import get_weather_for_city
    from modules.themes import get_theme
    import psutil
except ImportError as e:
    print(f"❌ Error: Missing dependencies. ({e})")
    print("\nPlease make sure you are running in the virtual environment:")
    print("  source venv/bin/activate")
    print("  python main.py")
    print("\nOR run directly:")
    print("  ./venv/bin/python main.py")
    sys.exit(1)

# Initialize global objects
console = Console()
data_manager = DataManager()
# Audio manager might be needed for noise command
audio_manager = AudioManager()
# Clipboard Manager
clipboard_manager = ClipboardManager(data_manager)

# Load Theme
current_theme_name = data_manager.get("app_settings", {}).get("theme", "default")
T = get_theme(current_theme_name)

def get_system_vitals():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    batt = psutil.sensors_battery()
    batt_str = f"{batt.percent}%" if batt else "AC"
    return f"CPU: {cpu}% | RAM: {mem}% | Disk: {disk}% | PWR: {batt_str}"

import subprocess
timer_end_timestamp = None
current_timer_id = None

# Eye Strain Thread Logic
def eye_strain_worker():
    while True:
        # Check config inside loop so we respect changes (simple poll)
        # Note: In a real app we might want better signaling, but this suffices for CLI
        settings = data_manager.get("app_settings", {})
        enabled = settings.get("nag_eye_strain", True)
        
        if enabled:
            # 20 minutes = 1200 seconds
            time.sleep(1200)
            # Re-check in case it was disabled during sleep
            if data_manager.get("app_settings", {}).get("nag_eye_strain", True):
                try:
                    if notification:
                        notification.notify(
                            title='DailyDash Health',
                            message='20-20-20 Rule:\nLook at something 20 feet away for 20 seconds.',
                            app_name='DailyDash',
                            timeout=10
                        )
                    else:
                        # Fallback for systems without plyer support (e.g. servers?)
                        pass 

                    # Play a subtle ding if audio enabled
                    if settings.get("audio_enabled", True):
                         audio_manager.play_chime()
                except Exception as e:
                    # console.print(f"[dim]Notification failed: {e}[/dim]")
                    pass
        else:
            time.sleep(60) # check again in a minute

# Stand Up Thread Logic
def stand_up_worker():
    while True:
        settings = data_manager.get("app_settings", {})
        enabled = settings.get("nag_stand_up", True)
        
        if enabled:
            # 60 minutes = 3600 seconds
            time.sleep(3600)
            if data_manager.get("app_settings", {}).get("nag_stand_up", True):
                try:
                    if notification:
                        notification.notify(
                            title='DailyDash Health',
                            message='Time to Stand Up!\nStretch your legs for a bit.',
                            app_name='DailyDash',
                            timeout=10
                        )
                    
                    if settings.get("audio_enabled", True):
                         audio_manager.play_chime()
                except Exception:
                    pass
        else:
            time.sleep(60)

# Start Threads
clipboard_manager.start_monitoring()

# Start Eye Strain Thread
eye_thread = threading.Thread(target=eye_strain_worker, daemon=True)
eye_thread.start()

# Start Stand Up Thread
stand_thread = threading.Thread(target=stand_up_worker, daemon=True)
stand_thread.start()

import random

QUOTES = [
    "The secret of getting ahead is getting started.",
    "It always seems impossible until it's done.",
    "Don't watch the clock; do what it does. Keep going.",
    "The future depends on what you do today.",
    "Focus on being productive instead of busy.",
    "Small steps in the right direction can turn out to be the biggest step of your life.",
    "Discipline is choosing between what you want now and what you want most."
]

def command_status(args, show_hints=True):
    """
    Displays the 'Head-Up Display' summary:
    - Weather & System
    - Big 3 Tasks
    - Health (Water + Coffee)
    - Brain Dump
    - Saved URLs
    """
    # 1. Header Info
    user_profile = data_manager.get("user_profile", {})
    name = user_profile.get("name", "User")
    city = user_profile.get("city", "Unknown")
    units = user_profile.get("unit_system", "metric")
    weather_info = get_weather_for_city(city, units)
    vitals = get_system_vitals()
    
    # 2. Daily State
    daily_state = data_manager.get("daily_state", {})
    tasks = daily_state.get("tasks", [])
    water = daily_state.get("current_water_intake", 0)
    caffeine = daily_state.get("current_caffeine_intake", 0)
    goal = user_profile.get("daily_water_goal", 2000)
    
    # 3. Persistent Data
    persistent = data_manager.get("persistent_data", {})
    notes = persistent.get("brain_dump_content", "")
    links = persistent.get("parking_lot_links", [])

    # --- UI Construction ---
    current_time = time.strftime('%H:%M')
    current_date = time.strftime('%a %b %d')
    
    # 1. Header Grid
    header = Table.grid(expand=True)
    header.add_column(justify="left", style=T["primary"])
    header.add_column(justify="right", style=T["accent"])
    header.add_row(f"Hi {name}!", f"DailyDash - {current_date} {current_time}")
    console.print(header)
    
    # 2. Main Table (No Title)
    table = Table(box=box.ROUNDED, expand=True, padding=(0, 1), border_style=T["box"])
    table.add_column("Section", style=T["secondary"], no_wrap=True)
    table.add_column("Content", style=T["text"])

    # Weather
    table.add_row("Weather", weather_info)
    
    # System
    if timer_end_timestamp and timer_end_timestamp > time.time():
        end_struct = time.localtime(timer_end_timestamp)
        end_str = time.strftime("%H:%M", end_struct)
        vitals += f" | ⏳ Ends: {end_str}"
    table.add_row("System", f"[dim]{vitals}[/dim]")

    # Health (Water + Caffeine on same line)
    water_percent = min(100, int((water / goal) * 100))
    water_color = "blue" if water_percent < 100 else "green"
    
    health_str = f":droplet: [{water_color}]{water}ml[/] / {goal}ml ({water_percent}%)"
    if caffeine > 0:
         health_str += f"  |  :coffee: [yellow]{caffeine}mg[/yellow]"
    else:
         health_str += f"  |  :coffee: [dim]{caffeine}mg[/dim]"
    
    table.add_row("Health", health_str, end_section=True)
    
    # Tasks
    task_str = ""
    for t in tasks:
        icon = f"[{T['success']}]✔[/{T['success']}]" if t["done"] else f"[{T['error']}]☐[/{T['error']}]"
        txt = t["text"] if t["text"] else f"[{T['dim']}]Empty[/{T['dim']}]"
        if t.get("budget"):
            txt += f" [{T['dim']}]({t['budget']})[/{T['dim']}]"
        task_str += f"{icon} {txt}\n"
    table.add_row("Big 3 Tasks", task_str.strip())
    
    # Habits
    habits = persistent.get("habits", [])
    habit_status = daily_state.get("habit_status", {})
    habit_str = ""
    if habits:
        for h in habits:
            is_done = habit_status.get(h, False)
            icon = f"[{T['success']}]✔[/{T['success']}]" if is_done else f"[{T['error']}]☐[/{T['error']}]"
            habit_str += f"{icon} {h}\n"
    else:
        habit_str = f"[{T['dim']}]No habits set[/{T['dim']}]"
    table.add_row("Habits", habit_str.strip(), end_section=True)

    # Links (Refined Title)
    link_str = ""
    for i, link in enumerate(links):
        link_str += f"{i+1}. [link={link}]{link}[/link]\n"
    link_str = link_str.strip() if link_str else f"[{T['dim']}]No links[/{T['dim']}]"
    table.add_row("Saved URLs", link_str)

    # Brain Dump (Full Content)
    if isinstance(notes, list):
        note_content = "\n".join([f"- {n}" for n in notes]) if notes else f"[{T['dim']}]No notes[/{T['dim']}]"
    else:
        # Fallback for legacy string support (unlikely strictly needed but safe)
        note_content = notes.strip() if notes else f"[{T['dim']}]No notes[/{T['dim']}]"
    
    table.add_row("Brain Dump", note_content)

    console.print(table)
    
    # 3. Quote (Bottom)
    quote = random.choice(QUOTES)
    console.print(Align.center(f"[italic {T['dim']}]\"{quote}\"[/italic {T['dim']}]"), style=f"italic {T['secondary']}")
    # Removed explicit spacer to reduce gap

    # Tooltips / Usage Footer
    if show_hints:
        tips = f"""[{T['dim']}]Try these commands:[/{T['dim']}]
[{T['secondary']}]task add "Todo"[/{T['secondary']}]  |  [{T['secondary']}]water add[/{T['secondary']}]  |  [{T['secondary']}]coffee add[/{T['secondary']}]  |  [{T['secondary']}]timer 25[/{T['secondary']}]
[{T['dim']}]Run 'python main.py help' for a full guide.[/{T['dim']}]"""
        console.print(Align.center(tips))

# ... (Previous commands remain, adding new ones below)

def command_coffee(args):
    action = args.action
    caffeine_size = data_manager.get("user_profile", {}).get("caffeine_size", 50)
    
    if action == "add":
        current = data_manager.config["daily_state"].get("current_caffeine_intake", 0)
        new_val = current + caffeine_size
        data_manager.config["daily_state"]["current_caffeine_intake"] = new_val
        data_manager.save_config()
        console.print(f"[yellow]Coffee time![/yellow] Added {caffeine_size}mg. Total: {new_val}mg")
        
    elif action == "undo":
        current = data_manager.config["daily_state"].get("current_caffeine_intake", 0)
        new_val = max(0, current - caffeine_size)
        data_manager.config["daily_state"]["current_caffeine_intake"] = new_val
        data_manager.save_config()
        console.print(f"[yellow]Undid coffee.[/yellow] Total: {new_val}mg")

def command_end_day(args):
    """
    Logs history and resets daily state.
    """
    if Confirm.ask("[bold red]End Day & Reset?[/bold red] This will save stats and clear daily progress.", default=True):
        # Check setting
        logging_enabled = data_manager.get("app_settings", {}).get("history_logging", True)
        if logging_enabled:
            data_manager.log_daily_history()
            console.print("[dim]History logged to CSV.[/dim]")
            
        data_manager.confirm_new_day()
        console.print("[green]Day reset. Good job today![/green]")
        time.sleep(2.0)

# ... (Existing interactive_mode and main dispatcher updates)

# ... (Removed duplicate interactive_mode and main)


def command_help(args):
    """Display a rich help guide."""
    help_text = """
[bold cyan]DailyDash CLI Guide[/bold cyan]

[bold]Dashboard[/bold]
  [green]status[/green]        Show the main dashboard (default).
  [green]setup[/green]         Run configuration wizard.

[bold]Task Management[/bold]
  [green]task list[/green]           Show your Big 3 tasks.
  [green]task add <text>[/green]     Add a task to the first empty slot.
  [green]task done <id>[/green]      Mark task #<id> as complete.
  [green]task delete <id>[/green]    Clear task #<id>.

[bold]Focus Tools[/bold]
  [green]timer <min>[/green]       Start a blocking focus timer (default 25m).
  [green]noise play[/green]        Play Brown Noise (Ctrl+C to stop).

[bold]Hydration[/bold]
  [green]water show[/green]        Show current intake.
  [green]water add[/green]         Add default container amount.
  [green]water undo[/green]        Remove last entry.

[bold]Brain Dump (Notes)[/bold]
  [green]note show[/green]         View your brain dump.
  [green]note add <text>[/green]     Append a note.
  [green]note clear[/green]        Clear all notes.

[bold]Parking Lot (Links)[/bold]
  [green]link list[/green]         List saved URLs.
  [green]link add <url>[/green]      Save a URL.
  [green]link open <id>[/green]      Open URL in browser.
    """
    console.print(Panel(help_text, title="Help & Usage", border_style=T["success"]))

def command_setup(args):
    """Interactive setup wizard."""
    console.print("[bold green]Welcome to DailyDash Setup[/bold green]")
    
    # 0. Name
    name = Prompt.ask("What is your Name?", default="User")

    # 1. Units
    is_metric = Confirm.ask("Use Metric units? (Celsius, ml)", default=True)
    unit_system = "metric" if is_metric else "imperial"
    
    # 2. City
    city = Prompt.ask("Enter your City for Weather", default="New York")
    
    # 3. Water Container
    default_size = 250 if is_metric else 8
    container = IntPrompt.ask("Enter your Water Container size (e.g. glass size)", default=default_size)
    
    # 4. Water Goal
    default_goal = 2000 if is_metric else 64
    goal = IntPrompt.ask("Enter Daily Water Goal", default=default_goal)

    # 5. Caffeine Size
    console.print("[dim]Note: 50mg is roughly a standard cup of coffee.[/dim]")
    caffeine_size = IntPrompt.ask("Caffeine Cup Size (mg)", default=50)

    # 6. Logging
    history_logging = Confirm.ask("Log daily history to CSV?", default=True)

    # 7. Eye Strain Reminder
    eye_strain = Confirm.ask("Enable Eye Strain Reminder (every 20m)?", default=True)

    # 8. EOD Journal
    eod_journal = Confirm.ask("Enable End of Day Journal?", default=False)
    
    # 9. Clipboard
    clipboard_en = Confirm.ask("Enable Clipboard Manager (Stores last 10 copied items)?", default=False)
    
    # 10. Habits (New)
    habits = []
    if Confirm.ask("Do you want to track daily habits (0-3)? (Optional)", default=True):
        for i in range(3):
            h = Prompt.ask(f"Habit #{i+1} Name (Leave empty to stop)", default="")
            if h.strip():
                habits.append(h.strip())
            else:
                break

    # 11. Day Reset Time
    reset_hour = IntPrompt.ask("Day Reset Hour (0-23) [0=Midnight, 4=4AM]", default=0)
    if not (0 <= reset_hour <= 23):
        reset_hour = 0

    # Save
    data_manager.config["user_profile"]["name"] = name
    data_manager.config["user_profile"]["unit_system"] = unit_system
    data_manager.config["user_profile"]["city"] = city
    data_manager.config["user_profile"]["container_size"] = container
    data_manager.config["user_profile"]["daily_water_goal"] = goal
    data_manager.config["user_profile"]["caffeine_size"] = caffeine_size
    data_manager.config["user_profile"]["day_reset_hour"] = reset_hour
    data_manager.config["app_settings"]["history_logging"] = history_logging
    data_manager.config["app_settings"]["nag_eye_strain"] = eye_strain
    data_manager.config["app_settings"]["eod_journal_enabled"] = eod_journal
    data_manager.config["app_settings"]["clipboard_enabled"] = clipboard_en
    
    # Save habits
    data_manager.config["persistent_data"]["habits"] = habits
    data_manager.config["daily_state"]["habit_status"] = {h: False for h in habits}
    
    data_manager.config["setup_complete"] = True
    
    data_manager.save_config()
    console.print("[bold green]Setup Complete![/bold green] Run [cyan]python main.py[/cyan] to see your dashboard.")

def command_task(args):
    action = args.action
    daily_state = data_manager.get("daily_state", {})
    tasks = daily_state.get("tasks", [])

    if action == "list":
        table = Table(title="Current Tasks", box=box.SIMPLE, border_style=T["box"])
        table.add_column("ID", style=T["primary"], width=4)
        table.add_column("Status", width=8)
        table.add_column("Description")
        table.add_column("Est. Time", style=T["secondary"])
        
        for t in tasks:
            status = "[green]DONE[/green]" if t["done"] else "[red]TODO[/red]"
            budget = f"({t['budget']})" if t.get("budget") else ""
            table.add_row(str(t["id"]), status, t["text"] or "[dim]Empty[/dim]", budget)
        console.print(table)
        
    elif action == "add":
        text = " ".join(args.text)
        budget = args.budget if hasattr(args, 'budget') else None
        
        found = False
        for t in tasks:
            if not t["text"]:
                t["text"] = text
                t["done"] = False
                t["budget"] = budget
                found = True
                budget_str = f" [blue]({budget})[/blue]" if budget else ""
                console.print(f"[green]Added task to slot {t['id']}:[/green] {text}{budget_str}")
                break
        if not found:
            console.print("[yellow]All 3 task slots are full. Use 'task done <id>' or 'task delete <id>' first.[/yellow]")
        else:
            data_manager.save_config()

    elif action == "done":
        try:
            t_id = int(args.target_id)
            for t in tasks:
                if t["id"] == t_id:
                    t["done"] = True
                    console.print(f"[green]Task {t_id} marked as done![/green]")
                    data_manager.save_config()
                    return
            console.print(f"[red]Task ID {t_id} not found.[/red]")
        except:
            console.print("[red]Invalid ID format.[/red]")

    elif action == "delete":
        try:
            t_id = int(args.target_id)
            for t in tasks:
                if t["id"] == t_id:
                    t["text"] = ""
                    t["done"] = False
                    console.print(f"[yellow]Task {t_id} cleared.[/yellow]")
                    data_manager.save_config()
                    return
            console.print(f"[red]Task ID {t_id} not found.[/red]")
        except:
            console.print("[red]Invalid ID format.[/red]")

def command_water(args):
    action = args.action
    if action == "show":
        daily_state = data_manager.get("daily_state", {})
        water = daily_state.get("current_water_intake", 0)
        goal = data_manager.get("user_profile", {}).get("daily_water_goal", 2000)
        console.print(f"💧 Current Intake: [blue]{water}ml[/blue] / {goal}ml")
        
    elif action == "add":
        container = data_manager.get("user_profile", {}).get("container_size", 250)
        current = data_manager.get("daily_state").get("current_water_intake", 0)
        
        new_val = current + container
        data_manager.config["daily_state"]["current_water_intake"] = new_val
        data_manager.save_config()
        console.print(f"[blue]Glug glug![/blue] Added {container}ml. Total: {new_val}ml")
        
    elif action == "undo":
        new_val = data_manager.undo_water_intake()
        console.print(f"[yellow]Undid last water.[/yellow] Total: {new_val}ml")

def command_note(args):
    action = args.action
    persistent = data_manager.get("persistent_data", {})
    # It should be a list now due to migration
    current_notes = persistent.get("brain_dump_content", [])
    if isinstance(current_notes, str):
        current_notes = [] # Fallback if migration failed or empty

    if action == "show":
        if not current_notes:
            panel = Panel(f"[{T['dim']}]No notes found.[/{T['dim']}]", title="Brain Dump", border_style=T["warning"])
            console.print(panel)
        else:
            table = Table(title="Brain Dump", box=box.SIMPLE, show_header=True, border_style=T["box"])
            table.add_column("ID", width=4, style=T["primary"])
            table.add_column("Note")
            for i, note in enumerate(current_notes):
                table.add_row(str(i+1), note)
            console.print(table)
        
    elif action == "add":
        new_text = " ".join(args.text)
        current_notes.append(new_text)
        data_manager.config["persistent_data"]["brain_dump_content"] = current_notes
        data_manager.save_config()
        console.print("[green]Note added![/green]")
        
    elif action == "clear":
        data_manager.config["persistent_data"]["brain_dump_content"] = []
        data_manager.save_config()
        console.print("[yellow]Brain dump cleared.[/yellow]")
        
    elif action == "delete":
        try:
            raw_input = args.target_id
            indices_to_delete = set()
            
            # Parse input like "1,2,5-7"
            parts = raw_input.replace(" ", "").split(",")
            for p in parts:
                if "-" in p:
                    start, end = map(int, p.split("-"))
                    indices_to_delete.update(range(start, end + 1))
                elif p:
                    indices_to_delete.add(int(p))
            
            # Filter valid (1-based to 0-based check)
            valid_indices = {i for i in indices_to_delete if 1 <= i <= len(current_notes)}
            
            if not valid_indices:
                console.print(f"[red]No valid IDs found in range 1-{len(current_notes)}.[/red]")
                return

            # Delete (Filter method)
            # We keep notes whose (index + 1) is NOT in valid_indices
            new_notes = [n for i, n in enumerate(current_notes) if (i + 1) not in valid_indices]
            
            deleted_count = len(current_notes) - len(new_notes)
            
            data_manager.config["persistent_data"]["brain_dump_content"] = new_notes
            data_manager.save_config()
            console.print(f"[yellow]Deleted {deleted_count} note(s).[/yellow]")
            
        except ValueError:
             console.print("[red]Invalid format. Use IDs like '1' or '1,3' or '1-5'.[/red]")

def command_link(args):
    action = args.action
    persistent = data_manager.get("persistent_data", {})
    links = persistent.get("parking_lot_links", [])

    if action == "list":
        table = Table(title="Parking Lot (Saved URLs)", box=box.SIMPLE, border_style=T["box"])
        table.add_column("ID", style=T["primary"], width=4)
        table.add_column("URL", style=T["secondary"])
        
        for i, link in enumerate(links):
            table.add_row(str(i+1), link)
        console.print(table)
        
    elif action == "add":
        url = args.url
        # Basic validation could go here
        links.append(url)
        data_manager.config["persistent_data"]["parking_lot_links"] = links
        data_manager.save_config()
        console.print(f"[green]Link saved:[/green] {url}")
        
    elif action == "delete":
        try:
            link_id = int(args.target_id)
            if 1 <= link_id <= len(links):
                removed = links.pop(link_id - 1)
                data_manager.config["persistent_data"]["parking_lot_links"] = links
                data_manager.save_config()
                console.print(f"[yellow]Removed:[/yellow] {removed}")
            else:
                console.print(f"[red]ID {link_id} out of range.[/red]")
        except ValueError:
            console.print("[red]Invalid ID format.[/red]")

    elif action == "open":
         try:
            link_id = int(args.target_id)
            if 1 <= link_id <= len(links):
                import webbrowser
                target = links[link_id - 1]
                console.print(f"[green]Opening:[/green] {target}")
                webbrowser.open(target)
            else:
                console.print(f"[red]ID {link_id} out of range.[/red]")
         except ValueError:
            console.print("[red]Invalid ID format.[/red]")

def command_timer(args):
    """
    Non-blocking focus timer.
    """
    global timer_end_timestamp, current_timer_id
    
    # Check if timer is already running
    if timer_end_timestamp and timer_end_timestamp > time.time():
        remaining = int((timer_end_timestamp - time.time()) / 60)
        if not Confirm.ask(f"[yellow]Timer already running ({remaining}m left). Cancel and start new?[/yellow]", default=True):
            console.print("[dim]Timer start cancelled.[/dim]")
            return

    duration_min = args.duration
    timer_end_timestamp = time.time() + duration_min * 60
    
    # Generate unique ID for this timer instance
    this_timer_id = time.time()
    current_timer_id = this_timer_id
    
    # Background thread for bell
    def timer_bell(timer_id):
        total_seconds = duration_min * 60
        time.sleep(total_seconds)
        
        # Check if this timer is still the active one
        if current_timer_id == timer_id:
            audio_manager.play_chime()
            
            # Desktop Notification
            try:
                subprocess.Popen(['notify-send', 'DailyDash Timer', 'Time is up! Take a break.'])
            except FileNotFoundError:
                # notify-send might not be installed
                pass
            except Exception as e:
                # unexpected error
                pass

    t = threading.Thread(target=timer_bell, args=(this_timer_id,), daemon=True)
    t.start()
    
    console.print(f"[bold green]Timer started for {duration_min} minutes.[/bold green]")
    time.sleep(1)

def command_noise(args):
    if args.action == "play":
        console.print("[bold  #964B00]Playing Brown Noise... (Ctrl+C to stop)[/]")
        audio_manager.toggle_brown_noise() # Starts playing
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            audio_manager.toggle_brown_noise() # Stops
            console.print("\n[dim]Noise stopped.[/dim]")


            audio_manager.toggle_brown_noise() # Stops
            console.print("\n[dim]Noise stopped.[/dim]")

def command_clipboard(args):
    """
    Shows clipboard history and allows actions.
    """
    settings = data_manager.get("app_settings", {})
    if not settings.get("clipboard_enabled", False):
        console.print("[yellow]Clipboard Manager is DISABLED in settings.[/yellow]")
        return
        
    menu_clipboard()
def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

def shutdown_sequence():
    # Helper to capture EOD note if enabled
    settings = data_manager.get("app_settings", {})
    if settings.get("eod_journal_enabled", False):
        cls()
        console.print(Align.center("\n[bold yellow]End of Day Journal[/bold yellow]"))
        console.print(Align.center("[italic]How was your day? What did you accomplish?[/italic]"))
        
        note = Prompt.ask("\nQuick Note (Enter to skip)", default="")
        if note.strip():
            # Log with note
            data_manager.log_daily_history(note=note.strip())
            console.print("[green]Note saved.[/green]")
            time.sleep(1.0)
        else:
            # Still update stats on exit even if no note
            data_manager.log_daily_history()

    cls()
    console.print(Align.center("\n\n[bold cyan]DailyDash[/bold cyan]"))
    
    msgs = [
        "See you tomorrow, Legend.",
        "Stay hard.",
        "Focus is the key.",
        "Rest well.",
        "You crushed it today.",
        "1% better every day."
    ]
    msg = random.choice(msgs)
    console.print(Align.center(f"[italic]{msg}[/italic]\n\n"))
    sys.exit(0)

def interactive_mode():
    """
    Main interactive loop.
    """
    while True:
        try:
            cls()
            # Show Dashboard
            command_status(None, show_hints=False)
            
            # Interactive Prompt
            console.print(f"\n[{T['primary']}]Interactive Menu[/{T['primary']}]")
            console.print("[dim]w: Water | c: Coffee | t: Task | k: Timer | b: Brain Dump | s: Saved URLs | h: Habits | v: Clipboard | e: End Day | m: Menu | q: Quit[/dim]")

            choice = Prompt.ask("Command", choices=["w", "c", "t", "k", "b", "s", "h", "v", "e", "m", "q"], default="q", show_choices=False, show_default=False)
            
            if choice == "q":
                shutdown_sequence()
                break
                
            elif choice == "w":
                # Add Water (default amount)
                args = argparse.Namespace(action="add")
                command_water(args)
                time.sleep(1.0)
                
            elif choice == "c":
                # Coffee - Changed from k
                args = argparse.Namespace(action="add")
                command_coffee(args)
                time.sleep(1.0)
                
            elif choice == "e":
                # End Day
                command_end_day(None)
                
            elif choice == "t":
                # Task Menu
                menu_task()
            
            elif choice == "k":
                # Timer - Changed from c
                mins = IntPrompt.ask("Duration (minutes)", default=25)
                args = argparse.Namespace(duration=mins)
                command_timer(args)
                
            elif choice == "b":
                # Brain Dump
                menu_note()
            
            elif choice == "s":
                # Saved URLs - Changed from p
                menu_parking_lot()

            elif choice == "h":
                # Habit Menu
                menu_habit()

            elif choice == "v":
                command_clipboard(None)
            
            elif choice == "m":
                menu_more_settings()
                
        except KeyboardInterrupt:
            shutdown_sequence()
            break

def menu_task():
    while True:
        cls()
        console.print(f"[{T['primary']}]Task Management[/{T['primary']}]")
        # Show list
        args = argparse.Namespace(action="list")
        command_task(args)
        
        console.print("\n[dim]x: Mark Done | a: Add | d: Delete | c: Clear All | b: Back[/dim]")
        choice = Prompt.ask("Action", choices=["x", "a", "d", "c", "b"], default="b", show_choices=False, show_default=False)
        
        if choice == "b":
            break
            
        elif choice == "x":
            target = IntPrompt.ask("Task ID to mark done")
            args = argparse.Namespace(action="done", target_id=str(target))
            command_task(args)
            time.sleep(1.0)
            
        elif choice == "a":
            text = Prompt.ask("Task Description")
            if text:
                budget = Prompt.ask("Time Budget (Optional, e.g. 30m)", default="")
                budget_arg = budget if budget else None
                
                args = argparse.Namespace(action="add", text=[text], budget=budget_arg)
                command_task(args)
                time.sleep(1.0)
                
        elif choice == "d":
            target = IntPrompt.ask("Task ID to delete")
            args = argparse.Namespace(action="delete", target_id=str(target))
            command_task(args)
            time.sleep(1.0)

        elif choice == "c":
            if Confirm.ask("Clear ALL tasks?"):
                # Manual clear logic
                data_manager.config["daily_state"]["tasks"] = [
                    {"id": 1, "text": "", "done": False},
                    {"id": 2, "text": "", "done": False},
                    {"id": 3, "text": "", "done": False}
                ]
                data_manager.save_config()
                console.print("[green]All tasks cleared.[/green]")
                time.sleep(1.0)

def menu_parking_lot():
    while True:
        cls()
        console.print(f"[{T['primary']}]Parking Lot Management[/{T['primary']}]")
        # Show list
        args = argparse.Namespace(action="list")
        command_link(args)
        
        console.print("\n[dim]a: Add | d: Delete | x: Clear All | o: Open | b: Back[/dim]")
        choice = Prompt.ask("Action", choices=["a", "d", "x", "o", "b"], default="b")
        
        if choice == "b":
            break
            
        elif choice == "a":
            url = Prompt.ask("URL to save")
            if url:
                args = argparse.Namespace(action="add", url=url)
                command_link(args)
                time.sleep(1.5)
                
        elif choice == "d":
            target = IntPrompt.ask("Link ID to delete")
            args = argparse.Namespace(action="delete", target_id=str(target))
            command_link(args)
            time.sleep(1.5)

        elif choice == "x":
            # Clear All
            if Confirm.ask("Are you sure you want to DELETE ALL saved links?", default=False):
                data_manager.config["persistent_data"]["parking_lot_links"] = []
                data_manager.save_config()
                console.print("[green]All links cleared.[/green]")
                time.sleep(1.5)

        elif choice == "o":
            target = IntPrompt.ask("Link ID to open")
            args = argparse.Namespace(action="open", target_id=str(target))
            command_link(args)
            time.sleep(1.5)

def menu_note():
    while True:
        cls()
        console.print(f"[{T['primary']}]Brain Dump (Notes)[/{T['primary']}]")
        # Show list
        args = argparse.Namespace(action="show")
        command_note(args)
        
        console.print("\n[dim]a: Add | d: Delete | c: Clear All | b: Back[/dim]")
        choice = Prompt.ask("Action", choices=["a", "d", "c", "b"], default="b", show_choices=False, show_default=False)
        
        if choice == "b":
            break
            
        elif choice == "a":
            text = Prompt.ask("Note content")
            if text:
                args = argparse.Namespace(action="add", text=[text])
                command_note(args)
                time.sleep(1.0)
                
        elif choice == "d":
            target = Prompt.ask("Note IDs to delete (e.g. 1,3 or 1-5)")
            if target:
                args = argparse.Namespace(action="delete", target_id=str(target))
                command_note(args)
                time.sleep(1.0)

        elif choice == "c":
            if Confirm.ask("Clear ALL notes?"):
                args = argparse.Namespace(action="clear")
                command_note(args)
                time.sleep(1.0)

def menu_edit_profile():
    while True:
        cls()
        console.print(f"[{T['primary']}]Edit Profile[/{T['primary']}]")
        p = data_manager.get("user_profile", {})
        
        console.print(f"1. Name: {p.get('name', 'User')}")
        console.print(f"2. City: {p.get('city', 'Unknown')}")
        console.print(f"3. Water Goal: {p.get('daily_water_goal', 2000)}")
        console.print(f"4. Container Size: {p.get('container_size', 250)}")
        console.print(f"5. Caffeine Size: {p.get('caffeine_size', 50)}")
        console.print("b. Back")
        
        choice = Prompt.ask("Select Field to Edit", choices=["1", "2", "3", "4", "5", "b"], default="b")
        
        if choice == "b":
            break
            
        elif choice == "1":
            new_val = Prompt.ask("Enter Name", default=p.get('name', 'User'))
            data_manager.config["user_profile"]["name"] = new_val
            data_manager.save_config()
            
        elif choice == "2":
            new_val = Prompt.ask("Enter City", default=p.get('city', 'New York'))
            data_manager.config["user_profile"]["city"] = new_val
            data_manager.save_config()
            # Force update weather cache? 
            # Ideally modules.weather_api._weather_cache should be cleared or updated, but a restart fixes it.
            console.print("[yellow]Weather will update on next refresh.[/yellow]")
            time.sleep(1.5)

        elif choice == "3":
            new_val = IntPrompt.ask("Enter Daily Water Goal", default=p.get('daily_water_goal', 2000))
            data_manager.config["user_profile"]["daily_water_goal"] = new_val
            data_manager.save_config()

        elif choice == "4":
            new_val = IntPrompt.ask("Enter Container Size", default=p.get('container_size', 250))
            data_manager.config["user_profile"]["container_size"] = new_val
            data_manager.save_config()

        elif choice == "5":
            new_val = IntPrompt.ask("Enter Caffeine Cup Size", default=p.get('caffeine_size', 50))
            data_manager.config["user_profile"]["caffeine_size"] = new_val
            data_manager.save_config()

def menu_more_settings():
    while True:
        cls()
        console.print(f"[{T['primary']}]More Settings[/{T['primary']}]")
        console.print("1. Remove Water (Undo)")
        console.print("2. Clear Water Intake (Reset)")
        console.print("3. Run Initial Setup")
        console.print("4. Toggle History Logging")
        console.print("5. Toggle Eye Strain Reminder")
        console.print("6. Toggle EOD Journal")
        console.print("7. Toggle Clipboard Manager")
        console.print("8. Toggle Audio")
        console.print("9. Toggle Stand Up Reminder")
        console.print("10. Edit Profile")
        console.print("11. Change Color Scheme")
        console.print("b. Back")
        
        choice = Prompt.ask("Select Option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "b"], default="b")
        
        if choice == "b":
            break
            
        elif choice == "1":
            # Undo Water
            args = argparse.Namespace(action="undo")
            command_water(args)
            time.sleep(1.5)
            
        elif choice == "2":
            # Reset Water
            if Confirm.ask("Reset daily water intake to 0?"):
                data_manager.config["daily_state"]["current_water_intake"] = 0
                data_manager.save_config()
                console.print("[green]Water reset.[/green]")
                time.sleep(1.5)
                
        elif choice == "3":
            command_setup(None)
            input("\nPress Enter to return...")

        elif choice == "4":
            curr = data_manager.get("app_settings", {}).get("history_logging", True)
            new_val = not curr
            data_manager.config["app_settings"]["history_logging"] = new_val
            data_manager.save_config()
            status = "ON" if new_val else "OFF"
            console.print(f"[green]History Logging is now {status}[/green]")
            time.sleep(1.5)

        elif choice == "5":
            curr = data_manager.get("app_settings", {}).get("nag_eye_strain", True)
            new_val = not curr
            data_manager.config["app_settings"]["nag_eye_strain"] = new_val
            data_manager.save_config()
            status = "ON" if new_val else "OFF"
            console.print(f"[green]Eye Strain Reminder is now {status}[/green]")
            time.sleep(1.5)

        elif choice == "6":
            curr = data_manager.get("app_settings", {}).get("eod_journal_enabled", False)
            new_val = not curr
            data_manager.config["app_settings"]["eod_journal_enabled"] = new_val
            data_manager.save_config()
            status = "ON" if new_val else "OFF"
            console.print(f"[green]EOD Journal is now {status}[/green]")
            time.sleep(1.5)

        elif choice == "7":
            curr = data_manager.get("app_settings", {}).get("clipboard_enabled", False)
            new_val = not curr
            data_manager.config["app_settings"]["clipboard_enabled"] = new_val
            data_manager.save_config()
            
            status = "ON" if new_val else "OFF"
            console.print(f"[green]Clipboard Manager is now {status}[/green]")
            
            if new_val:
                clipboard_manager.start_monitoring()
            else:
                clipboard_manager.stop_monitoring()
            
            time.sleep(1.5)

        elif choice == "8":
            curr = data_manager.get("app_settings", {}).get("audio_enabled", True)
            new_val = not curr
            data_manager.config["app_settings"]["audio_enabled"] = new_val
            data_manager.save_config()
            status = "ON" if new_val else "OFF"
            console.print(f"[green]Audio is now {status}[/green]")
            time.sleep(1.5)

        elif choice == "9":
            curr = data_manager.get("app_settings", {}).get("nag_stand_up", True)
            new_val = not curr
            data_manager.config["app_settings"]["nag_stand_up"] = new_val
            data_manager.save_config()
            status = "ON" if new_val else "OFF"
            console.print(f"[green]Stand Up Reminder is now {status}[/green]")
            time.sleep(1.5)

        elif choice == "10":
            menu_edit_profile()

        elif choice == "11":
            menu_theme()

def menu_theme():
    """Menu to select and apply themes."""
    from modules.themes import THEMES, get_theme
    global T
    
    while True:
        cls()
        console.print(f"[{T['primary']}]Select Color Scheme[/{T['primary']}]")
        console.print(f"Current: [{T['accent']}]{data_manager.get('app_settings', {}).get('theme', 'default').title()}[/{T['accent']}]\n")
        
        theme_names = list(THEMES.keys())
        for i, name in enumerate(theme_names):
            # Preview using the theme's primary color
            preview_style = THEMES[name]["primary"]
            console.print(f"{i+1}. [{preview_style}]{name.title()}[/{preview_style}]")
            
        console.print("\nb. Back")
        
        choice = Prompt.ask("Select Theme", choices=[str(i+1) for i in range(len(theme_names))] + ["b"], default="b")
        
        if choice == "b":
            break
            
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(theme_names):
                    new_theme = theme_names[idx]
                    data_manager.config["app_settings"]["theme"] = new_theme
                    data_manager.save_config()
                    
                    # Update global T
                    # We need to reach into the global scope or restart
                    # Since we are in the same process, we can update the global T
                    # However, main.py imports T globally. 
                    # We can update the 'T' variable if we use 'global T'
                    # Update global T
                    # We need to reach into the global scope or restart
                    # Since we are in the same process, we can update the global T
                    # However, main.py imports T globally. 
                    T = get_theme(new_theme)
                    
                    console.print(f"[green]Theme changed to {new_theme.title()}![/green]")
                    time.sleep(1.0)
                    pass
            except ValueError:
                pass

def command_habit(args):
    action = args.action
    persistent = data_manager.get("persistent_data", {})
    daily = data_manager.get("daily_state", {})
    
    habits = persistent.get("habits", [])
    habit_status = daily.get("habit_status", {})
    
    if action == "list":
        table = Table(title="Daily Habits", box=box.SIMPLE)
        table.add_column("ID", width=4)
        table.add_column("Status", width=8)
        table.add_column("Habit")
        
        for i, h in enumerate(habits):
            status = "[green]DONE[/green]" if habit_status.get(h, False) else "[red]TODO[/red]"
            table.add_row(str(i+1), status, h)
        console.print(table)
        
    elif action == "add":
        if len(habits) >= 3:
            console.print("[red]Max 3 habits allowed.[/red]")
            return
            
        name = " ".join(args.name)
        if name not in habits:
            habits.append(name)
            habit_status[name] = False # Init for today
            
            data_manager.config["persistent_data"]["habits"] = habits
            data_manager.config["daily_state"]["habit_status"] = habit_status
            data_manager.save_config()
            console.print(f"[green]Habit added:[/green] {name}")
        else:
            console.print("[yellow]Habit already exists.[/yellow]")
            
    elif action == "delete":
        try:
            target_id = int(args.target_id)
            if 1 <= target_id <= len(habits):
                removed = habits.pop(target_id - 1)
                # Cleanup status
                if removed in habit_status:
                    del habit_status[removed]
                    
                data_manager.config["persistent_data"]["habits"] = habits
                data_manager.config["daily_state"]["habit_status"] = habit_status
                data_manager.save_config()
                console.print(f"[yellow]Habit removed:[/yellow] {removed}")
            else:
                console.print(f"[red]ID {target_id} out of range.[/red]")
        except ValueError:
             console.print("[red]Invalid ID.[/red]")

    elif action == "done":
        try:
            target_id = int(args.target_id)
            if 1 <= target_id <= len(habits):
                h_name = habits[target_id - 1]
                habit_status[h_name] = True
                
                data_manager.config["daily_state"]["habit_status"] = habit_status
                data_manager.save_config()
                console.print(f"[green]Good job![/green] Completed: {h_name}")
            else:
                console.print(f"[red]ID {target_id} out of range.[/red]")
        except ValueError:
             console.print("[red]Invalid ID.[/red]")

def menu_habit():
    while True:
        cls()
        console.print("[bold magenta]Habit Tracker[/bold magenta]")
        
        args = argparse.Namespace(action="list")
        command_habit(args)
        
        console.print("\n[dim]x: Mark Done | a: Add | d: Delete | b: Back[/dim]")
        choice = Prompt.ask("Action", choices=["x", "a", "d", "b"], default="b", show_choices=False, show_default=False)
        
        if choice == "b":
            break
            
        elif choice == "x":
            target = IntPrompt.ask("Habit ID to mark done")
            args = argparse.Namespace(action="done", target_id=str(target))
            command_habit(args)
            time.sleep(1.0)
            
        elif choice == "a":
            text = Prompt.ask("New Habit Name")
            if text:
                args = argparse.Namespace(action="add", name=[text])
                command_habit(args)
                time.sleep(1.0)

        elif choice == "d":
            target = IntPrompt.ask("Habit ID to delete")
            args = argparse.Namespace(action="delete", target_id=str(target))
            command_habit(args)
            time.sleep(1.0)

def menu_clipboard():
    while True:
        cls()
        console.print("[bold cyan]Clipboard Manager (Last 10)[/bold cyan]")
        history = clipboard_manager.get_history()
        
        if not history:
            console.print(f"[italic {T['dim']}]History is empty.[/italic {T['dim']}]")
        else:
            table = Table(show_header=True, header_style=T["primary"], box=box.SIMPLE, border_style=T["box"])
            table.add_column("ID", style=T["dim"], width=4)
            table.add_column("Preview", style=T["text"])
            
            for idx, text in enumerate(history):
                # Truncate preview
                preview = text.replace("\n", " ").strip()
                if len(preview) > 60:
                    preview = preview[:57] + "..."
                table.add_row(str(idx+1), preview)
            console.print(table)
            
        console.print("\n[dim]c: Copy ID | d: Delete ID | x: Clear All | b: Back[/dim]")
        choice = Prompt.ask("Action", choices=["c", "d", "x", "b"], default="b")
        
        if choice == "b":
            break
            
        elif choice == "c":
            if not history: 
                continue
            idx = IntPrompt.ask("ID to Copy")
            if 1 <= idx <= len(history):
                clipboard_manager.copy_to_system(idx-1)
                console.print(f"[green]Copied item {idx}[/green]")
                time.sleep(1.0)
            else:
                console.print("[red]Invalid ID[/red]")
                time.sleep(1.0)
                
        elif choice == "d":
            if not history: 
                continue
            idx = IntPrompt.ask("ID to Delete")
            if 1 <= idx <= len(history):
                clipboard_manager.delete_entry(idx-1)
                console.print("[green]Deleted.[/green]")
                time.sleep(1.0)
                
        elif choice == "x":
            if Confirm.ask("Clear entire clipboard history?"):
                clipboard_manager.clear_history()
                console.print("[green]Cleared.[/green]")
                time.sleep(1.0)


def main():
    parser = argparse.ArgumentParser(description="DailyDash CLI")
    subparsers = parser.add_subparsers(dest="command")

    # SETUP Subcommand
    subparsers.add_parser("config", help="Run setup wizard")
    subparsers.add_parser("setup", help="Run setup wizard")

    # HELP Subcommand
    subparsers.add_parser("help", help="Show usage guide")

    # TASK Subcommand
    task_parser = subparsers.add_parser("task", help="Manage Big 3 tasks")
    task_sub = task_parser.add_subparsers(dest="action", required=True)
    task_sub.add_parser("list", help="List tasks")
    
    add_p = task_sub.add_parser("add", help="Add a task")
    add_p.add_argument("text", nargs="+", help="Task description")
    add_p.add_argument("--budget", "-b", help="Time budget (e.g. 30m, 1h)")
    
    done_p = task_sub.add_parser("done", help="Mark task as done")
    done_p.add_argument("target_id", help="Task ID (1-3)")
    
    del_p = task_sub.add_parser("delete", help="Clear a task")
    del_p.add_argument("target_id", help="Task ID (1-3)")

    # WATER Subcommand
    water_parser = subparsers.add_parser("water", help="Track water intake")
    water_sub = water_parser.add_subparsers(dest="action", required=True)
    water_sub.add_parser("show", help="Show current intake")
    water_sub.add_parser("add", help="Add water (default container)")
    water_sub.add_parser("undo", help="Remove last water entry")

    # NOTE Subcommand
    note_parser = subparsers.add_parser("note", help="Brain Dump notes")
    note_sub = note_parser.add_subparsers(dest="action", required=True)
    note_sub.add_parser("show", help="Show notes")
    note_sub.add_parser("clear", help="Clear notes")
    
    note_add = note_sub.add_parser("add", help="Add a note")
    note_add.add_argument("text", nargs="+", help="Note content")
    
    note_del = note_sub.add_parser("delete", help="Delete a specific note")
    note_del.add_argument("target_id", help="Note ID")

    # LINK Subcommand
    link_parser = subparsers.add_parser("link", help="Parking Lot links")
    link_sub = link_parser.add_subparsers(dest="action", required=True)
    link_sub.add_parser("list", help="List links")
    
    link_add = link_sub.add_parser("add", help="Add a link")
    link_add.add_argument("url", help="URL to save")
    
    link_del = link_sub.add_parser("delete", help="Delete a link")
    link_del.add_argument("target_id", help="Link ID")
    
    link_open = link_sub.add_parser("open", help="Open a link")
    link_open.add_argument("target_id", help="Link ID")

    # TIMER Subcommand
    timer_parser = subparsers.add_parser("timer", help="Start focus timer")
    timer_parser.add_argument("duration", type=int, nargs="?", default=25, help="Duration in minutes (default 25)")

    # NOISE Subcommand
    noise_parser = subparsers.add_parser("noise", help="Ambient noise")
    noise_sub = noise_parser.add_subparsers(dest="action", required=True)
    noise_sub.add_parser("play", help="Play brown noise")
    
    # STATUS Subcommand
    subparsers.add_parser("status", help="Show dashboard summary")

    # IF no args --> Interactive Mode
    if len(sys.argv) == 1:
        interactive_mode()
        return

    args = parser.parse_args()

    # Dispatcher
    if args.command in ["help", "--help"]:
        command_help(args)
    elif args.command in ["config", "setup"]:
        command_setup(args)
    elif args.command == "task":
        command_task(args)
    elif args.command == "water":
        command_water(args)
    elif args.command == "note":
        command_note(args)
    elif args.command == "link":
        command_link(args)
    elif args.command == "timer":
        command_timer(args)
    elif args.command == "noise":
        command_noise(args)
    elif args.command == "status":
         command_status(args)
    elif args.command == "clipboard":
         command_clipboard(args)
    else:
        # Default fallback if something weird happens (though argv=1 is caught above)
        command_status(args)

if __name__ == "__main__":
    main()
