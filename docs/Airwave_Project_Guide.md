# Airwave Computer Networks Project Guide
## Setup operation technical explanation and viva preparation
Airwave demonstrates how one broadcaster can deliver live audio and video to multiple receivers using IP multicast. A Python desktop application manages channels, discovers stations over TCP, controls broadcasting and playback, and displays network measurements.
This guide explains how to run and demonstrate the actual project, how its components work, and how to answer common viva questions. The intended demonstration is one sender and two or more receivers on a multicast-capable local network. A single-computer test is also supported.
The application uses Python sockets for station discovery and monitoring. FFmpeg encodes and transmits media; libVLC decodes it inside the interface. These library responsibilities should be stated clearly during assessment.
## Project details
Project name: Internet Radio Multicasting Multimedia over IP
Application name: Airwave
Repository owner: Arijai2007
Document date: 16 November 2026
Implementation reviewed: a755a6b
Repository: https://github.com/Arijai2007/Internet-Radio-Multicasting-Multimedia-over-IP
## Guide map
1  Project overview and meaning
2  Included features and software requirements
3  Architecture and end to end operation
4  Networking concepts and default configuration
5  Windows installation and first run
6  Linux setup and command line operation
7  Demonstration across multiple computers
8  Channel editing and media selection
9  Network dashboard and interpreting measurements
10  Source code and implementation walkthrough
11  Verification and presentation procedure
12  Troubleshooting and common errors
13  Limitations improvements and references
14 to 17  Forty expected viva questions with answers

# 1 Project overview and meaning
## Problem being addressed
Sending a separate copy of the same television or radio stream to every viewer increases the sender's bandwidth requirement. Airwave demonstrates multicast delivery: a sender transmits a channel to a group address, and interested receivers join that group. Network devices replicate traffic where needed.
For a teaching example, suppose a channel requires 1.5 Mb/s and ten viewers receive it. Ten separate unicast streams would require about 15 Mb/s of media traffic at the sender. One multicast stream remains about 1.5 Mb/s at the sender for that channel, excluding overhead. This is an illustration, not a measured benchmark; downstream links and Wi-Fi airtime still carry traffic.
## Meaning of the project name
Internet radio means delivering audio through IP networking. Multicasting means delivering one transmission to a selected receiver group. Multimedia means audio, video or both. Over IP means the network carries the media using Internet Protocol packets.
The title does not imply that the application works through every public internet connection. This implementation is intended for a multicast-capable LAN, normally within one network segment because its default multicast TTL is 1.
## Objectives
- Discover available channels through a TCP directory.
- Broadcast live media using UDP multicast and switch between channel groups.
- Provide a desktop player with audio controls and configurable local channels.
- Observe incoming traffic and explain the limits of packet-loss estimation.
- Demonstrate socket programming, group membership, addressing and concurrent tasks.
## What makes this a Computer Networks project
The main networking work is the separation between reliable control information and live media delivery. TCP carries station metadata. UDP multicast carries the media. The receiver joins a group, buffers incoming data and displays measurements. The interface makes those functions easier to demonstrate, but the networking behavior is the academic focus.
## How to describe our contribution
We implement the Python application logic, station configuration, TCP discovery, process management, channel editor and network dashboard. We integrate FFmpeg for encoding and MPEG-TS transmission, and libVLC for playback. We do not claim to have implemented H.264, AAC, TCP or UDP themselves.

# 2 Included features and requirements
## Current features
- Desktop interface built with Tkinter, including a station list and embedded player.
- Start and stop all configured local broadcasts from the interface.
- TCP station discovery through the directory host field.
- Play, stop, pause and resume, with volume and mute controls.
- Add, rename, edit and remove local channels through the channel editor.
- Choose an audio or video file without editing configuration manually.
- Network dashboard with bitrate, UDP packet count, stream-counter gaps, buffering state and a traffic graph.
- Headless broadcasting mode for a sender that does not need the GUI.
- Input validation, atomic configuration saving and per-station error logs.
## Default channels
| Channel | Media | Group | UDP port |
| Studio One | Ode to Joy instrumental with test video | 239.192.4.1 | 5433 |
| Studio Two | Twinkle instrumental with test video | 239.192.4.2 | 5434 |
The demo tracks are original synthesized arrangements of public-domain melodies, generated offline and cached under media/demo-music. No commercial recordings are bundled.
## Software requirements
| Component | Purpose |
| Python 3.10 or later and Tkinter | Runs the application and GUI |
| Native VLC desktop | Supplies libVLC for embedded playback |
| python-vlc | Python bindings for libVLC |
| imageio-ffmpeg | Supplies the FFmpeg executable used by the sender |
| pytest | Runs automated checks during development |
Use a 64-bit Python and 64-bit VLC installation on the usual Windows setup. Installing python-vlc alone does not install VLC. Dependencies are listed in requirements.txt. The project does not require a C compiler or WSL.
## Supported environments
Windows and Linux have embedded playback paths; local verification was on Windows. macOS embedded playback is not implemented; use standalone VLC as a receiver. Internet is needed for initial downloads, but the demo channels then work offline.

