# =========================================
# SARA POS - Official Theme
# =========================================

# COLORS

PRIMARY_COLOR = "#4A6A92"

SIDEBAR_COLOR = "#28364A"

SECONDARY_COLOR = "#8EA3BB"

BACKGROUND_COLOR = "#DFE6EE"

SUCCESS_COLOR = "#8B9B8B"

TEXT_DARK = "#1E1E1E"

TEXT_LIGHT = "#FFFFFF"


# =========================================
# GLOBAL WINDOW STYLE
# =========================================

WINDOW_STYLE = f"""
QWidget {{
    background-color: {BACKGROUND_COLOR};
    color: {TEXT_DARK};
    font-size: 14px;
    font-family: Arial;
}}
"""


# =========================================
# INPUT STYLE
# =========================================

INPUT_STYLE = f"""
QLineEdit {{
    padding: 10px;
    border-radius: 8px;
    border: 1px solid {SECONDARY_COLOR};
    background-color: white;
    color: {TEXT_DARK};
}}

QLineEdit:focus {{
    border: 2px solid {PRIMARY_COLOR};
}}
"""


# =========================================
# BUTTON STYLE
# =========================================

BUTTON_STYLE = f"""
QPushButton {{
    background-color: {PRIMARY_COLOR};
    color: white;
    border-radius: 8px;
    padding: 12px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {SIDEBAR_COLOR};
}}
"""
