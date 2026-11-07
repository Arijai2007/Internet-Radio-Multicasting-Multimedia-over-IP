"""Load libVLC from a normal install or the optional portable tools folder."""
import os
from pathlib import Path
import sys
from .core import ROOT


def create_vlc(interface="", muted=False):
    if sys.platform == "win32":
        candidates = [ROOT / ".tools" / "vlc-3.0.21",
                      Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "VideoLAN/VLC"]
        for folder in candidates:
            if (folder / "libvlc.dll").exists():
                os.environ["PYTHON_VLC_LIB_PATH"] = str(folder / "libvlc.dll")
                os.environ["PYTHON_VLC_MODULE_PATH"] = str(folder)
                os.environ["VLC_PLUGIN_PATH"] = str(folder / "plugins")
                global _dll_directory
                _dll_directory = os.add_dll_directory(str(folder))
                break
    try:
        import vlc
        options = ["--no-video-title-show", "--network-caching=700"]
        if interface:
            options.append(f"--miface={interface}")
        if muted:
            options.append("--aout=dummy")
        instance = vlc.Instance(*options)
        if instance is None:
            raise RuntimeError("VLC could not initialize")
        return instance
    except (OSError, ImportError) as exc:
        raise RuntimeError("Install 64-bit VLC from videolan.org (matching your Python architecture), then restart the app.") from exc
