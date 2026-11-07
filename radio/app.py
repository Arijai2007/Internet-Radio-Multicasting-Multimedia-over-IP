"""Native Python desktop UI. Networking stays off the Tk event thread."""
import ipaddress
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from .core import Broadcaster, DirectoryServer, discover, load_stations
from .player import create_vlc


class RadioApp:
    def __init__(self, root):
        self.root = root
        self.stations = load_stations()
        self.broadcaster = Broadcaster()
        self.directory = None
        self.instance = self.player = None
        self.current = None
        self.results = queue.Queue()
        self.cleanup_threads = []
        self.closing = False
        root.title("Airwave | Multicast TV & Radio")
        root.geometry("1180x760")
        root.minsize(900, 640)
        root.configure(bg="#0c1220")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0c1220")
        style.configure("TLabel", background="#0c1220", foreground="#e7edf9", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=9)
        style.configure("Title.TLabel", font=("Segoe UI", 25, "bold"))
        style.configure("Sub.TLabel", foreground="#8fa4c2")
        shell = ttk.Frame(root, padding=24)
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="AIRWAVE", style="Title.TLabel").pack(anchor="w")
        ttk.Label(shell, text="Multicast television & radio  /  Computer Networks Lab", style="Sub.TLabel").pack(anchor="w", pady=(0, 18))
        network = ttk.Frame(shell)
        network.pack(fill="x", pady=(0, 16))
        self.host = tk.StringVar(value="127.0.0.1")
        self.interface = tk.StringVar()
        ttk.Label(network, text="Directory host").pack(side="left")
        ttk.Entry(network, textvariable=self.host, width=18).pack(side="left", padx=8)
        self.refresh = ttk.Button(network, text="Refresh stations", command=self.refresh_stations)
        self.refresh.pack(side="left")
        ttk.Label(network, text="Local IPv4 (optional)").pack(side="left", padx=(20, 8))
        ttk.Entry(network, textvariable=self.interface, width=18).pack(side="left")
        body = ttk.Frame(shell)
        body.pack(fill="both", expand=True)
        sidebar = ttk.Frame(body, width=235)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        ttk.Label(sidebar, text="STATION LIBRARY", style="Sub.TLabel").pack(anchor="w", pady=(0, 10))
        self.listbox = tk.Listbox(sidebar, bg="#172238", fg="#eef4ff", selectbackground="#2563eb", font=("Segoe UI", 12), relief="flat", borderwidth=0, width=23, height=12, exportselection=False)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", lambda _: self.play())
        ttk.Button(sidebar, text="Play selected station", command=self.play).pack(fill="x", pady=12)
        ttk.Label(sidebar, text="BROADCAST STUDIO", style="Sub.TLabel").pack(anchor="w", pady=(20, 8))
        ttk.Button(sidebar, text="Start local broadcast", command=self.start_broadcast).pack(fill="x", pady=4)
        ttk.Button(sidebar, text="Stop local broadcast", command=self.stop_broadcast).pack(fill="x", pady=4)
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)
        self.now = tk.StringVar(value="Ready to tune in")
        ttk.Label(right, textvariable=self.now, font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(0, 10))
        self.video = tk.Frame(right, bg="#000000")
        self.video.pack(fill="both", expand=True)
        controls = ttk.Frame(right)
        controls.pack(fill="x", pady=12)
        ttk.Button(controls, text="Pause / Resume", command=self.pause).pack(side="left")
        ttk.Button(controls, text="Stop", command=self.stop).pack(side="left", padx=8)
        self.muted = tk.BooleanVar(value=False)
        ttk.Checkbutton(controls, text="Mute", variable=self.muted, command=self.set_volume).pack(side="left")
        ttk.Label(controls, text="Volume").pack(side="left", padx=(18, 6))
        self.volume = tk.DoubleVar(value=80)
        ttk.Scale(controls, from_=0, to=100, variable=self.volume, command=lambda _: self.set_volume()).pack(side="left", fill="x", expand=True)
        self.detail = tk.StringVar(value="Select a channel, or start a local broadcast to try both test stations.")
        ttk.Label(right, textvariable=self.detail, wraplength=650, style="Sub.TLabel").pack(anchor="w")
        self.status = tk.StringVar(value="Idle • Audio enabled • Live MPEG-TS / UDP multicast")
        ttk.Label(shell, textvariable=self.status, style="Sub.TLabel").pack(anchor="w", pady=(18, 0))
        self.render_stations()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(500, self.tick)

    def render_stations(self):
        self.listbox.delete(0, "end")
        for station in self.stations:
            self.listbox.insert("end", f"{station.id:02}   {station.name}")
        if self.stations:
            self.listbox.selection_set(0)

    def refresh_stations(self):
        host = self.host.get().strip()
        self.refresh.configure(state="disabled")
        self.status.set("Connecting to station directory…")
        def work():
            try:
                self.results.put((True, discover(host)))
            except Exception as exc:
                self.results.put((False, str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def play(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        try:
            interface = self.interface.get().strip()
            if interface:
                ipaddress.IPv4Address(interface)
            self.stop()
            self.instance = create_vlc(interface)
            self.player = self.instance.media_player_new()
            self.root.update_idletasks()
            if sys.platform == "win32":
                self.player.set_hwnd(self.video.winfo_id())
            elif sys.platform == "darwin":
                raise RuntimeError("Embedded playback currently supports Windows and Linux. Use VLC on macOS.")
            else:
                self.player.set_xwindow(self.video.winfo_id())
            station = self.stations[selected[0]]
            media = self.instance.media_new(f"udp://@{station.group}:{station.port}")
            self.player.set_media(media)
            media.release()
            self.set_volume()
            if self.player.play() == -1:
                raise RuntimeError("Could not start VLC playback")
            self.current = station
            self.now.set(station.name)
            self.detail.set(f"{station.description}\n{station.group}:{station.port} • H.264 + AAC • Live playback")
            self.status.set("Joining multicast group…")
        except Exception as exc:
            messagebox.showerror("Playback", str(exc))

    def pause(self):
        if self.player:
            self.player.pause()

    def stop(self):
        player, instance = self.player, self.instance
        self.player = self.instance = None
        if player or instance:
            def cleanup():
                # VLC may wait for native window messages during stop. Keep
                # Tk processing those messages instead of blocking its thread.
                if player:
                    player.stop()
                    player.release()
                if instance:
                    instance.release()
            worker = threading.Thread(target=cleanup, daemon=True)
            self.cleanup_threads = [t for t in self.cleanup_threads if t.is_alive()]
            self.cleanup_threads.append(worker)
            worker.start()
        self.current = None
        self.now.set("Ready to tune in")
        self.status.set("Stopped")

    def set_volume(self):
        if self.player:
            self.player.audio_set_volume(round(self.volume.get()))
            self.player.audio_set_mute(self.muted.get())

    def start_broadcast(self):
        try:
            interface = self.interface.get().strip()
            if interface:
                ipaddress.IPv4Address(interface)
            if self.directory:
                return
            self.directory = DirectoryServer(("0.0.0.0", 5432), self.stations)
            self.directory.start()
            for station in self.stations:
                self.broadcaster.start(station, interface)
            self.status.set("Local stations broadcasting. Select a station and press Play.")
        except Exception as exc:
            self.stop_broadcast()
            messagebox.showerror("Broadcast", str(exc))

    def stop_broadcast(self):
        self.broadcaster.stop()
        if self.directory:
            self.directory.close()
            self.directory = None
        self.status.set("Local broadcast stopped")

    def tick(self):
        try:
            while True:
                ok, result = self.results.get_nowait()
                self.refresh.configure(state="normal")
                if ok:
                    self.stations = result
                    self.render_stations()
                    self.status.set(f"Discovered {len(result)} stations")
                else:
                    self.status.set(f"Directory unavailable: {result}")
        except queue.Empty:
            pass
        failed = [str(key) for key, proc in self.broadcaster.processes.items() if proc.poll() is not None]
        if failed:
            self.status.set(f"Broadcast failed for station {', '.join(failed)}. See station log files.")
        elif self.player and self.current:
            state = str(self.player.get_state()).split(".")[-1]
            self.status.set(f"{state} • {self.current.group}:{self.current.port} • Volume {round(self.volume.get())}%" + (" • Muted" if self.muted.get() else ""))
            if state in ("Opening", "Buffering"):
                self.status.set(self.status.get() + " • Check sender / firewall if this persists")
        self.root.after(500, self.tick)

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.stop()
        self.stop_broadcast()
        def finish():
            if any(t.is_alive() for t in self.cleanup_threads):
                self.root.after(50, finish)
            else:
                self.root.destroy()
        finish()


def main():
    root = tk.Tk()
    RadioApp(root)
    root.mainloop()
