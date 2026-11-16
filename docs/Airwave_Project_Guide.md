# Airwave Computer Networks Project Report
## Internet Radio Multicasting Multimedia over IP
Airwave is a Python desktop application that demonstrates audio and video delivery over a local IP network. A broadcaster sends each channel to a multicast group, and receivers select the channel they want to play. The system combines reliable station discovery with live media distribution.
## Abstract
Sending a separate copy of the same media stream to each viewer increases the sender's traffic as the audience grows. This project uses UDP multicast to send one stream per channel and TCP to provide the channel directory. A Windows desktop interface supports broadcasting, playback, local channel editing and network observation.
Python implements the application and networking controls. FFmpeg encodes media and transmits MPEG-TS; libVLC decodes and plays it. The dashboard reports received bitrate, packet count, buffering state and estimated stream continuity gaps. Local automated and live checks verify operation, while larger LAN capacity remains an evaluation task.
## Purpose of this report
This report explains the problem, objectives, design, implementation, operation and verification of the project. A new reader can follow the Windows setup, understand each control, add a media channel, run a LAN demonstration and prepare for the viva. Actual functions are distinguished from future enhancements.
## Project information
Academic subject: Computer Networks
Application: Airwave
Implementation language: Python
Primary demonstration environment: Windows on a multicast-capable LAN
Repository owner: Arijai2007
Report date: 16 November 2026
Implementation reviewed: a755a6b
Repository: https://github.com/Arijai2007/Internet-Radio-Multicasting-Multimedia-over-IP

# Contents
1 Project overview and meaning
2 Included features and requirements
3 Architecture and end to end operation
4 Networking concepts and configuration
5 Windows installation and first run
6 Main window connection and channel controls
7 Playback broadcast and window controls
8 Demonstration across multiple computers
9 Adding a new media channel step by step
10 Channel editor buttons fields and saved changes
11 Network dashboard and measurements
12 Source code and implementation walkthrough
13 Verification and presentation procedure
14 Troubleshooting and common errors
15 Limitations improvements and references
16 Viva questions on the project basics
17 Viva questions on networking
18 Viva questions on media and implementation
19 Viva questions on measurements and evaluation

Read the report in order for a full explanation. For a first practical session, use Windows installation and first run, the two main-window control chapters, and Adding a new media channel step by step. The final four chapters contain 40 viva questions with answers.

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
This report follows the Windows desktop workflow used for local verification. Install the dependencies before the demonstration; the generated demo channels then work offline.

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
## What to expect during startup
The launcher creates a private Python environment and installs the listed dependencies before opening Airwave. On later runs it checks those dependencies again. You do not need to enter networking commands for normal operation. If installation fails, read the message in the launcher window and check Python, internet connectivity and folder permissions.
Stop and Stop local broadcast perform different actions. The first stops your player; the second stops media transmission and the directory on this computer. Close the main window to clean up both.

# 6 Main window connection and channel controls
## Understand the two roles first
A broadcaster sends media; a receiver plays it. Airwave can perform both roles on one computer, which is useful for a local test. In a multi-computer demonstration, normally only the sender starts broadcasting. Receiver computers refresh the sender's directory and play its channels.
## Directory host field
Enter the IP address or hostname of the computer providing the channel directory. For a same-computer test use 127.0.0.1. On a remote receiver, use the sender's LAN address, for example 192.168.1.10. This field is used by Refresh stations; changing it alone does not start a connection or change playback.
## Local IPv4 field
Enter this computer's own adapter IPv4 address before starting broadcasting or playback. Use 127.0.0.1 for the local test. On a LAN receiver use its own address, not the sender's address. A blank value lets the operating system choose a route. Apply a changed value by stopping and restarting the relevant broadcast or playback.
## Refresh stations button
Connects to Directory host through TCP port 5432, validates the channel information and replaces the visible station list with the received records. It does not start playback or broadcasting and does not overwrite your saved local channels. The button is temporarily disabled while the request is running. If it fails, read the status message and check the sender and address.
## Station library and Play selected station button
Single-click a channel to select it; selection alone does not tune the player. Click Play selected station, or double-click the channel, to stop any previous playback and join the selected stream. A short opening or buffering delay is normal. The sender must already be transmitting that group and port. The selected name and description identify what is playing.
## Show local channels button
Restores the main list from the channels saved on this computer. Use it after viewing a remote directory or after editing local channels. It changes the visible list without automatically stopping current playback or starting a broadcast.
## Manage local channels button
Opens the editor for this computer's saved channels. It always edits local records, even if the main station list currently came from another sender. Opening the editor does not itself stop or alter a broadcast. Saving a change stops local playback and broadcasting, with confirmation if the broadcast is active.

