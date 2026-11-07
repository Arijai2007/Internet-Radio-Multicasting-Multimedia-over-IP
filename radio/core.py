"""Validated station metadata, TCP discovery, and paced MPEG-TS broadcasting."""
from dataclasses import dataclass, asdict
import ipaddress
import json
import os
from pathlib import Path
import socket
import socketserver
import subprocess
import threading
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Station:
    id: int
    name: str
    description: str
    group: str
    port: int
    source: str = "demo"

    def __post_init__(self):
        address = ipaddress.ip_address(self.group)
        if address.version != 4 or not address.is_multicast:
            raise ValueError("Station address must be an IPv4 multicast group")
        if type(self.port) is not int or not 1024 <= self.port <= 65535:
            raise ValueError("Station port must be between 1024 and 65535")
        if type(self.id) is not int or self.id < 1 or not self.name.strip():
            raise ValueError("Station needs a positive ID and a name")


def load_stations(path=ROOT / "stations.json"):
    stations = [Station(**item) for item in json.loads(Path(path).read_text(encoding="utf-8"))]
    if not stations or len({s.id for s in stations}) != len(stations):
        raise ValueError("Provide stations with unique IDs")
    if len({(s.group, s.port) for s in stations}) != len(stations):
        raise ValueError("Each station needs a unique group/port")
    return stations


def ffmpeg_path():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def broadcast_command(station, interface="", ttl=1):
    if interface:
        ipaddress.IPv4Address(interface)
    if not 1 <= ttl <= 255:
        raise ValueError("TTL must be 1 to 255")
    cmd = [ffmpeg_path(), "-hide_banner", "-loglevel", "warning", "-nostdin"]
    if station.source == "demo":
        cmd += ["-re", "-f", "lavfi", "-i", "testsrc2=size=960x540:rate=25",
                "-re", "-f", "lavfi", "-i", f"sine=frequency={440 if station.id == 1 else 660}:sample_rate=48000"]
    else:
        source = Path(station.source).expanduser()
        if not source.is_absolute():
            source = ROOT / source
        if not source.is_file():
            raise ValueError(f"Media file not found: {source}")
        cmd += ["-re", "-stream_loop", "-1", "-i", str(source)]
    # Optional mappings support audio-only radio and silent video as well as TV.
    cmd += ["-map", "0:v:0?", "-map", "1:a:0" if station.source == "demo" else "0:a:0?",
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
            "-pix_fmt", "yuv420p", "-b:v", "1200k", "-g", "25", "-keyint_min", "25",
            "-sc_threshold", "0", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
            "-mpegts_flags", "+resend_headers", "-f", "mpegts"]
    options = {"pkt_size": 1316, "ttl": ttl}
    if interface:
        options["localaddr"] = interface
    return cmd + [f"udp://{station.group}:{station.port}?{urlencode(options)}"]


class Broadcaster:
    def __init__(self):
        self.processes = {}
        self.memberships = {}

    def start(self, station, interface=""):
        if station.id in self.processes and self.processes[station.id].poll() is None:
            return
        cmd = broadcast_command(station, interface)
        # Windows needs a group membership to route multicast on loopback,
        # even before a viewer joins. Keep it alive across station switching.
        if os.name == "nt" and interface and ipaddress.IPv4Address(interface).is_loopback:
            if station.id in self.memberships:
                self.memberships.pop(station.id).close()
            membership = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                membership.bind(("", 0))
                membership.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                      socket.inet_aton(station.group) + socket.inet_aton(interface))
            except Exception:
                membership.close()
                raise
            self.memberships[station.id] = membership
        log = open(ROOT / f"station-{station.id}.log", "ab", buffering=0)
        try:
            self.processes[station.id] = subprocess.Popen(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        finally:
            log.close()

    def stop(self):
        for process in self.processes.values():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        self.processes.clear()
        for membership in self.memberships.values():
            membership.close()
        self.memberships.clear()


class DirectoryServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, stations):
        payload = json.dumps({"version": 1, "stations": [asdict(s) for s in stations]}).encode() + b"\n"

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                self.request.settimeout(3)
                try:
                    self.request.sendall(payload)
                except OSError:
                    pass

        super().__init__(address, Handler)

    def start(self):
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def close(self):
        self.shutdown()
        self.server_close()


def discover(host, port=5432):
    with socket.create_connection((host, port), timeout=3) as connection:
        connection.settimeout(3)
        with connection.makefile("rb") as stream:
            data = stream.readline(65537)
    if len(data) > 65536 or not data.endswith(b"\n"):
        raise ValueError("Station directory response is incomplete or too large")
    payload = json.loads(data)
    if payload.get("version") != 1:
        raise ValueError("Unsupported directory version")
    return [Station(**item) for item in payload["stations"]]
