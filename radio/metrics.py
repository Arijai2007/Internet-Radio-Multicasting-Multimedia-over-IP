"""Passive multicast measurements, independent of playback and audio output."""
import socket
import threading
import time


class TransportCounter:
    """Estimate missing MPEG-TS payload packets from per-PID continuity counters.

    Not an exact UDP-loss measurement: counters wrap at 16, and reordering or
    sender resets can resemble loss. Explicit discontinuities reset the baseline.
    """
    def __init__(self):
        self.previous = {}
        self.packets = self.gaps = 0

    def feed(self, data):
        for offset in range(0, len(data) - 187, 188):
            packet = data[offset:offset + 188]
            if packet[0] != 0x47:
                continue
            pid = ((packet[1] & 31) << 8) | packet[2]
            if pid == 8191 or packet[1] & 0x80:
                continue
            control = (packet[3] >> 4) & 3
            if not control:
                continue
            discontinuity = control in (2, 3) and packet[4] > 0 and packet[5] & 0x80
            if discontinuity:
                self.previous.pop(pid, None)
            if not control & 1:
                continue
            cc = packet[3] & 15
            old = self.previous.get(pid)
            if old is not None and cc != old:
                self.gaps += (cc - old - 1) % 16
            self.previous[pid] = cc
            self.packets += 1


class NetworkMonitor:
    def __init__(self, station, interface=""):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            # Linux can otherwise deliver traffic for other joined groups on the
            # same port. Restrict this socket to its own memberships when offered.
            if __import__('sys').platform.startswith("linux"):
                self.socket.setsockopt(socket.IPPROTO_IP, 49, 0)  # IP_MULTICAST_ALL
            self.socket.bind(("", station.port))
            self.membership = socket.inet_aton(station.group) + socket.inet_aton(interface or "0.0.0.0")
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.membership)
            self.socket.settimeout(.3)
        except Exception:
            self.socket.close()
            raise
        self.lock = threading.Lock()
        self.done = threading.Event()
        self.counter = TransportCounter()
        self.bytes = self.datagrams = 0
        self.last_received = None
        self.last_sample = time.monotonic()
        self.sample_bytes = 0
        self.thread = threading.Thread(target=self.receive, daemon=True)
        self.thread.start()

    def receive(self):
        while not self.done.is_set():
            try:
                data = self.socket.recv(65536)
            except socket.timeout:
                continue
            except OSError:
                break
            with self.lock:
                self.bytes += len(data)
                self.datagrams += 1
                self.last_received = time.monotonic()
                self.counter.feed(data)

    def sample(self):
        now = time.monotonic()
        with self.lock:
            rate = (self.bytes - self.sample_bytes) * 8 / max(now - self.last_sample, .001) / 1000
            self.sample_bytes, self.last_sample = self.bytes, now
            return {"kbps": rate, "datagrams": self.datagrams,
                    "gaps": self.counter.gaps,
                    "silence": None if self.last_received is None else now - self.last_received}

    def close(self):
        self.done.set()
        self.socket.close()
        self.thread.join(timeout=1)
