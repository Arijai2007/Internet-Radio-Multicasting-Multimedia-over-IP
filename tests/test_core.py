import socket
import time
import pytest
from radio.core import Station, load_stations, broadcast_command, DirectoryServer, discover, Broadcaster


def test_invalid_group_and_port():
    for group, port in [("127.0.0.1", 5433), ("ff02::1", 5433), ("239.1.1.1", 70000)]:
        with pytest.raises(ValueError):
            Station(1, "Test", "", group, port)


def test_directory_roundtrip_and_restart():
    stations = load_stations()
    server = DirectoryServer(("127.0.0.1", 0), stations)
    port = server.server_address[1]
    server.start()
    try:
        assert discover("127.0.0.1", port) == stations
        assert discover("127.0.0.1", port) == stations
    finally:
        server.close()
    server = DirectoryServer(("127.0.0.1", port), stations)
    server.server_close()


def test_sender_audio_and_packetization():
    cmd = broadcast_command(load_stations()[0], "127.0.0.1")
    assert "1:a:0" in cmd
    assert "aac" in cmd
    assert "mpegts" in cmd
    assert "pkt_size=1316" in cmd[-1]
    assert "localaddr=127.0.0.1" in cmd[-1]
    assert not any("sine=frequency" in argument for argument in cmd)
    import wave
    from pathlib import Path
    track = next(Path(argument) for argument in cmd if argument.endswith(".wav"))
    with wave.open(str(track), "rb") as music:
        assert music.getnframes() / music.getframerate() > 10
        assert any(music.readframes(music.getnframes()))


def test_real_multicast_transport():
    station = load_stations()[0]
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    receiver.bind(("", station.port))
    receiver.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                        socket.inet_aton(station.group) + socket.inet_aton("127.0.0.1"))
    receiver.settimeout(15)
    broadcaster = Broadcaster()
    try:
        broadcaster.start(station, "127.0.0.1")
        packets = [receiver.recv(65536) for _ in range(20)]
        assert all(len(packet) <= 1316 for packet in packets)
        assert all(packet[0] == 0x47 for packet in packets)
        assert broadcaster.processes[station.id].poll() is None
    finally:
        broadcaster.stop()
        receiver.close()
    assert not broadcaster.processes


def test_broadcast_survives_before_viewer_joins():
    broadcaster = Broadcaster()
    station = load_stations()[1]
    try:
        broadcaster.start(station, "127.0.0.1")
        time.sleep(1)
        assert broadcaster.processes[station.id].poll() is None
    finally:
        broadcaster.stop()
    assert not broadcaster.memberships
