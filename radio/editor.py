"""Local channel management; changes go through the application's save callback."""
from dataclasses import asdict
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .core import ROOT, Station, parse_stations


class ChannelEditor(tk.Toplevel):
    def __init__(self, parent, stations, apply):
        super().__init__(parent)
        self.title("Manage local channels")
        self.geometry("760x610")
        self.transient(parent)
        self.apply = apply
        self.stations = list(stations)
        self.editing = None
        panel = ttk.Frame(self, padding=18)
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text="Local channels", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(panel, text="Saved changes apply to this computer. Restart broadcasting after editing.").pack(anchor="w", pady=6)
        self.tree = ttk.Treeview(panel, columns=("name", "address"), show="headings", height=5)
        self.tree.heading("name", text="Channel")
        self.tree.heading("address", text="Multicast address / port")
        self.tree.pack(fill="x", pady=8)
        self.tree.bind("<<TreeviewSelect>>", self.select)
        form = ttk.Frame(panel)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        self.fields = {}
        for row, (key, label) in enumerate([( "id", "Channel ID"), ("name", "Name"),
                ("description", "Description"), ("group", "Multicast IPv4"),
                ("port", "UDP port"), ("source", "Media file (or demo)")]):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=6, padx=(0,12))
            variable = tk.StringVar()
            self.fields[key] = variable
            ttk.Entry(form, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=6)
        ttk.Button(form, text="Choose file…", command=self.browse).grid(row=5, column=2, padx=6)
        buttons = ttk.Frame(panel)
        buttons.pack(fill="x", pady=18)
        for label, action in [("New channel", self.new), ("Save channel", self.save),
                              ("Remove channel", self.remove), ("Close", self.destroy)]:
            ttk.Button(buttons, text=label, command=action).pack(side="left", padx=(0,6))
        self.refresh()
        self.new()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for index, station in enumerate(self.stations):
            self.tree.insert("", "end", iid=str(index), values=(station.name, f"{station.group}:{station.port}"))

    def select(self, _=None):
        selected = self.tree.selection()
        if selected:
            self.editing = int(selected[0])
            for key, value in asdict(self.stations[self.editing]).items():
                self.fields[key].set(value)

    def new(self):
        self.editing = None
        self.tree.selection_remove(*self.tree.selection())
        number = max(s.id for s in self.stations) + 1
        used = {(s.group, s.port) for s in self.stations}
        port = 5433
        while ("239.192.4.1", port) in used:
            port += 1
        values = dict(id=number, name="New channel", description="", group="239.192.4.1", port=port, source="demo")
        for key, value in values.items():
            self.fields[key].set(value)

    def browse(self):
        path = filedialog.askopenfilename(parent=self, title="Choose a song or video", filetypes=[
            ("Audio and video", "*.mp3 *.wav *.aac *.flac *.ogg *.m4a *.mp4 *.mkv *.mov *.webm"), ("All files", "*.*")])
        if path:
            self.fields["source"].set(path)

    def save(self):
        try:
            values = {key: variable.get().strip() for key, variable in self.fields.items()}
            values["id"], values["port"] = int(values["id"]), int(values["port"])
            station = Station(**values)
            if station.source != "demo":
                path = Path(station.source).expanduser()
                if not path.is_absolute():
                    path = ROOT / path
                if not path.is_file():
                    raise ValueError("Choose an existing audio or video file")
            updated = list(self.stations)
            if self.editing is None:
                updated.append(station)
            else:
                updated[self.editing] = station
            parse_stations([asdict(s) for s in updated])
            if self.apply(updated):
                self.stations = updated
                self.refresh()
                self.tree.selection_set(str(updated.index(station)))
        except (ValueError, OSError) as exc:
            messagebox.showerror("Cannot save channel", str(exc), parent=self)

    def remove(self):
        if self.editing is None:
            return
        if len(self.stations) == 1:
            messagebox.showerror("Cannot remove channel", "Keep at least one channel.", parent=self)
            return
        if not messagebox.askyesno("Remove channel", "Remove this channel from your local configuration? The media file will be kept.", parent=self):
            return
        updated = [s for i, s in enumerate(self.stations) if i != self.editing]
        try:
            if self.apply(updated):
                self.stations = updated
                self.refresh()
                self.new()
        except (ValueError, OSError) as exc:
            messagebox.showerror("Cannot remove channel", str(exc), parent=self)
