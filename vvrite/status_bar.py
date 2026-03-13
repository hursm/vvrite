"""Menu bar status item and dropdown menu."""

import objc
from AppKit import (
    NSObject,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSMenu,
    NSMenuItem,
    NSApp,
    NSImage,
    NSColor,
)


class StatusBarController(NSObject):
    def initWithDelegate_(self, delegate):
        self = objc.super(StatusBarController, self).init()
        if self is None:
            return None
        self._delegate = delegate
        self._recording = False
        self._setup()
        return self

    def _setup(self):
        self._status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        button = self._status_item.button()
        button.setImage_(self._sf_symbol("exclamationmark.triangle"))
        button.setTitle_("")

        self._menu = NSMenu.alloc().init()

        # App title
        title_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "vvrite", None, ""
        )
        title_item.setEnabled_(False)
        self._menu.addItem_(title_item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # Status
        self._status_menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "● Ready", None, ""
        )
        self._status_menu_item.setEnabled_(False)
        self._menu.addItem_(self._status_menu_item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # Hotkey display
        self._hotkey_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Hotkey: ⌥Space", None, ""
        )
        self._hotkey_item.setEnabled_(False)
        self._menu.addItem_(self._hotkey_item)

        # Mic display
        self._mic_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Microphone: System Default", None, ""
        )
        self._mic_item.setEnabled_(False)
        self._menu.addItem_(self._mic_item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # Settings
        settings_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Settings...", "openSettings:", ","
        )
        settings_item.setTarget_(self)
        self._menu.addItem_(settings_item)

        # Check for Updates
        self._update_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Check for Updates...", "checkForUpdates:", ""
        )
        self._update_item.setTarget_(self)
        self._menu.addItem_(self._update_item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # Quit
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit vvrite", "terminate:", "q"
        )
        self._menu.addItem_(quit_item)

        self._status_item.setMenu_(self._menu)

    def _sf_symbol(self, name):
        return NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)

    def _update_icon(self, ready: bool):
        button = self._status_item.button()
        if ready:
            button.setImage_(self._sf_symbol("waveform"))
        else:
            button.setImage_(self._sf_symbol("exclamationmark.triangle"))

    def setStatus_(self, status: str):
        self._status_menu_item.setTitle_(f"● {status}")
        self._update_icon(status in ("Ready", "Recording...", "Transcribing..."))

    def setRecording_(self, recording: bool):
        self._recording = recording

    def setDownloadProgress_(self, percent: int):
        """Show download percentage on menu bar button. -1 to clear."""
        button = self._status_item.button()
        if percent < 0:
            button.setTitle_("")
        else:
            button.setTitle_(f"{percent}%")

    def setUpdateAvailable_(self, version: str):
        """Update menu item text when an update is available."""
        self._update_item.setTitle_(f"Update Available ({version})")

    @objc.typedSelector(b"v@:@")
    def openSettings_(self, sender):
        self._delegate.openSettings()

    @objc.typedSelector(b"v@:@")
    def checkForUpdates_(self, sender):
        self._delegate.checkForUpdates()
