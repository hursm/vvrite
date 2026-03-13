"""System sound playback using NSSound."""

from AppKit import NSSound


def play(name: str):
    """Play a macOS system sound by name (non-blocking)."""
    sound = NSSound.soundNamed_(name)
    if sound:
        sound.play()
