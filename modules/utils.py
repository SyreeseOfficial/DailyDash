import os
import psutil

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_system_vitals():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    # disk = psutil.disk_usage('/').percent
    batt = psutil.sensors_battery()
    batt_str = f"{batt.percent}%" if batt else "AC"
    return f"CPU: {cpu}% | RAM: {mem}% | PWR: {batt_str}"
