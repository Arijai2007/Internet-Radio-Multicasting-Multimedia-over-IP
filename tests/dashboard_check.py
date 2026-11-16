"""Manual GUI/media integration check. Uses dummy audio to avoid playing sound."""
import tkinter as tk
from radio.app import RadioApp
from radio.player import create_vlc
import radio.app as module


def main():
    root = tk.Tk()
    app = RadioApp(root, '127.0.0.1')
    original = module.create_vlc
    module.create_vlc = lambda interface: create_vlc(interface, muted=True)
    failures = []
    def check():
        try:
            assert app.player.is_playing(), app.player.get_state()
            assert app.monitor.datagrams > 0
            assert len(app.rate_history) > 0
            assert max(app.rate_history) > 0
            assert 'UDP packets' in app.metrics.get()
            import vlc
            media = app.player.get_media()
            try:
                stats = vlc.MediaStats()
                assert media.get_stats(stats)
                assert stats.decoded_video > 0 and stats.decoded_audio > 0
            finally:
                media.release()
            print('PASS: live dashboard, graph, video and audio decode together')
        except Exception as exc:
            failures.append(exc)
        finally:
            app.close()
    try:
        app.start_broadcast()
        app.play()
        root.after(10000, check)
        root.mainloop()
    finally:
        module.create_vlc = original
        app.broadcaster.stop()
    if failures:
        raise failures[0]


if __name__ == '__main__':
    main()
