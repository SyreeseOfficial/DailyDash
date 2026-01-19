
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
    },
    "dracula": {
        "primary": "bold #BD93F9",  # Purple
        "secondary": "bold #8BE9FD", # Cyan
        "accent": "bold #FF79C6",    # Pink
        "success": "#50FA7B",        # Green
        "warning": "#F1FA8C",        # Yellow
        "error": "#FF5555",          # Red
        "text": "#F8F8F2",           # Foreground
        "dim": "dim #6272A4",        # Comment
        "box": "#BD93F9"             # Purple border
    },
    "solarized": {
        "primary": "bold #B58900",   # Yellow
        "secondary": "bold #2AA198", # Cyan
        "accent": "bold #CB4B16",    # Orange
        "success": "#859900",        # Green
        "warning": "#B58900",        # Yellow
        "error": "#DC322F",          # Red
        "text": "#93A1A1",           # Base1
        "dim": "dim #586E75",        # Base01
        "box": "#2AA198"             # Cyan border
    },
    "cyberpunk": { 
        "primary": "bold #FCEE09",   # Neon Yellow
        "secondary": "bold #00E5FF", # Neon Cyan
        "accent": "bold #FF0099",    # Neon Pink
        "success": "#00FF9C",        # Neon Green
        "warning": "#FCEE09",        # Neon Yellow
        "error": "#FF3333",          # Bright Red
        "text": "#E0E0E0",           # Off white
        "dim": "dim #707070",
        "box": "#FF0099"             # Neon Pink border
    },
    "gruvbox": {
        "primary": "bold #fabd2f",   # Yellow
        "secondary": "bold #83a598", # Blue
        "accent": "bold #fe8019",    # Orange
        "success": "#b8bb26",        # Green
        "warning": "#fabd2f",        # Yellow
        "error": "#fb4934",          # Red
        "text": "#ebdbb2",           # Light BG
        "dim": "dim #928374",        # Gray
        "box": "#fabd2f"             # Yellow border
    },
    "nord": {
        "primary": "bold #88C0D0",   # Frost Blue
        "secondary": "bold #81A1C1", # Frost Blue darker
        "accent": "bold #EBCB8B",    # Aurora Yellow
        "success": "#A3BE8C",        # Aurora Green
        "warning": "#EBCB8B",        # Aurora Yellow
        "error": "#BF616A",          # Aurora Red
        "text": "#D8DEE9",           # Snow Storm
        "dim": "dim #4C566A",        # Polar Night
        "box": "#88C0D0"             # Frost Blue
    },
    "tokyo_night": {
        "primary": "bold #7aa2f7",   # Blue
        "secondary": "bold #bb9af7", # Magenta/Purple
        "accent": "bold #e0af68",    # Orange
        "success": "#9ece6a",        # Green
        "warning": "#e0af68",        # Orange
        "error": "#f7768e",          # Red
        "text": "#c0caf5",           # FG
        "dim": "dim #565f89",        # Terminal Black light
        "box": "#7aa2f7"             # Blue
    }
}

def get_theme(theme_name):
    return THEMES.get(theme_name, THEMES['default'])
