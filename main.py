import argparse
import time
import sys
import os

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
    from modules.weather_api import get_weather_for_city
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

def get_system_vitals():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    batt = psutil.sensors_battery()
    batt_str = f"{batt.percent}%" if batt else "AC"
    return f"CPU: {cpu}% | RAM: {mem}% | Disk: {disk}% | PWR: {batt_str}"

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
    header.add_column(justify="left", style="bold magenta")
    header.add_column(justify="right", style="bold yellow")
    header.add_row(f"Hi {name}!", f"DailyDash - {current_date} {current_time}")
    console.print(header)
    
    # 2. Main Table (No Title)
    table = Table(box=box.ROUNDED, expand=True, padding=(1, 1))
    table.add_column("Section", style="cyan", no_wrap=True)
    table.add_column("Content", style="white")

    # Weather
    table.add_row("Weather", weather_info)
    
    # System
    table.add_row("System", f"[dim]{vitals}[/dim]")
    
    # Tasks
    task_str = ""
    for t in tasks:
        icon = "[green]✔[/green]" if t["done"] else "[red]☐[/red]"
        txt = t["text"] if t["text"] else "[dim]Empty[/dim]"
        task_str += f"{icon} {txt}\n"
    table.add_row("Big 3 Tasks", task_str.strip())
    
    # Health (Water + Caffeine on same line)
    water_percent = min(100, int((water / goal) * 100))
    water_color = "blue" if water_percent < 100 else "green"
    
    health_str = f"💧 [{water_color}]{water}ml[/] / {goal}ml ({water_percent}%)"
    if caffeine > 0:
         health_str += f"  |  ☕ [yellow]{caffeine}mg[/yellow]"
    else:
         health_str += f"  |  ☕ [dim]{caffeine}mg[/dim]"
    
    table.add_row("Health", health_str)

    # Notes (Full Content)
    note_content = notes.strip() if notes else "[dim]No notes[/dim]"
    table.add_row("Brain Dump", note_content)

    # Links (Refined Title)
    link_str = ""
    for i, link in enumerate(links):
        link_str += f"{i+1}. [link={link}]{link}[/link]\n"
    link_str = link_str.strip() if link_str else "[dim]No links[/dim]"
    table.add_row("Saved URLs", link_str)

    console.print(table)
    
    # 3. Quote (Bottom)
    quote = random.choice(QUOTES)
    console.print(Align.center(f"[italic dim]\"{quote}\"[/italic dim]"), style="italic cyan")
    # Removed explicit spacer to reduce gap

    # Tooltips / Usage Footer
    if show_hints:
        tips = """[dim]Try these commands:[/dim]
[cyan]task add "Todo"[/cyan]  |  [cyan]water add[/cyan]  |  [cyan]coffee add[/cyan]  |  [cyan]timer 25[/cyan]
[dim]Run 'python main.py help' for a full guide.[/dim]"""
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
    if Confirm.ask("[bold red]End Day & Reset?[/bold red] This will save stats and clear daily progress."):
        # Check setting
        logging_enabled = data_manager.get("app_settings", {}).get("history_logging", True)
        if logging_enabled:
            data_manager.log_daily_history()
            console.print("[dim]History logged to CSV.[/dim]")
            
        data_manager.confirm_new_day()
        console.print("[green]Day reset. Good job today![/green]")
        time.sleep(2.0)

# ... (Existing interactive_mode and main dispatcher updates)

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
            console.print("\n[bold cyan]Interactive Menu[/bold cyan]")
            console.print("[dim]w: Water | k: Coffee | t: Task | c: Timer | b: Brain Dump | p: Saved URLs | e: End Day | m: Menu | q: Quit[/dim]") # Added k and e
            
            choice = Prompt.ask("Command", choices=["w", "k", "t", "c", "b", "p", "e", "m", "q"], default="q", show_choices=False, show_default=False)
            
            if choice == "q":
                console.print("Bye!")
                break
                
            elif choice == "w":
                # Add Water (default amount)
                args = argparse.Namespace(action="add")
                command_water(args)
                time.sleep(1.0) # Faster
                
            elif choice == "k":
                # Coffee
                args = argparse.Namespace(action="add")
                command_coffee(args)
                time.sleep(1.0)
                
            elif choice == "e":
                # End Day
                command_end_day(None)
                
            elif choice == "t":
                # Task Menu
                menu_task()
            
            elif choice == "c":
                # Timer
                mins = IntPrompt.ask("Duration (minutes)", default=25)
                args = argparse.Namespace(duration=mins)
                command_timer(args)
                input("\nPress Enter to return...")
                
            elif choice == "b":
                # Brain Dump
                text = Prompt.ask("Quick Note")
                if text:
                    args = argparse.Namespace(action="add", text=[text])
                    command_note(args)
                    time.sleep(1.0)
            
            elif choice == "p":
                menu_parking_lot()
            
            elif choice == "m":
                menu_more_settings()
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting Interactive Mode...[/yellow]")
            break