# 3 Architecture and end to end operation
## Logical architecture
```text
SENDER COMPUTER                       RECEIVER COMPUTERS
stations.json
      |
      +-- Python channel directory -- TCP 5432 --> station list
      |
 Python broadcaster launches FFmpeg
      |
 Source -> H.264 video and AAC audio -> MPEG-TS
      |
 UDP multicast group ------------------> libVLC player
      |                                  |
      +--------------------------------> passive monitor
                                         |
                                   network dashboard
```
The receiver side can run on several computers. A single application can also run the sender and receiver together for a local demonstration. The diagram describes logical components; it does not mean each component needs a separate machine.
## Discovery sequence
1. The sender reads the saved local channel configuration.
2. Starting a local broadcast opens the station directory on TCP port 5432 and starts one FFmpeg process per channel.
3. A receiver connects to the directory host when Refresh stations is clicked.
4. The directory sends a versioned JSON object terminated by a newline and closes the connection.
5. The receiver validates the response and displays its station records.
Discovery does not transfer the song files. The receiver only needs channel metadata and a reachable multicast stream. A receiver can also use its locally saved station list without contacting the directory.
## Media sequence
1. FFmpeg reads a file at its playback rate, or combines the demo video source with generated music.
2. Video is encoded as H.264 and audio as AAC where the source contains those media types.
3. MPEG-TS multiplexes the media into a live transport stream.
4. FFmpeg sends datagrams of up to 1316 bytes to the channel group and port.
5. libVLC receives, buffers and decodes the stream inside the desktop window.
6. A separate multicast socket observes traffic for the dashboard.
Regular video keyframes and repeated headers help a viewer join an already-running channel. There may still be a short opening or buffering delay.

# 4 Networking concepts and configuration
## Transport and network roles
TCP is connection-oriented and delivers an ordered byte stream. Airwave uses it for the small station-directory response, where complete metadata matters. The response needs framing because one TCP receive operation is not guaranteed to correspond to one application message.
UDP preserves datagram boundaries but does not guarantee delivery, ordering or retransmission. Multicast delivery uses UDP here because the sender can transmit a live channel to a group without establishing one media connection per viewer. The application does not implement acknowledgements or recovery of lost media packets.
IP multicast is different from broadcast. Broadcast addresses all hosts in its broadcast domain; multicast targets a group. Receivers request membership through their operating system networking stack. IGMP is used by IPv4 hosts and network equipment to manage multicast membership where applicable [1].
## Default network values
| Setting | Value | Meaning |
| Directory | TCP 5432 | Station metadata service |
| Channel one | 239.192.4.1 and UDP 5433 | First media group and destination port |
| Channel two | 239.192.4.2 and UDP 5434 | Second media group and destination port |
| Multicast TTL | 1 | Intended for the local network segment |
| UDP payload target | Up to 1316 bytes | Seven complete 188-byte TS packets |
| Video target | 1200 kb/s and GOP 25 | Target encoding rate and keyframe interval setting |
| Audio target | 128 kb/s and 48 kHz stereo | AAC encoding settings |
The general IPv4 multicast address range is 224.0.0.0 through 239.255.255.255 [1]. The chosen groups belong to administratively scoped multicast space [2]. A multicast group is a destination identifier, not the sender's computer address.
## Why the payload size matters
Seven MPEG-TS packets occupy 7 times 188 = 1316 bytes. With typical IPv4 and UDP headers, that is 1344 bytes before link-layer overhead. It fits a common 1500-byte IP MTU and reduces fragmentation risk, but tunnels and unusual paths may have smaller MTUs.
The application-layer content is MPEG-TS, carried in UDP, carried in IPv4, then in the local link technology such as Ethernet or Wi-Fi. This project does not use RTP or RTSP for media transport.

