
THEMES = {
    "default": {
        "primary": "bold magenta",
        "secondary": "bold cyan",
        "accent": "bold yellow",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "text": "white",
        "dim": "dim",
        "box": "cyan"
    },
    "ocean": {
        "primary": "bold #005F87",  # Deep Blue
        "secondary": "bold #00AFFF", # Bright Blue
        "accent": "bold #FFFFFF",    # White
        "success": "#00D700",        # Green
        "warning": "#FFAF00",        # Orange/Yellow
        "error": "#D70000",          # Red
        "text": "#87D7FF",           # Light Blue
        "dim": "dim #005F87",
        "box": "#0087FF"
    },
    "forest": {
        "primary": "bold #005F00",  # Deep Green
        "secondary": "bold #87D700", # Bright Lime
        "accent": "bold #FFFFFF",    # White
        "success": "#5FD700",        # Green
        "warning": "#D7D700",        # Yellow
        "error": "#AF0000",          # Red
        "text": "#D7FFD7",           # Pale Green
        "dim": "dim #005F00",
        "box": "#5F8700"
    },
    "sunset": {
        "primary": "bold #D7005F",  # Deep Red/Pink
        "secondary": "bold #FF8700", # Orange
        "accent": "bold #FFFF00",    # Yellow
        "success": "#87D700",        # Green
        "warning": "#FFAF00",        # Orange
        "error": "#D70000",          # Red
        "text": "#FFD7AF",           # Pale Orange
        "dim": "dim #870000",
        "box": "#D75F00"
    },
    "monochrome": {
        "primary": "bold #FFFFFF",
        "secondary": "#E4E4E4",
        "accent": "bold #FFFFFF",
        "success": "#FFFFFF",
        "warning": "#E4E4E4",
        "error": "#FFFFFF",
        "text": "#D0D0D0",
        "dim": "dim #808080",
        "box": "#FFFFFF"
    }
}

def get_theme(theme_name):
    return THEMES.get(theme_name, THEMES['default'])
