import tkinter as tk
import pytest


@pytest.fixture(scope="session")
def tk_root():
    """Keep one Tk interpreter for the GUI tests, as in the real app."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()
