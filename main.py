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
    batt = psutil.sensors_battery()
    batt_str = f"{batt.percent}%" if batt else "AC"
    return f"CPU: {cpu}% | RAM: {mem}% | PWR: {batt_str}"

def command_status(args):
    """
    Displays the 'Head-Up Display' summary:
    - Weather & Vitals
    - Big 3 Tasks
    - Water Intake
    """
    # 1. Header Info
    user_profile = data_manager.get("user_profile", {})
    city = user_profile.get("city", "Unknown")
    units = user_profile.get("unit_system", "metric")
    weather_info = get_weather_for_city(city, units)
    vitals = get_system_vitals()
    
    # 2. Daily State
    daily_state = data_manager.get("daily_state", {})
    tasks = daily_state.get("tasks", [])
    water = daily_state.get("current_water_intake", 0)
    goal = user_profile.get("daily_water_goal", 2000)
    
    # 3. Persistent Data
    persistent = data_manager.get("persistent_data", {})
    notes = persistent.get("brain_dump_content", "")
    links = persistent.get("parking_lot_links", [])

    # --- UI Construction ---
    current_time = time.strftime('%H:%M')
    table = Table(title=f"DailyDash Status - [bold yellow]{current_time}[/]", box=box.ROUNDED, expand=True)
    table.add_column("Section", style="cyan", no_wrap=True)
    table.add_column("Content", style="white")

    # Weather & System
    table.add_row("Environment", f"{weather_info}\n[dim]{vitals}[/dim]")
    
    # Tasks
    task_str = ""
    for t in tasks:
        icon = "[green]✔[/green]" if t["done"] else "[red]☐[/red]"
        txt = t["text"] if t["text"] else "[dim]Empty[/dim]"
        task_str += f"{icon} {txt}\n"
    table.add_row("Big 3 Tasks", task_str.strip())
    
    # Water
    water_percent = min(100, int((water / goal) * 100))
    water_color = "blue" if water_percent < 100 else "green"
    table.add_row("Hydration", f"[{water_color}]{water}ml[/] / {goal}ml ({water_percent}%)")

    # Notes (Brain Dump)
    note_preview = notes.strip() if notes else "[dim]No notes[/dim]"
    if len(note_preview) > 100: note_preview = note_preview[:97] + "..."
    table.add_row("Brain Dump", note_preview)

    # Links (Parking Lot)
    link_str = ""
    for i, link in enumerate(links):
        link_str += f"{i+1}. [link={link}]{link}[/link]\n"
    link_str = link_str.strip() if link_str else "[dim]No links[/dim]"
    table.add_row("Parking Lot", link_str)

    console.print(table)
    
    # Tooltips / Usage Footer
    tips = """[dim]Try these commands:[/dim]
[cyan]task add "Todo"[/cyan]  |  [cyan]water add[/cyan]  |  [cyan]timer 25[/cyan]  |  [cyan]note add "Idea"[/cyan]
[dim]Run 'python main.py help' for a full guide.[/dim]"""
    console.print(Align.center(tips))

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

    # Save
    data_manager.config["user_profile"]["unit_system"] = unit_system
    data_manager.config["user_profile"]["city"] = city
    data_manager.config["user_profile"]["container_size"] = container
    data_manager.config["user_profile"]["daily_water_goal"] = goal
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
        # Default
        command_status(args)

if __name__ == "__main__":
    main()