# 7 Playback broadcast and window controls
## Start local broadcast button
Starts the TCP directory and an FFmpeg sender for every saved local channel. It does not merely start the highlighted channel and does not automatically play anything. After clicking it, select a channel and press Play selected station if this computer should also receive.
Only the intended sender needs this button during a LAN demonstration. Clicking it while this app's directory is already running does not start another copy. If another program occupies TCP 5432, or a media source cannot be opened, an error is shown or reported in the status area and station log.
## Stop local broadcast button
Stops this app's media senders and its TCP directory. Other receivers will no longer receive new live packets and cannot refresh from this directory. They may continue playing briefly from their buffers. This button does not directly close the local player; click Stop as well when ending a demonstration.
## Pause and Resume button
The first click asks VLC to pause the current player. The next click asks it to resume. It does not pause the sender or other viewers. Network traffic can continue while playback is paused, so the dashboard can still show incoming packets. This is live playback, not a guaranteed recording or seekable pause buffer.
## Stop button
Stops only this computer's player, leaves its current multicast reception, and clears the session dashboard and graph. It does not stop any local broadcaster. To watch again, select a channel and click Play selected station. Use Stop local broadcast separately if this computer is also the sender.
## Mute checkbox and Volume slider
Mute turns this player's sound off without stopping video or reception. Uncheck it to hear sound again. The slider changes the local player volume from 0 to 100; it cannot change other receivers or the source recording. The system mixer, output device and source audio track also determine what you hear.
## Window close and status display
The main window X closes Airwave and cleans up its own player, monitor, local senders and directory. Minimize hides the window without stopping the session. Maximize changes the available viewing area. The editor's Close button only closes the editor.
The status line shows opening, playback or failure information. The content description identifies the channel, group and port. Dashboard values are observations, not buttons. Check the sender and network when opening or buffering persists.
## Useful control sequences
To watch locally: Start local broadcast, select a channel, then Play selected station. To switch: select another channel and press Play. To finish completely: Stop, then Stop local broadcast, or close the main window.

# 8 Demonstration across multiple computers
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

# 9 Adding a new media channel step by step
## Prepare the media on the sender
Choose a song or video stored on the computer that will broadcast it. An audio file makes a radio channel; a video file makes a television channel if it contains video. A source without audio remains silent. Put the file in a stable location, since moving it later breaks the saved path.
For this example, create a channel named Music TV with ID 3, group 239.192.4.3 and UDP port 5435. Use any audio or video file you are entitled to demonstrate. These network values fit the default two-channel setup; review the editor's suggested values before saving.
## Create and save the channel
1. Open Airwave on the sender and click Manage local channels.
2. Click New channel. This prepares a blank new record with suggested values; it does not yet save anything.
3. Enter 3 in Channel ID and Music TV in Name. Add a description such as Our selected music video.
4. Enter 239.192.4.3 in Multicast IPv4 and 5435 in UDP port. Do not enter the sender's ordinary LAN address in the multicast field.
5. Click Choose file, select the song or video, and confirm the file chooser. The Media file field now contains its path. Choosing the file alone does not save the channel.
6. Click Save channel. If local broadcasting is active, confirm that it may stop. Saving also stops local playback. Invalid values produce an error; correct them and save again.
7. Confirm that Music TV appears in the editor list. Click Close to return to the main window. Saved channels persist after the app restarts.
## Start and verify the new stream
1. Click Show local channels if needed, then Start local broadcast. This restarts all saved local channels, including Music TV.
2. Select Music TV and click Play selected station. Expect your chosen media, not the original demo track. Audio-only playback may leave the video area black.
3. Check that UDP packet count increases and bitrate is above zero. For sound, uncheck Mute and raise both application and system volume.
4. On other computers, click Refresh stations using the sender's Directory host, then select Music TV and play it. The receivers do not need the media file itself.
If the channel appears but will not play, check the sender's media path, broadcast status, local adapter, firewall and group-port agreement. Adding a channel does not upload its media to GitHub or copy it to another broadcaster.

