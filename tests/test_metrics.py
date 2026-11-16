from radio.metrics import TransportCounter, NetworkMonitor
from radio.core import Broadcaster, load_stations
import time


def packet(cc, pid=256, control=1, discontinuity=False):
    data = bytearray(188)
    data[:4] = bytes([0x47, (pid >> 8) & 31, pid & 255, (control << 4) | cc])
    if control in (2, 3):
        data[4:6] = bytes([1, 128 if discontinuity else 0])
    return bytes(data)


def test_continuity_wrap_duplicates_and_missing_packets():
    counter = TransportCounter()
    counter.feed(b''.join(packet(cc) for cc in [14, 15, 0, 0, 3, 4]))
    assert counter.gaps == 2


def test_pid_independence_null_packets_and_discontinuity():
    counter = TransportCounter()
    counter.feed(packet(0) + packet(9, pid=257) + packet(7, pid=8191))
    counter.feed(packet(0, control=2) + packet(1))
    counter.feed(packet(10, control=3, discontinuity=True) + packet(11))
    counter.feed(packet(3, control=2, discontinuity=True) + packet(7))
    assert counter.gaps == 0


def test_monitor_measures_live_multicast_and_closes():
    station = load_stations()[0]
    monitor = NetworkMonitor(station, "127.0.0.1")
    sender = Broadcaster()
    try:
        sender.start(station, "127.0.0.1")
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            time.sleep(.15)
            stats = monitor.sample()
            if stats['datagrams'] > 10:
                break
        assert stats['datagrams'] > 10
        assert stats['kbps'] > 0
        assert stats['silence'] < 2
    finally:
        sender.stop()
        monitor.close()
    assert not monitor.thread.is_alive()
