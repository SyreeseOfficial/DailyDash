from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

# 1. Current Approach (Raw Unicode + VS16)
weather_info_raw = "New York: \u2600\ufe0f  -1.1°C | \U0001F4A7\ufe0f 94% | \U0001F4A8\ufe0f 23.3km/h"
# 2. Rich Markup Approach
weather_info_markup = "New York: :sun: -1.1°C | :droplet: 94% | :dash: 23.3km/h"

def draw_test():
    console.print("[bold]Test 1: Raw Unicode + VS16[/bold]")
    table = Table(box=box.ROUNDED, expand=True, padding=(0, 1))
    table.add_column("Section", no_wrap=True)
    table.add_column("Content")
    table.add_row("Weather", weather_info_raw)
    console.print(table)
    
    console.print("\n[bold]Test 2: Rich Markup (:emoji:)[/bold]")
    table2 = Table(box=box.ROUNDED, expand=True, padding=(0, 1))
    table2.add_column("Section", no_wrap=True)
    table2.add_column("Content")
    table2.add_row("Weather", weather_info_markup)
    console.print(table2)

if __name__ == "__main__":
    draw_test()
