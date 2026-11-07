import argparse
import time
from .core import Broadcaster, DirectoryServer, load_stations


def main():
    parser = argparse.ArgumentParser(description="Airwave Python multicast TV & radio")
    parser.add_argument("--broadcast", action="store_true", help="Run sender and directory without the GUI")
    parser.add_argument("--interface", default="", help="Local network adapter IPv4 address")
    args = parser.parse_args()
    if not args.broadcast:
        from .app import main as gui
        gui()
        return
    stations = load_stations()
    server = DirectoryServer(("0.0.0.0", 5432), stations)
    broadcaster = Broadcaster()
    try:
        server.start()
        for station in stations:
            broadcaster.start(station, args.interface)
        print("Broadcasting. Directory TCP 5432. Ctrl+C to stop.")
        while True:
            time.sleep(1)
            if any(p.poll() is not None for p in broadcaster.processes.values()):
                raise RuntimeError("A broadcaster exited. Check station-*.log")
    except KeyboardInterrupt:
        pass
    finally:
        broadcaster.stop()
        server.close()


if __name__ == "__main__":
    main()
