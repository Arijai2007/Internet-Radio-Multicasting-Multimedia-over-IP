# Airwave — Python Multicast TV & Radio

The application is written in Python (`radio/`), with a native desktop UI, TCP station discovery, and UDP multicast video/audio. It replaces the previous C implementation, which remains available in Git history.

## Complete project report

Read the [project report](docs/Airwave_Project_Guide.md) or download the [Word document](docs/Airwave_Project_Guide.docx) for Windows setup, every button and field, a step-by-step channel creation example, architecture, networking explanations, dashboard measurements, demonstration steps, troubleshooting and 40 viva questions with answers.

## Run on Windows

Install Python 3.10+ and [64-bit VLC desktop](https://www.videolan.org/vlc/) matching Python architecture. Then double-click `run.bat`. First launch downloads dependencies, including FFmpeg.

Click **Start local broadcast**, select **Studio One**, then **Play selected station**. Studio One plays an instrumental arrangement of **Ode to Joy**; Studio Two plays **Twinkle, Twinkle, Little Star**, both with a moving video test card. These original synthesized arrangements of public-domain melodies are generated offline and cached in `media/demo-music/`. No song downloads are needed. Use volume, mute, pause/resume, stop and station switching. Closing the window stops the broadcasters started by this app.

Manual setup:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m radio
```

Linux: install Python, Tkinter and VLC (`sudo apt install python3-venv python3-tk vlc` on Ubuntu), then use `.venv/bin/python` for the commands. Embedded playback supports Windows and Linux. macOS embedded playback is not implemented; use the headless sender and VLC as receiver.

## Media and network setup

Click **Manage local channels** to add, edit or remove a channel. Choose **New channel**, enter its name and network details, and use **Choose file…** to select a song or video. Use `demo` as the source for generated music. **Save channel** validates the fields and saves them to `stations.json`; media files are never deleted. Keep at least one channel. Saving while broadcasting asks to stop the broadcast; press **Start local broadcast** afterwards to apply the changes. **Show local channels** restores your saved list after viewing a remote directory.

Edit `stations.json`: replace `source: "demo"` with a video/audio path such as `media/my-video.mp4` or `media/radio.mp3`, update its name/description, and restart. Relative paths resolve against the project folder. Each channel needs a unique multicast group/port pair. Sources loop. Silent videos remain silent; missing source audio cannot be recovered.

For multiple computers, start the broadcaster on the sender. On each receiver enter the sender's IP in **Directory host**, click **Refresh stations**, and play a channel. Use **Local IPv4** to select that machine's own adapter address before broadcasting/playback. For same-machine testing try `127.0.0.1`.

Headless sender: `python -m radio --broadcast --interface 192.168.1.10` (use the actual sender adapter address).

Allow TCP 5432 and station UDP ports (5433/5434 by default) through the private-network firewall. Use a multicast-capable LAN. Wi-Fi isolation can block delivery; ordinary internet connections generally do not route multicast. TCP is for discovery; media comes from multicast groups. Configured local stations can play without discovery.

## Fixes and additions

The original sender sent 64 KB MP4 chunks with fixed delays, and the receiver played an incomplete growing file. Fragmentation, mid-file joins, missing headers and file boundaries could break audio/video. Pause stopped reception and cleanup killed unrelated players.

The Python sender uses FFmpeg real-time pacing, MPEG-TS, H.264 video, AAC audio, regular keyframes/headers, and 1316-byte UDP packets. libVLC decodes audio/video inside the UI. Cleanup targets only this app's processes. Pause is temporary live-player pause, not DVR recording; buffering/live position after resume depends on VLC.

Added configurable channels, audio-only support, volume/mute, station library, broadcaster controls, background discovery, validated JSON metadata, per-station error logs, headless mode and integration checks.

## Network dashboard

When a channel plays, the dashboard shows incoming media bitrate (kb/s), received UDP packet count, time since the last packet, player opening/buffering duration or playback state, and a 30-second bitrate graph. Measurements reset when switching or stopping channels. They describe the selected channel on this receiver, not server upload speed or viewer count. The graph scales to recent traffic.

**TS gaps** estimates missing MPEG-TS payload packets using per-stream continuity counters. It is not an exact count or percentage of lost UDP datagrams: counters wrap, and reordering, duplicated packets, sender restarts or local receive-buffer overflow can affect the estimate. Explicit stream discontinuities reset the baseline. The dashboard uses a separate passive multicast socket, so its reception can differ from the player's. If that socket cannot open, playback continues and the dashboard reports measurements unavailable. See [FFmpeg's MPEG-TS continuity handling](https://github.com/FFmpeg/FFmpeg/blob/master/libavformat/mpegts.c) for protocol context.

## Troubleshooting

- VLC missing: install native VLC matching Python architecture. The Python binding does not include libVLC.
- No sound: unmute the app/system mixer, check the system output device, and try Studio One's music. Check your own source contains audio.
- Opening/buffering: check broadcaster, adapter address, firewall and multicast support.
- Broadcast fails: inspect `station-1.log` / `station-2.log`, media paths and whether TCP 5432 is already in use.
- First setup requires internet. Demo channels then work offline.

## Checks

```sh
python -m pip install pytest
python -m pytest -q
python -m tests.playback_check
python -m tests.dashboard_check
```

Tests cover invalid addressing, TCP discovery/restart, stream configuration and real multicast reception. Playback check requires VLC and verifies decoded video frames and audio blocks using dummy audio output; it cannot prove physical speakers are audible. Check audible sound and real LAN delivery on presentation machines.

Code: `radio/app.py` (UI), `radio/core.py` (broadcast/discovery), `radio/player.py` (VLC loading), `radio/__main__.py` (entry point).

References: [FFmpeg UDP](https://ffmpeg.org/ffmpeg-protocols.html#udp), [VideoLAN libVLC](https://videolan.videolan.me/vlc/master/libvlc.html).
