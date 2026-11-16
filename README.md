# Airwave — Python Multicast TV & Radio

The application is written in Python (`radio/`), with a native desktop UI, TCP station discovery, and UDP multicast video/audio. It replaces the previous C implementation, which remains available in Git history.

Airwave is a **Computer Networks project** demonstrating one broadcaster sending live media to multiple receivers on a multicast-capable local network. Python manages discovery, channels and network monitoring; FFmpeg encodes and transmits the media, and libVLC plays it inside the window.

## Features

- Desktop player with channel switching, pause/resume, volume and mute.
- TCP station directory and UDP multicast audio/video delivery.
- Channel editor for adding, editing and removing channels and choosing media files.
- Network dashboard with received bitrate, packet count, buffering state and a traffic graph.
- Offline instrumental demo channels and support for your own songs and videos.
- Validated configuration, safe saving and cleanup of this app's sender processes.

## Complete project report

Read the [project report](docs/Airwave_Project_Guide.md) or download the [Word document](docs/Airwave_Project_Guide.docx) for Windows setup, every button and field, a step-by-step channel creation example, architecture, networking explanations, dashboard measurements, demonstration steps, troubleshooting and 40 viva questions with answers.

## Run on Windows

1. Install Python 3.10+ with Tkinter and [VLC desktop](https://www.videolan.org/vlc/), normally 64-bit for both.
2. Download and extract this repository into a writable folder.
3. Double-click **run.bat**. First launch creates the Python environment and downloads dependencies, including FFmpeg.
4. Enter **127.0.0.1** in **Local IPv4** for a same-computer test.
5. Click **Start local broadcast**, select **Studio One**, then click **Play selected station**.

Click **Start local broadcast**, select **Studio One**, then **Play selected station**. Studio One plays an instrumental arrangement of **Ode to Joy**; Studio Two plays **Twinkle, Twinkle, Little Star**, both with a moving video test card. These original synthesized arrangements of public-domain melodies are generated offline and cached in `media/demo-music/`. No song downloads are needed. Use volume, mute, pause/resume, stop and station switching. Closing the window stops the broadcasters started by this app.

The main workflow uses the Windows GUI. Internet is needed for initial setup; the generated demo channels then work offline. Installing the Python binding alone does not install native VLC.

## What each control does

| Control | Purpose |
|---|---|
| Directory host | Address of the sender providing the station list. Use `127.0.0.1` for this computer. |
| Local IPv4 | This computer's own network adapter address. Set it before starting playback or broadcasting. |
| Refresh stations | Fetches the directory host's channel list over TCP. It does not start playback or overwrite local channels. |
| Station library | Single-click to select a channel; double-click to play it. |
| Play selected station | Joins and plays the selected channel, replacing previous playback. |
| Manage local channels | Opens the editor for this computer's saved channels. |
| Show local channels | Restores the saved local channel list after viewing a remote directory. |
| Start local broadcast | Starts the directory and **all** saved local channels. Does not automatically play a channel. |
| Stop local broadcast | Stops this app's senders and directory. Other viewers stop receiving new media. |
| Pause / Resume | Pauses or resumes this player's playback; the sender and other viewers continue. |
| Stop | Stops only local playback and clears its dashboard. Broadcasting continues until separately stopped. |
| Mute and Volume | Adjust this player's audio without affecting other receivers. |
| Main window X | Closes the app and cleans up its player, monitoring socket and local broadcasts. |

To finish a local demonstration, click **Stop** and **Stop local broadcast**, or close the main window.

## Add your own channel

1. Store a song or video on the **sender computer** in a stable location.
2. Click **Manage local channels**, then **New channel**.
3. For a third channel in the default setup, enter:
   - **Channel ID:** `3`
   - **Name:** `Music TV`
   - **Description:** a short description of your content
   - **Multicast IPv4:** `239.192.4.3`
   - **UDP port:** `5435`
4. Click **Choose file…** and select your media. Use the exact source value `demo` for generated content instead.
5. Click **Save channel**. If broadcasting is active, confirm that it may stop. Saving also stops local playback.
6. Close the editor, click **Start local broadcast**, select the new channel and press **Play selected station**.
7. On remote receivers, click **Refresh stations** to retrieve the updated list.

Selecting a saved editor row loads its fields for editing. **Save channel** stores changes; **Remove channel** removes the selected record after confirmation while keeping its media file. At least one channel must remain. **Close** exits the editor without saving unsaved field edits.

Channels are saved in `stations.json`. IDs must be unique positive integers, ports must be from 1024 to 65535, and every multicast group/port pair must be unique. Relative file paths resolve against the project folder. Source files loop continuously; playlists are not implemented. Audio-only files play without video, and silent videos remain silent.

Media files are not automatically uploaded to GitHub or copied to receivers. Receivers need the stream, not a local copy of the source file.

## Run across multiple computers

1. Connect the computers to the same multicast-capable LAN.
2. On the **sender**, set **Local IPv4** to its LAN address and click **Start local broadcast**.
3. On each **receiver**, set **Directory host** to the sender's address and **Local IPv4** to that receiver's own address.
4. Click **Refresh stations**, select a channel and press **Play selected station**. Receivers do not need to start local broadcasts.

For example, the sender might be `192.168.1.10` and two receivers `192.168.1.11` and `192.168.1.12`. Use the actual assigned addresses. `127.0.0.1` always refers to the same computer and cannot identify a remote sender.

Allow TCP 5432 and station UDP ports (5433/5434 by default) through the private-network firewall. Use a multicast-capable LAN. Wi-Fi isolation can block delivery; ordinary internet connections generally do not route multicast. TCP is for discovery; media comes from multicast groups. Configured local stations can play without discovery.

## How the networking works

```text
stations.json -> Python directory -- TCP 5432 --> receiver channel list
Media file   -> FFmpeg -- MPEG-TS over UDP multicast --> libVLC player
                                  |
                                  +--> passive monitor --> dashboard
```

Each channel has its own multicast destination and FFmpeg process. The default multicast TTL is 1, intended for the local segment. Default destinations are `239.192.4.1:5433` and `239.192.4.2:5434`.

There is no configured viewer limit or measured maximum capacity. Multicast avoids a separate media stream at the sender for each viewer, but practical delivery depends on the LAN. More channels increase encoder CPU and outgoing bandwidth. Listener counts, authentication and encrypted media are not implemented.

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

## Project structure

| File | Responsibility |
|---|---|
| `radio/app.py` | Desktop controls, playback and dashboard integration |
| `radio/core.py` | Channel validation/saving, TCP discovery and FFmpeg broadcasting |
| `radio/editor.py` | Channel editor and media selection |
| `radio/metrics.py` | Multicast traffic monitoring and continuity-gap estimation |
| `radio/player.py` | Native VLC loading |
| `radio/music.py` | Offline instrumental demo generation |
| `radio/__main__.py` | Application entry point |
| `stations.json` | Local channel configuration |
| `tests/` | Automated tests and live playback/dashboard checks |
| `docs/` | Complete project report and viva preparation |

References: [FFmpeg UDP](https://ffmpeg.org/ffmpeg-protocols.html#udp), [VideoLAN libVLC](https://videolan.videolan.me/vlc/master/libvlc.html).