# 10 Channel editor buttons fields and saved changes
## Editor buttons
| Button | Action and expected result |
| New channel | Prepares suggested values for a new record. Nothing is saved yet. |
| Choose file | Selects a media path. Cancelling keeps the previous value. |
| Save channel | Validates and saves the record, then stops local playback and broadcasting. |
| Remove channel | Removes a selected record after confirmation, keeping its media file. One channel must remain. |
| Close | Closes only the editor. Unsaved field edits are not saved. |
Select a channel row in the editor to load its fields before editing or removing it. To rename a channel or choose another song, change the selected record and click Save channel. Editing fields without saving leaves the stored configuration unchanged.
## Meaning of every field
| Field | What to enter |
| Channel ID | A positive whole number unique within the saved list. It identifies the record, not a network port. |
| Name | A nonempty display name shown in the station library. |
| Description | Optional text explaining the channel content. |
| Multicast IPv4 | An IPv4 multicast destination group, such as 239.192.4.3. |
| UDP port | A whole number from 1024 to 65535. Keep each group and port pair unique; separate ports are simplest for a demonstration. |
| Media file | An existing local audio or video file path, or the exact word demo for generated content. |
## Where changes are stored
The application validates records before atomically replacing stations.json in the project folder. Relative media paths resolve from that folder; file-chooser paths can be absolute. Source files loop continuously. Selecting a different file replaces that channel's source; it does not create a playlist.
Declining the save confirmation keeps the existing broadcast and configuration. After saving, restart broadcasting; remote receivers must refresh. A familiar file extension does not guarantee the media is decodable.

# 11 Network dashboard and measurements
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

# 12 Source code and implementation walkthrough
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

# 13 Verification and presentation procedure
## Checks supplied with the project
Run the automated checks from the project folder after activating the environment, or use its Python executable explicitly:
```powershell
.\.venv\Scripts\python -m pip install pytest
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m tests.playback_check
.\.venv\Scripts\python -m tests.dashboard_check
```
At report preparation, the current suite passed 25 tests on the local Windows environment. The tests cover invalid fields, duplicate records, Windows text encoding, safe saves, discovery, multicast reception, editor operations, local and remote configuration separation, continuity estimation and monitor cleanup.
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

# 14 Troubleshooting and common errors
## The app does not open
Run run.bat from an extracted project folder. If it closes early, read the error in the launcher window. Check Python, Tkinter, dependency installation and folder write permission. A missing or invalid stations.json produces a configuration error; restore a valid nonempty channel list.
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

# 15 Limitations improvements and references
## Current limits to state honestly
The project has no authentication, encryption or access-control layer. Treat it as a trusted lab LAN application. Multicast traffic is not confidential. Do not expose the directory or media services as a public production service.
Viewer count is not known because receivers do not register media sessions with the sender. Channel count has no small hard-coded cap, but it is limited by CPU, bandwidth, ports and directory response size. Each channel has its own encoder. Maximum concurrent viewers and channels have not been benchmarked.
The current system loops one source per channel. Playlists, scheduled programmes, recording, guaranteed reconnect and retransmission or forward-error correction are not implemented. Pausing is live-player buffering behavior, not a DVR promise. macOS embedded playback and broad cross-platform deployment need further work.
The application assumes a suitable multicast network, with TTL 1 by default. Wider routing requires network support and configuration. Increasing TTL alone does not make public internet multicast available.
## Project conclusion
Airwave demonstrates multicast media distribution through a working desktop application. TCP discovery tells receivers where channels are available; UDP multicast carries their media. Channel editing makes the sources configurable, and the dashboard connects user-visible playback with measurable network traffic. Local checks verify the implementation, while multi-computer capacity and broader deployment require further testing.
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
[6] Project source and README at the Arijai2007 repository. The implementation details and reported checks in this report refer to version a755a6b, rather than the older C report.

# 16 Viva questions on the project basics
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

# 17 Viva questions on networking
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

# 18 Viva questions on media and implementation
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

# 19 Viva questions on measurements and evaluation
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