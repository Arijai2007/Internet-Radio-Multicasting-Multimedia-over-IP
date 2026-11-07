"""Manual integration check: decode live multicast video AND audio through libVLC."""
import time
from radio.core import Broadcaster, load_stations
from radio.player import create_vlc


def main():
    sender = Broadcaster()
    instance = create_vlc("127.0.0.1", muted=True)
    player = instance.media_player_new()
    station = load_stations()[0]
    media = instance.media_new(f"udp://@{station.group}:{station.port}")
    player.set_media(media)
    try:
        player.play()
        sender.start(station, "127.0.0.1")
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            stats = __import__('vlc').MediaStats()
            if media.get_stats(stats) and stats.decoded_video > 10 and stats.decoded_audio > 10:
                print(f"PASS: decoded {stats.decoded_video} video frames and {stats.decoded_audio} audio blocks")
                return
            time.sleep(.5)
        raise AssertionError(f"Playback did not decode audio/video: {player.get_state()}")
    finally:
        player.stop()
        player.release()
        media.release()
        instance.release()
        sender.stop()


if __name__ == '__main__':
    main()
