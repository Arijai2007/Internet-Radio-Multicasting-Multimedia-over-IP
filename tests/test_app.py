"""Application startup and station-discovery regression tests (no playback)."""
from dataclasses import replace
import tkinter as tk
from radio.app import RadioApp


def test_remote_refresh_preserves_local_broadcast_configuration(tk_root):
    root = tk.Toplevel(tk_root)
    root.withdraw()
    app = RadioApp(root, "127.0.0.1")
    try:
        original = list(app.local_stations)
        remote = [replace(original[0], name="Remote only", source="missing-on-this-computer.mp4")]
        app.results.put((True, remote))
        app.tick()
        assert app.stations == remote
        assert app.local_stations == original
        assert app.interface.get() == "127.0.0.1"
    finally:
        app.close()
