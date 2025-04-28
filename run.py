import sys
import os

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# run.py
from gui.main_window import main_window

if __name__ == "__main__":
    app = main_window()
    # Removed app.run() as main_window already starts the GUI loop.