def main():
    parser = argparse.ArgumentParser(description="DailyDash CLI")
    subparsers = parser.add_subparsers(dest="command")

    # ... (Add coffee parser)
    
    # COFFEE Subcommand
    coffee_parser = subparsers.add_parser("coffee", help="Track caffeine")
    coffee_sub = coffee_parser.add_subparsers(dest="action", required=True)
    coffee_sub.add_parser("add", help="Add cup (95mg)")
    coffee_sub.add_parser("undo", help="Remove cup")
    
    # END DAY Subcommand
    subparsers.add_parser("end", help="End day and log stats")

    # ... (Rest of parsers)

    if len(sys.argv) == 1:
        interactive_mode()
        return

    args = parser.parse_args()

    # Dispatcher
    if args.command == "coffee":
        command_coffee(args)
    elif args.command == "end":
        command_end_day(args)
    # ... (Rest of dispatcher)


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
    console.print(Panel(help_text, title="Help & Usage", border_style="green"))

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

    # Save
    data_manager.config["user_profile"]["name"] = name
    data_manager.config["user_profile"]["unit_system"] = unit_system
    data_manager.config["user_profile"]["city"] = city
    data_manager.config["user_profile"]["container_size"] = container
    data_manager.config["user_profile"]["daily_water_goal"] = goal
    data_manager.config["user_profile"]["caffeine_size"] = caffeine_size
    data_manager.config["app_settings"]["history_logging"] = history_logging
    
    data_manager.config["setup_complete"] = True
    
    data_manager.save_config()
    console.print("[bold green]Setup Complete![/bold green] Run [cyan]python main.py[/cyan] to see your dashboard.")

def command_task(args):
    action = args.action
    daily_state = data_manager.get("daily_state", {})
    tasks = daily_state.get("tasks", [])

    if action == "list":
        table = Table(title="Current Tasks", box=box.SIMPLE)
        table.add_column("ID", style="magenta", width=4)
        table.add_column("Status", width=8)
        table.add_column("Description")
        
        for t in tasks:
            status = "[green]DONE[/green]" if t["done"] else "[red]TODO[/red]"
            table.add_row(str(t["id"]), status, t["text"] or "[dim]Empty[/dim]")
        console.print(table)
        
    elif action == "add":
        text = " ".join(args.text)
        found = False
        for t in tasks:
            if not t["text"]:
                t["text"] = text
                t["done"] = False
                found = True
                console.print(f"[green]Added task to slot {t['id']}:[/green] {text}")
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
    current_notes = persistent.get("brain_dump_content", "")

    if action == "show":
        panel = Panel(current_notes if current_notes else "[dim]No notes found.[/dim]", title="Brain Dump", border_style="yellow")
        console.print(panel)
        
    elif action == "add":
        new_text = " ".join(args.text)
        if current_notes:
            current_notes += f"\n- {new_text}"
        else:
            current_notes = f"- {new_text}"
            
        data_manager.config["persistent_data"]["brain_dump_content"] = current_notes
        data_manager.save_config()
        console.print("[green]Note added![/green]")
        
    elif action == "clear":
        data_manager.config["persistent_data"]["brain_dump_content"] = ""
        data_manager.save_config()
        console.print("[yellow]Brain dump cleared.[/yellow]")

