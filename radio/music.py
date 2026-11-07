"""Original synthesized arrangements of public-domain melodies, rendered offline."""
from array import array
import math
from pathlib import Path
import sys
import wave

RATE = 22050
# MIDI pitches and durations in beats; these melodies are public domain.
ODE = [(64,1),(64,1),(65,1),(67,1),(67,1),(65,1),(64,1),(62,1),
       (60,1),(60,1),(62,1),(64,1),(64,1.5),(62,.5),(62,2),
       (64,1),(64,1),(65,1),(67,1),(67,1),(65,1),(64,1),(62,1),
       (60,1),(60,1),(62,1),(64,1),(62,1.5),(60,.5),(60,2)]
TWINKLE = [(60,1),(60,1),(67,1),(67,1),(69,1),(69,1),(67,2),
           (65,1),(65,1),(64,1),(64,1),(62,1),(62,1),(60,2),
           (67,1),(67,1),(65,1),(65,1),(64,1),(64,1),(62,2),
           (67,1),(67,1),(65,1),(65,1),(64,1),(64,1),(62,2),
           (60,1),(60,1),(67,1),(67,1),(69,1),(69,1),(67,2),
           (65,1),(65,1),(64,1),(64,1),(62,1),(62,1),(60,2)]


def demo_music(station_id, folder):
    """Cache a piano-like melody with a soft arpeggiated accompaniment."""
    ode = station_id % 2 == 1
    target = Path(folder) / ("ode-to-joy-v1.wav" if ode else "twinkle-v1.wav")
    if target.is_file():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    melody = ODE if ode else TWINKLE
    beat = 60 / (112 if ode else 104)
    duration = sum(length for _, length in melody) * beat + .4
    samples = [0.0] * math.ceil(duration * RATE)

    def note(pitch, start, length, gain):
        frequency = 440 * 2 ** ((pitch - 69) / 12)
        count = int((length + .15) * RATE)
        offset = int(start * RATE)
        for i in range(min(count, len(samples) - offset)):
            t = i / RATE
            envelope = min(1, t / .008) * math.exp(-3 * t / max(length, .2))
            envelope *= min(1, (count - i) / (RATE * .04))
            tone = (math.sin(2 * math.pi * frequency * t)
                    + .28 * math.sin(4 * math.pi * frequency * t)
                    + .08 * math.sin(6 * math.pi * frequency * t))
            samples[offset + i] += gain * envelope * tone

    position = 0
    for pitch, beats in melody:
        note(pitch, position, beats * beat * .9, .40)
        position += beats * beat
    for tick in range(int(position / beat) * 2):
        # C, F and G accompaniment, repeating an eight-bar progression.
        chord = [(48,52,55), (48,52,55), (53,57,60), (55,59,62)][(tick // 8) % 4]
        note(chord[tick % 3], tick * beat / 2, beat * .65, .13)
    peak = max(1, max(abs(value) for value in samples))
    pcm = array("h", (int(value / peak * 28000) for value in samples))
    if sys.byteorder != "little":
        pcm.byteswap()
    # Publish atomically so playback never reads a partially rendered track.
    import os
    import tempfile
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".wav", delete=False) as temporary:
        temp_path = Path(temporary.name)
    try:
        with wave.open(str(temp_path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(RATE)
            output.writeframes(pcm.tobytes())
        os.replace(temp_path, target)
    finally:
        temp_path.unlink(missing_ok=True)
    return target
