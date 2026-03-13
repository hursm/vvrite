"""FFmpeg audio normalization."""

import os
import subprocess
import sys
import tempfile

from vvrite.preferences import FFMPEG_ARGS


def _resolve_ffmpeg() -> str:
    """Resolve ffmpeg binary: bundle first, then system fallbacks."""
    # PyInstaller sets _MEIPASS; py2app uses NSBundle
    base = getattr(sys, "_MEIPASS", None)
    if base:
        path = os.path.join(base, "ffmpeg")
        if os.path.isfile(path):
            return path
    try:
        from Foundation import NSBundle
        resource_path = NSBundle.mainBundle().resourcePath()
        if resource_path:
            path = os.path.join(resource_path, "ffmpeg")
            if os.path.isfile(path):
                return path
    except ImportError:
        pass
    for path in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if os.path.isfile(path):
            return path
    return "ffmpeg"


def normalize(input_path: str) -> str:
    """
    Normalize audio to 16kHz mono PCM s16le WAV using ffmpeg.
    Returns path to the normalized temporary WAV file.
    """
    fd, output_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    ffmpeg = _resolve_ffmpeg()

    subprocess.run(
        [ffmpeg, "-y", "-i", input_path] + FFMPEG_ARGS + [output_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return output_path