def command_link(args):
    action = args.action
    persistent = data_manager.get("persistent_data", {})
    links = persistent.get("parking_lot_links", [])

    if action == "list":
        table = Table(title="Parking Lot (Saved URLs)", box=box.SIMPLE)
        table.add_column("ID", style="magenta", width=4)
        table.add_column("URL", style="blue")
        
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
    Blocking focus timer.
    """
    duration_min = args.duration
    total_seconds = duration_min * 60
    
    console.print(f"[bold green]Starting Focus Timer for {duration_min} minutes...[/bold green]")
    try:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("[cyan]Focusing...", total=total_seconds)
            
            while not progress.finished:
                time.sleep(1)
                progress.update(task, advance=1)
                
        console.print("[bold green]Timer Complete! Take a break.[/bold green]")
        # Play a beep?
        sys.stdout.write('\a')
        sys.stdout.flush()
        
    except KeyboardInterrupt:
        console.print("\n[red]Timer Cancelled.[/red]")

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



def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

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
            console.print("[bold cyan]Interactive Menu[/bold cyan]")
            console.print("[dim]w: Water | k: Coffee | t: Task | c: Timer | b: Brain Dump | p: Saved URLs | e: End Day | m: Menu | q: Quit[/dim]")
            
            choice = Prompt.ask("Command", choices=["w", "k", "t", "c", "b", "p", "e", "m", "q"], default="q", show_choices=False, show_default=False)
            
            if choice == "q":
                console.print("Bye!")
                break
                
            elif choice == "w":
                # Add Water (default amount)
                args = argparse.Namespace(action="add")
                command_water(args)
                time.sleep(1.0)
                
            elif choice == "k":
                # Coffee
                args = argparse.Namespace(action="add")
                command_coffee(args)
                time.sleep(1.0)
                
            elif choice == "e":
                # End Day
                command_end_day(None)
                
            elif choice == "t":
                # Task Menu
                menu_task()
            
            elif choice == "c":
                # Timer
                mins = IntPrompt.ask("Duration (minutes)", default=25)
                args = argparse.Namespace(duration=mins)
                command_timer(args)
                input("\nPress Enter to return...")
                
            elif choice == "b":
                # Brain Dump
                text = Prompt.ask("Quick Note")
                if text:
                    args = argparse.Namespace(action="add", text=[text])
                    command_note(args)
                    time.sleep(1.0)
            
            elif choice == "p":
                menu_parking_lot()
            
            elif choice == "m":
                menu_more_settings()
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting Interactive Mode...[/yellow]")
            break

def menu_task():
    while True:
        cls()
        console.print("[bold magenta]Task Management[/bold magenta]")
        # Show list
        args = argparse.Namespace(action="list")
        command_task(args)
        
        console.print("\n[dim]a: Add | d: Delete | c: Clear All | b: Back[/dim]")
        choice = Prompt.ask("Action", choices=["a", "d", "c", "b"], default="b", show_choices=False, show_default=False)
        
        if choice == "b":
            break
            
        elif choice == "a":
            text = Prompt.ask("Task Description")
            if text:
                args = argparse.Namespace(action="add", text=[text])
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
        console.print("[bold magenta]Parking Lot Management[/bold magenta]")
        # Show list
        args = argparse.Namespace(action="list")
        command_link(args)
        
        console.print("\n[dim]a: Add | d: Delete | o: Open | b: Back[/dim]")
        choice = Prompt.ask("Action", choices=["a", "d", "o", "b"], default="b")
        
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

        elif choice == "o":
            target = IntPrompt.ask("Link ID to open")
            args = argparse.Namespace(action="open", target_id=str(target))
            command_link(args)
            time.sleep(1.5)

def menu_more_settings():
    while True:
        cls()
        console.print("[bold cyan]More Settings[/bold cyan]")
        console.print("1. Remove Water (Undo)")
        console.print("2. Clear Water Intake (Reset)")
        console.print("3. Clear Brain Dump")
        console.print("4. Clear Parking Lot")
        console.print("5. Run Initial Setup")
        console.print("6. Toggle History Logging")
        console.print("7. Set Caffeine Size")
        console.print("b. Back")
        
        choice = Prompt.ask("Select Option", choices=["1", "2", "3", "4", "5", "6", "7", "b"], default="b")
        
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
            # Clear Notes
            if Confirm.ask("Clear all notes?"):
                args = argparse.Namespace(action="clear")
                command_note(args)
                time.sleep(1.5)
                
        elif choice == "4":
            # Clear Parking Lot
            if Confirm.ask("Delete ALL saved links?"):
                data_manager.config["persistent_data"]["parking_lot_links"] = []
                data_manager.save_config()
                console.print("[green]Parking lot cleared.[/green]")
                time.sleep(1.5)

        elif choice == "5":
            command_setup(None)
            input("\nPress Enter to return...")

        elif choice == "6":
            curr = data_manager.get("app_settings", {}).get("history_logging", True)
            new_val = not curr
            data_manager.config["app_settings"]["history_logging"] = new_val
            data_manager.save_config()
            status = "ON" if new_val else "OFF"
            console.print(f"[green]History Logging is now {status}[/green]")
            time.sleep(1.5)

        elif choice == "7":
            curr = data_manager.get("user_profile", {}).get("caffeine_size", 50)
            console.print(f"Current Size: {curr}mg")
            new_val = IntPrompt.ask("New Caffeine Size (mg)", default=curr)
            data_manager.config["user_profile"]["caffeine_size"] = new_val
            data_manager.save_config()
            console.print(f"[green]Caffeine size updated to {new_val}mg[/green]")
            time.sleep(1.5)


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
    else:
        # Default fallback if something weird happens (though argv=1 is caught above)
        command_status(args)

if __name__ == "__main__":
    main()