# 5 Windows installation and first run
## Install the prerequisites
1. Install Python from python.org. Include Tkinter and make Python available from the command line during installation.
2. Install the standard VLC desktop application from videolan.org. Match VLC architecture to Python, normally 64-bit for both.
3. Download the project ZIP from the Arijai2007 repository and extract it, or clone the repository. Keep the project files together in a writable folder.
4. Open the project folder and double-click run.bat. The first run creates .venv and installs the required Python packages, including the FFmpeg package.
Do not run the application directly inside a ZIP preview. First launch may take time because dependencies must be downloaded. If Windows asks about network access, review the prompt yourself and permit only the access appropriate to your trusted demonstration network.
## Run a test on one computer
1. Wait for the Airwave window to open.
2. Set Local IPv4 to 127.0.0.1. Directory host can remain 127.0.0.1.
3. Click Show local channels if the visible list came from a remote directory.
4. Click Start local broadcast.
5. Select Studio One and click Play selected station.
6. Expect a moving test card and the Ode to Joy instrumental. Ensure Mute is off and volume is above zero.
7. Select Studio Two and click Play selected station to change the stream.
8. Observe the dashboard, then use Stop and Stop local broadcast to finish.
The loopback address means this same computer. Other computers cannot use the sender's loopback address to reach it. Windows loopback multicast routing is handled by keeping the broadcaster's group membership alive before viewers join.
## Manual setup if the launcher fails
Open a terminal in the project folder and run:
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m radio
```
The virtual environment keeps project dependencies separate from other Python projects. To reopen an existing installation, run run.bat again. It checks dependencies on each launch, so a fresh or incomplete setup may still need internet access.

# 6 Linux setup and command line operation
## Linux installation example
On Ubuntu or Debian, install the native prerequisites, then create the project environment:
```sh
sudo apt update
sudo apt install python3-venv python3-tk vlc
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m radio
```
Run these commands from an extracted or cloned project folder. Other Linux distributions use different package-manager commands. Embedded video uses the X11 window handle path; a desktop session with suitable X11 or XWayland support is needed. Linux behavior should be checked on the demonstration machine before assessment.
## Headless broadcasting
Headless means the broadcaster runs without the desktop interface. On Windows:
```powershell
.\.venv\Scripts\python -m radio --broadcast --interface 192.168.1.10
```
On Linux:
```sh
.venv/bin/python -m radio --broadcast --interface 192.168.1.10
```
Replace the example address with the sender's own LAN adapter IPv4 address. The sender loads stations.json, starts the directory and all configured channels, and runs until interrupted. Press Ctrl+C to stop it. Do not also start the GUI broadcaster on the same computer using the same TCP port.
## Selecting an interface for the GUI
```powershell
.\.venv\Scripts\python -m radio --interface 127.0.0.1
```
Without --broadcast, the application opens its GUI and pre-fills the interface field. The interface can also be set directly in the window before starting playback or broadcasting. Leaving it blank lets the networking stack choose a route, which can be confusing on computers with Wi-Fi, Ethernet, virtual adapters or VPNs.
## Receiving with standalone VLC
For an alternative receiver, use VLC Open Network Stream with udp://@239.192.4.1:5433 for Studio One or udp://@239.192.4.2:5434 for Studio Two. The network must deliver the multicast group to that machine. Standalone VLC does not provide Airwave's channel editor or its dashboard.
The ordinary workflow remains the desktop app. Terminal mode is an additional deployment option for the sender, not a requirement for each viewer.

# 7 Demonstration across multiple computers
## Suggested arrangement
| Role | Example IPv4 | Action |
| Sender | 192.168.1.10 | Starts local broadcast and station directory |
| Receiver A | 192.168.1.11 | Discovers sender and plays Studio One |
| Receiver B | 192.168.1.12 | Discovers sender and plays either channel |
Use actual machine addresses rather than these examples. Connect all machines to one multicast-capable LAN. Ethernet is often easier to demonstrate than isolated Wi-Fi.
## Sender steps
1. Install the project dependencies and VLC where playback is also needed.
2. Open Airwave and set Local IPv4 to the sender's own LAN address.
3. Review local channels and ensure selected source files exist on the sender.
4. Click Start local broadcast. Allow TCP 5432 and the configured UDP traffic on the appropriate trusted network through local firewall policy.
## Receiver steps
1. Open Airwave on each receiver.
2. Set Directory host to the sender's LAN address, such as 192.168.1.10.
3. Set Local IPv4 to that receiver's own LAN address, not the sender's address.
4. Click Refresh stations, select a channel and press Play selected station.
5. Do not start another local broadcast on the receivers for this demonstration.
No source-file copies are required at the receivers. File paths in directory metadata describe the sender's configuration; the receiver plays the group stream rather than opening those paths.
## What to demonstrate
First show both receivers playing Studio One. Switch Receiver B to Studio Two while Receiver A continues on Studio One. Explain that each receiver chooses a group and that the sender already transmits each configured channel independently of viewer count.
Stop the sender broadcast. The receivers should eventually stop receiving new packets; bitrate falls and the time since the last packet rises. Playback may continue briefly from buffered data. Restart and replay the channel if needed; automatic reconnect is not a guaranteed feature.
## Network conditions
A successful TCP refresh does not prove multicast works. Firewalls and Wi-Fi isolation may block media while allowing discovery. TTL 1 restricts the stream to its local segment. Test the LAN before the viva; avoid relying on guest Wi-Fi or mobile hotspots.

# 8 Channel editing and media selection
## Add a channel through the interface
1. Click Manage local channels and then New channel.
2. Enter a positive, unique Channel ID and a clear Name.
3. Add a Description that identifies the content.
4. Enter an IPv4 multicast group and a UDP port between 1024 and 65535. Each saved group and port pair must be unique.
5. Click Choose file to select an existing song or video. Leave source as demo to use generated test content.
6. Click Save channel. If a local broadcast is active, the app asks before stopping it for the configuration change.
7. Close the editor, start local broadcast again, select the new channel and play it.
Use a separate UDP port for each channel during the demonstration. For example, a third channel can use 239.192.4.3 and port 5435. The editor proposes values, but you should review them for conflicts on the LAN.
## Editing and removing
Select a saved channel in the editor to load its fields. Change the name, media path or network details and save. Remove channel deletes the configuration entry after confirmation; it does not delete the song or video file. At least one local channel must remain.
Changes are written to stations.json using validation and an atomic replacement. This avoids leaving a partially written configuration if saving fails. The editor always manages the local broadcaster configuration, even when the main window is showing a remote directory list.
## Configuration example
```json
{
  "id": 3,
  "name": "Music TV",
  "description": "Our selected music video",
  "group": "239.192.4.3",
  "port": 5435,
  "source": "media/music.mp4"
}
```
stations.json contains a JSON list of these objects, separated by commas. Relative paths resolve against the project folder. File paths selected with the browser can be absolute. A file path valid on one sender may need updating after copying the project to another computer.
Audio-only files play as radio without video. A video with no audio remains silent. Files loop continuously; selecting several songs as an automatic playlist is not implemented. Only use media you are entitled to demonstrate or distribute, and remember that ignored media files are not automatically included in GitHub downloads.

# 9 Network dashboard and measurements
## Reading the dashboard
| Reading | Interpretation |
| Received kb/s | Incoming UDP payload bytes converted to kilobits per second over the latest sample interval |
| UDP packets | Number of datagrams received by the monitoring socket since tuning this channel |
| TS gaps | Estimate of missing MPEG-TS payload packets from continuity-counter jumps |
| Opening or Buffering time | How long the player has remained in these observed states |
| Last packet age | Time since the monitoring socket last received a datagram |
| Traffic graph | Recent bitrate samples, normally about 30 seconds, scaled to recent traffic |
The interface normally samples every half second. Measurements reset when stopping or switching channels. A paused player can still have incoming multicast traffic, so nonzero bitrate during pause is expected. Buffering time is not a measurement of one-way network latency or remaining buffer capacity.
## Bitrate calculation example
If the monitor receives 100,000 payload bytes over 0.5 seconds, it reports 1600 kb/s: multiply bytes by 8, divide by elapsed seconds, then divide by 1000. The measurement excludes Ethernet, IP and UDP header overhead, and it includes the MPEG-TS data carried in those UDP payloads.
The graph is a recent trend, not a fixed-scale speed test. Video content, encoding behavior and scheduling can change the observed rate. The configured encoder target is not a guaranteed constant measured bitrate.
## Understanding the loss estimate
MPEG-TS packets carry a packet identifier and a four-bit continuity counter. Payload counters normally advance modulo 16 for each identifier. A jump can indicate missing packets. The monitor maintains a separate baseline per identifier, ignores null packets and resets the baseline for explicit discontinuities.
TS gaps are not lost UDP datagrams, an exact packet-loss percentage or a count of missing video frames. A datagram can contain several TS packets. Reordering, sender resets and local buffer overflow can resemble loss; whole multiples of the counter range can also conceal losses.
## Measurement boundaries
The dashboard uses a passive multicast socket separate from libVLC. Its receive behavior can differ from the player's. Zero observed gaps does not prove perfect delivery. If the monitoring socket cannot open, playback can continue while the dashboard reports measurements unavailable. The dashboard does not measure viewer count, sender CPU usage, round-trip delay or end-to-end latency.

# 10 Source code and implementation walkthrough
## File responsibilities
| File | Main responsibility |
| radio/app.py | Tkinter window, playback controls, editor integration and dashboard updates |
| radio/core.py | Station validation, atomic saving, TCP directory, discovery and FFmpeg process lifecycle |
| radio/editor.py | Local channel form, file chooser, add edit and remove operations |
| radio/metrics.py | Multicast monitoring socket, received bitrate and TS continuity-gap estimation |
| radio/player.py | Loads native libVLC and creates player instances |
| radio/music.py | Generates and caches the offline instrumental demo tracks |
| radio/__main__.py | Argument handling and GUI or headless entry point |
| stations.json | Saved local channel records |
| requirements.txt and run.bat | Python dependencies and Windows launcher |
| tests directory | Validation, networking, editor and live playback checks |
## Important functions to explain
Station validates field types, group addresses, port ranges and positive IDs. parse_stations checks lists and duplicate identifiers or group-port pairs. save_stations validates before replacing the configuration file. load_stations accepts UTF-8 files including the byte-order marker sometimes written by Windows editors.
DirectoryServer uses a threaded TCP server to answer independent discovery connections. discover reads a bounded newline-terminated response, checks its version and validates each record. The current maximum response is 65,536 bytes, so channel metadata size is a practical configuration limit.
broadcast_command builds an argument list rather than a shell command. It selects demo or file input, real-time pacing, media mappings, encoders and the multicast URL. Broadcaster starts only its own FFmpeg processes and terminates them during cleanup.
## Concurrency
Tkinter handles the interface on its main thread. Directory fetching runs in a worker and returns results through a queue. The monitor receives packets on another worker and protects shared counters with a lock. Native player shutdown runs in a background thread so the GUI can continue processing window messages.
FFmpeg performs the intensive media encoding in separate processes. libVLC handles playback and decoding. One FFmpeg process is created for each channel, so increasing channels increases sender CPU and network demand.
The old C implementation is retained in Git history. It is not the active application and its protocol is not compatible with the Python version.

# 11 Verification and presentation procedure
## Checks supplied with the project
Run the automated checks from the project folder after activating the environment, or use its Python executable explicitly:
```powershell
.\.venv\Scripts\python -m pip install pytest
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m tests.playback_check
.\.venv\Scripts\python -m tests.dashboard_check
```
At guide preparation, the current suite passed 25 tests on the local Windows environment. The tests cover invalid fields, duplicate records, Windows text encoding, safe saves, discovery, multicast reception, editor operations, local and remote configuration separation, continuity estimation and monitor cleanup.
The live playback check verified decoded audio and video. The dashboard check verified live traffic measurements and graph updates alongside decoding. Its dummy audio output deliberately does not test whether physical speakers are audible. These results are local verification, not a large-scale LAN capacity benchmark.
## Suggested five minute presentation
1. Explain the problem and show the architecture. Identify TCP discovery and UDP multicast as separate paths.
2. Start the broadcaster and play Studio One on two receivers. Briefly identify the group and port.
3. Switch one receiver to Studio Two while the other remains on Studio One.
4. Show the channel editor and add a prepared media file. Explain that saving requires restarting the broadcast.
5. Read the bitrate, packet count, last packet time and TS-gap estimate. Explain the measurement limits.
6. Stop broadcasting and show that new packet reception ceases after buffers drain.
## Evidence to record for the report
Record the real machine addresses, network type, number of active channels, number of receivers, observed bitrate and whether playback was audible and stable. Capture screenshots of both receivers and the dashboard. If using a packet analyzer, record its TCP directory exchange, multicast destination and UDP ports. Do not report hypothetical capacity calculations as measured results.
## Short introduction for speaking
Our project is Airwave, a Python application for multicast television and radio over a local IP network. We use TCP to share the channel directory and UDP multicast to transmit media to interested receivers. FFmpeg prepares the live stream and VLC plays it. We added a channel editor and a dashboard to observe incoming traffic and estimate stream continuity gaps.

# 12 Troubleshooting and common errors
## The app does not open
Run run.bat from an extracted project folder. If it closes early, use the manual commands in section 5 so you can read the error. Check Python, Tkinter, dependency installation and folder write permission. A missing or invalid stations.json produces a configuration error; restore a valid nonempty channel list.
## VLC cannot be loaded
Install native desktop VLC matching Python architecture and restart the app. python-vlc is only a binding. The application also recognizes its optional project-local portable VLC directory when present, but that directory is not part of the GitHub source download.
## The picture plays without sound
Uncheck Mute, raise the app volume and check the operating system mixer and output device. Test Studio One to distinguish a source-file problem from an audio-output problem. A source without an audio track cannot produce sound. Demo tracks should produce instrumental music.
## Opening or buffering persists
Confirm the broadcaster is running and the selected group and port match the sender. Check the chosen local adapter. For one-computer testing use 127.0.0.1; for several machines use each machine's actual LAN address. Inspect firewall rules and Wi-Fi isolation. Directory refresh succeeding only confirms TCP connectivity.
## Broadcasting fails or the port is busy
Only one directory can use TCP 5432 on the same listening address. Stop another GUI or headless broadcaster. Check station-N.log, where N is the channel ID, for FFmpeg details. Confirm source paths exist on the sender and media is readable and decodable. All configured channels start together, so one invalid file can interrupt startup.
## New channels do not appear
Save in Manage local channels, then click Show local channels. Restart the local broadcast after editing. Remote receivers must refresh the sender directory again to see updated metadata. A newly created local file path does not upload the file to another sender or to GitHub.
## Dashboard shows zero bitrate or gaps
With zero bitrate, check last packet age and whether the sender is active. If playback works but measurements are unavailable, the monitoring socket may have failed to bind or join. TS gaps can indicate loss or reordering; they can also rise after sender changes. Inspect the LAN and compare with an independent capture before claiming an exact loss rate.
## Safe shutdown
Stop playback and local broadcast, or close the main window. The application cleans up its own player, sockets and sender processes. Avoid broad commands that terminate every VLC or FFmpeg process on the machine.

# 13 Limitations improvements and references
## Current limits to state honestly
The project has no authentication, encryption or access-control layer. Treat it as a trusted lab LAN application. Multicast traffic is not confidential. Do not expose the directory or media services as a public production service.
Viewer count is not known because receivers do not register media sessions with the sender. Channel count has no small hard-coded cap, but it is limited by CPU, bandwidth, ports and directory response size. Each channel has its own encoder. Maximum concurrent viewers and channels have not been benchmarked.
The current system loops one source per channel. Playlists, scheduled programmes, recording, guaranteed reconnect and retransmission or forward-error correction are not implemented. Pausing is live-player buffering behavior, not a DVR promise. macOS embedded playback and broad cross-platform deployment need further work.
The application assumes a suitable multicast network, with TTL 1 by default. Wider routing requires network support and configuration. Increasing TTL alone does not make public internet multicast available.
## Practical future improvements
- Playlists and a now-playing display so each channel can schedule multiple tracks.
- Automatic reconnect with clear timeout and retry status after interruptions.
- Receiver registration or heartbeats for an approximate active-listener count.
- Exportable measurement logs and repeatable multi-client performance experiments.
- Authentication for the directory and an appropriate security design for deployment.
- Quality settings and load measurements to study channel capacity on the actual sender.
## Reference material
[1] RFC 1112, Host Extensions for IP Multicasting. Membership and IPv4 multicast addressing. https://www.rfc-editor.org/rfc/rfc1112
[2] RFC 2365, Administratively Scoped IP Multicast. https://www.rfc-editor.org/rfc/rfc2365
[3] FFmpeg protocols documentation, UDP options and examples. https://ffmpeg.org/ffmpeg-protocols.html#udp
[4] Python socket documentation. https://docs.python.org/3/library/socket.html
[5] VideoLAN libVLC documentation. https://videolan.videolan.me/vlc/master/libvlc.html
[6] Project source and README at the Arijai2007 repository. The implementation details and reported checks in this guide refer to version a755a6b, rather than the older C report.

# 14 Viva questions on the project basics
## 1 What is the aim of your project
To demonstrate live audio and video delivery from one broadcaster to multiple receivers using IP multicast, with TCP station discovery, a desktop player and network measurements.
## 2 Why is this a Computer Networks project
It uses TCP and UDP sockets, multicast groups, IP addresses, ports, interfaces and concurrent reception. The demonstration compares reliable control traffic with live media distribution.
## 3 Is the project terminal based
Its main interface is a Tkinter desktop GUI. A headless sender mode is available through the command line for broadcasting without the GUI.
## 4 What is the difference between unicast multicast and broadcast
Unicast targets one destination. Multicast targets members of a group. Broadcast targets all hosts in a broadcast domain. Airwave sends one media stream per channel to a multicast group.
## 5 What does multimedia over IP mean
It means audio and video are represented digitally and transported in IP packets. Here MPEG-TS media data is carried in UDP over IPv4.
## 6 Which language and libraries do you use
Python runs the application. Tkinter supplies the GUI, socket and socketserver support networking, python-vlc controls libVLC, and imageio-ffmpeg supplies FFmpeg.
## 7 What did you implement yourselves
The application integrates station validation and saving, channel editing, TCP discovery, FFmpeg process control, player controls and passive network measurements. The codecs and media decoding come from existing libraries.
## 8 Why did you choose Python
Python provides portable socket APIs and a standard GUI toolkit, which makes the networking application easier to develop and explain. Media processing is delegated to native tools rather than performed in Python loops.
## 9 Can the project run without internet
After dependencies are installed, the default generated channels can run offline on one machine or an appropriate LAN. Internet is required for initial software downloads and repository access.
## 10 What is a channel in this project
A saved record containing an ID, name, description, multicast group, UDP port and media source. The group and port identify the live stream that receivers tune to.

# 15 Viva questions on networking
## 11 Why use TCP for station discovery
The directory response should arrive completely and in order. TCP provides an ordered reliable byte stream, and the app adds newline framing and validation for the metadata message.
## 12 Why use UDP for the media
UDP works with IP multicast and does not require a separate reliable media connection per viewer. The tradeoff is that delivery and order are not guaranteed, and this app does not recover missing packets.
## 13 What is a multicast group address
It identifies a receiver group rather than a particular computer. Studio One uses 239.192.4.1. A receiver joins the group on a chosen local interface to receive that channel.
## 14 What is IGMP
Internet Group Management Protocol supports IPv4 multicast group membership between hosts and nearby network equipment. The operating system manages protocol exchanges when applications request membership.
## 15 What is the purpose of TTL
Time To Live limits IP packet lifetime through routing hops. The default TTL of 1 keeps this demonstration on the local segment; broader multicast requires routing support as well as suitable TTL.
## 16 What is the difference between Directory host and Local IPv4
Directory host identifies the computer providing TCP metadata. Local IPv4 selects this computer's own adapter for multicast. On a receiver, these addresses usually belong to different machines.
## 17 Why is 127.0.0.1 unsuitable for another computer
It is a loopback address referring to the computer that uses it. A remote receiver must contact the sender's actual LAN address instead.
## 18 What is the role of a port
A port identifies a transport endpoint or service on a host or group address. TCP 5432 is the directory service; UDP 5433 and 5434 are the default channel destinations.
## 19 Does multicast guarantee lower traffic everywhere
No. It avoids separate identical media copies at the sender for every viewer, but network devices still replicate traffic on required links. Wi-Fi airtime and forwarding behavior affect actual performance.
## 20 Does this project use RTP
No. It sends MPEG-TS directly over UDP multicast. RTP could be introduced in a future design, but should not be claimed as part of this implementation.

# 16 Viva questions on media and implementation
## 21 What is FFmpeg doing
It reads media at playback speed, encodes H.264 video and AAC audio as applicable, multiplexes MPEG-TS and sends it to the channel's UDP multicast destination.
## 22 What is VLC doing
libVLC joins and receives the media stream, buffers it, decodes audio and video, and renders playback inside the application. python-vlc exposes its control interface to Python.
## 23 Why use MPEG TS instead of concatenating MP4 chunks
MPEG-TS is designed for transport streams and carries repeated synchronization and programme information. An arbitrary MP4 fragment may depend on metadata that a receiver joining mid-file never received.
## 24 Why choose 1316 byte datagrams
1316 bytes carries seven 188-byte MPEG-TS packets and fits under a common 1500-byte IPv4 MTU with typical IP and UDP headers. This reduces fragmentation risk on such networks.
## 25 What are keyframes and why do they matter
Keyframes provide independently decodable video reference points. Regular keyframes help a new receiver begin decoding a running stream rather than waiting a long time for a usable reference.
## 26 How are audio only files handled
The sender uses optional media mappings. An audio-only source can transmit AAC audio without a video stream. A video source without audio remains silent.
## 27 How does the GUI remain responsive
Discovery and packet reception use workers, while the Tk main thread processes controls and queued results. Native player shutdown also runs in a worker to avoid blocking window-message processing.
## 28 How is configuration saved safely
The app validates station records and uniqueness first, writes a temporary file in the same directory, and atomically replaces stations.json. Invalid input does not overwrite the previous configuration.
## 29 How are local channels protected from remote discovery
The app keeps the local broadcaster configuration separate from the station list currently displayed. Refreshing a remote directory therefore does not redefine the local sources to broadcast.
## 30 How does the sender stop safely
It retains handles to its own FFmpeg processes, requests termination and escalates to killing those processes only if necessary. It closes associated membership sockets and the directory service.

# 17 Viva questions on measurements and evaluation
## 31 How do you calculate received bitrate
Measure the change in received UDP payload bytes over elapsed time, multiply by eight, and divide by 1000 to report kb/s. The reading excludes network and link headers.
## 32 How do you estimate packet loss
The monitor checks per-PID MPEG-TS payload continuity counters. Unexpected forward changes suggest missing TS packets. The result is labelled TS gaps because it is an estimate, not exact UDP loss.
## 33 Why can the loss estimate be wrong
Four-bit counters wrap. Reordering, duplicates, resets and local receive-buffer loss complicate interpretation. Missing a multiple of the counter range may also hide loss. An independent capture helps investigate.
## 34 Does buffering time equal network latency
No. It describes how long the player is observed opening or buffering. True end-to-end delay includes encoding, transport, buffering and decoding and needs a separate measurement method.
## 35 How many viewers can the server support
There is no fixed viewer limit configured in the application, and no measured maximum. Multicast avoids per-viewer media streams at the sender, but practical capacity depends on network delivery and receiver conditions.
## 36 How many channels can you add
There is no small hard-coded channel cap. CPU and bandwidth grow with one encoder per channel. Unique configuration values, available ports and the bounded directory response also constrain usable channel count.
## 37 What happens when the sender stops
New multicast packets stop arriving. Received bitrate falls, the last packet age rises, and playback may continue briefly from buffered media. Replaying after sender recovery may be necessary.
## 38 What testing have you completed
The local Windows suite passed 25 tests, and live checks verified media decoding and dashboard updates. These checks do not establish physical speaker audibility, large-network capacity or performance on every operating system.
## 39 What security features are present
Input validation and process isolation improve robustness, but the application has no authentication or encrypted transport. Its intended setting is a trusted lab LAN, not an unrestricted public deployment.
## 40 What would you improve next
Add playlists, reconnect behavior, measurement export and listener heartbeats, then run controlled multi-client and multi-channel experiments. Security and cross-platform packaging would be needed for wider deployment.
