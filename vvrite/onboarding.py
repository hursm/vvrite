"""First-run onboarding wizard."""

import threading

import objc
import ApplicationServices
import AVFoundation
from AppKit import (
    NSObject,
    NSWindow,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSBackingStoreBuffered,
    NSTextField,
    NSFont,
    NSButton,
    NSColor,
    NSApp,
    NSBezelStyleRounded,
    NSView,
    NSImage,
    NSImageView,
    NSProgressIndicator,
    NSProgressIndicatorStyleBar,
)
from Foundation import NSMakeRect, NSLog, NSURL, NSWorkspace, NSTimer

from vvrite.widgets import ShortcutField
from vvrite import transcriber

# Window dimensions
_WIDTH = 400
_HEIGHT = 300

# Step indices
_WELCOME = 0
_PERMISSIONS = 1
_HOTKEY = 2
_MODEL = 3
_NUM_STEPS = 4


class OnboardingWindowController(NSObject):
    def initWithPreferences_statusBar_onComplete_(self, prefs, status_bar, on_complete):
        self = objc.super(OnboardingWindowController, self).init()
        if self is None:
            return None
        self._prefs = prefs
        self._status_bar = status_bar
        self._on_complete = on_complete
        self._step = _WELCOME
        self._window = None
        self._content_area = None
        self._dots = []
        self._back_btn = None
        self._next_btn = None
        self._permission_timer = None
        self._shortcut_field = None
        self._progress_bar = None
        self._progress_label = None
        self._size_label = None
        self._error_label = None
        self._retry_btn = None
        self._download_btn = None
        self._load_retries = 0
        self._local_model_path = None
        self._build_window()
        return self

    # --- Window ---

    def _build_window(self):
        frame = NSMakeRect(0, 0, _WIDTH, _HEIGHT)
        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_("vvrite")
        self._window.center()
        self._window.setDelegate_(self)

        root = self._window.contentView()

        # Dot indicator at top
        dot_y = _HEIGHT - 30
        dot_start_x = (_WIDTH - (_NUM_STEPS * 16)) / 2
        for i in range(_NUM_STEPS):
            dot = NSTextField.labelWithString_("●")
            dot.setFrame_(NSMakeRect(dot_start_x + i * 16, dot_y, 16, 16))
            dot.setAlignment_(1)  # center
            dot.setFont_(NSFont.systemFontOfSize_(10.0))
            root.addSubview_(dot)
            self._dots.append(dot)

        # Content area
        self._content_area = NSView.alloc().initWithFrame_(
            NSMakeRect(0, 50, _WIDTH, _HEIGHT - 80)
        )
        root.addSubview_(self._content_area)

        # Back / Next buttons
        self._back_btn = NSButton.alloc().initWithFrame_(NSMakeRect(20, 12, 80, 32))
        self._back_btn.setTitle_("Back")
        self._back_btn.setBezelStyle_(NSBezelStyleRounded)
        self._back_btn.setTarget_(self)
        self._back_btn.setAction_("backClicked:")
        root.addSubview_(self._back_btn)

        self._next_btn = NSButton.alloc().initWithFrame_(NSMakeRect(_WIDTH - 120, 12, 100, 32))
        self._next_btn.setTitle_("Get Started")
        self._next_btn.setBezelStyle_(NSBezelStyleRounded)
        self._next_btn.setTarget_(self)
        self._next_btn.setAction_("nextClicked:")
        root.addSubview_(self._next_btn)

        self._show_step(_WELCOME)

    def show(self):
        self._window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)

    def windowWillClose_(self, notification):
        if self._permission_timer:
            self._permission_timer.invalidate()
            self._permission_timer = None
        NSApp.terminate_(None)

    # --- Navigation ---

    def _show_step(self, step):
        self._step = step
        self._update_dots()

        # Clear content area
        for sub in list(self._content_area.subviews()):
            sub.removeFromSuperview()

        # Stop permission timer if leaving permissions step
        if step != _PERMISSIONS and self._permission_timer:
            self._permission_timer.invalidate()
            self._permission_timer = None

        builders = {
            _WELCOME: self._build_welcome,
            _PERMISSIONS: self._build_permissions,
            _HOTKEY: self._build_hotkey,
            _MODEL: self._build_model,
        }
        builders[step]()
        self._update_buttons()

    def _update_dots(self):
        for i, dot in enumerate(self._dots):
            if i <= self._step:
                dot.setTextColor_(NSColor.controlAccentColor())
            else:
                dot.setTextColor_(NSColor.tertiaryLabelColor())

    def _update_buttons(self):
        # Back button
        self._back_btn.setHidden_(self._step == _WELCOME)

        # Next button label
        labels = {
            _WELCOME: "Get Started",
            _PERMISSIONS: "Next",
            _HOTKEY: "Next",
            _MODEL: "Done",
        }
        self._next_btn.setTitle_(labels[self._step])

        # Next button enabled state
        if self._step == _PERMISSIONS:
            self._next_btn.setEnabled_(self._all_permissions_granted())
        elif self._step == _MODEL:
            self._next_btn.setEnabled_(transcriber.is_model_loaded())
        else:
            self._next_btn.setEnabled_(True)

    @objc.typedSelector(b"v@:@")
    def backClicked_(self, sender):
        if self._step > _WELCOME:
            self._show_step(self._step - 1)

    @objc.typedSelector(b"v@:@")
    def nextClicked_(self, sender):
        if self._step < _MODEL:
            self._show_step(self._step + 1)
        else:
            # Done — finish onboarding
            self._prefs.onboarding_completed = True
            if self._permission_timer:
                self._permission_timer.invalidate()
                self._permission_timer = None
            self._window.setDelegate_(None)
            self._window.close()
            self._on_complete()

    # --- Step 1: Welcome ---

    def _build_welcome(self):
        area = self._content_area
        w = _WIDTH

        # Icon
        icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "waveform", None
        )
        icon_view = NSImageView.alloc().initWithFrame_(
            NSMakeRect((w - 64) / 2, 120, 64, 64)
        )
        icon_view.setImage_(icon)
        icon_view.setContentTintColor_(NSColor.controlAccentColor())
        area.addSubview_(icon_view)

        # Title
        title = NSTextField.labelWithString_("vvrite")
        title.setFrame_(NSMakeRect(0, 88, w, 28))
        title.setFont_(NSFont.boldSystemFontOfSize_(22.0))
        title.setAlignment_(1)
        area.addSubview_(title)

        # Subtitle
        subtitle = NSTextField.labelWithString_("Voice to text, instantly.")
        subtitle.setFrame_(NSMakeRect(0, 64, w, 20))
        subtitle.setFont_(NSFont.systemFontOfSize_(13.0))
        subtitle.setTextColor_(NSColor.secondaryLabelColor())
        subtitle.setAlignment_(1)
        area.addSubview_(subtitle)

    # --- Step 2: Permissions ---

    def _all_permissions_granted(self):
        ax_ok = ApplicationServices.AXIsProcessTrusted()
        mic_ok = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(
            AVFoundation.AVMediaTypeAudio
        ) == 3
        return ax_ok and mic_ok

    def _build_permissions(self):
        area = self._content_area
        w = _WIDTH

        title = NSTextField.labelWithString_("Permissions")
        title.setFrame_(NSMakeRect(0, 170, w, 24))
        title.setFont_(NSFont.boldSystemFontOfSize_(16.0))
        title.setAlignment_(1)
        area.addSubview_(title)

        # Accessibility row
        self._acc_label = NSTextField.labelWithString_("Accessibility")
        self._acc_label.setFrame_(NSMakeRect(20, 130, 120, 20))
        self._acc_label.setFont_(NSFont.systemFontOfSize_(13.0))
        area.addSubview_(self._acc_label)

        acc_desc = NSTextField.labelWithString_("For global hotkey")
        acc_desc.setFrame_(NSMakeRect(20, 114, 150, 16))
        acc_desc.setFont_(NSFont.systemFontOfSize_(11.0))
        acc_desc.setTextColor_(NSColor.secondaryLabelColor())
        area.addSubview_(acc_desc)

        self._acc_status = NSTextField.labelWithString_("")
        self._acc_status.setFrame_(NSMakeRect(220, 122, 90, 20))
        self._acc_status.setFont_(NSFont.systemFontOfSize_(11.0))
        self._acc_status.setAlignment_(2)  # right
        area.addSubview_(self._acc_status)

        acc_btn = NSButton.alloc().initWithFrame_(NSMakeRect(320, 120, 60, 24))
        acc_btn.setTitle_("Open")
        acc_btn.setBezelStyle_(NSBezelStyleRounded)
        acc_btn.setTarget_(self)
        acc_btn.setAction_("openAccessibility:")
        area.addSubview_(acc_btn)

        # Microphone row
        mic_label = NSTextField.labelWithString_("Microphone")
        mic_label.setFrame_(NSMakeRect(20, 80, 120, 20))
        mic_label.setFont_(NSFont.systemFontOfSize_(13.0))
        area.addSubview_(mic_label)

        mic_desc = NSTextField.labelWithString_("For voice recording")
        mic_desc.setFrame_(NSMakeRect(20, 64, 150, 16))
        mic_desc.setFont_(NSFont.systemFontOfSize_(11.0))
        mic_desc.setTextColor_(NSColor.secondaryLabelColor())
        area.addSubview_(mic_desc)

        self._mic_status = NSTextField.labelWithString_("")
        self._mic_status.setFrame_(NSMakeRect(220, 72, 90, 20))
        self._mic_status.setFont_(NSFont.systemFontOfSize_(11.0))
        self._mic_status.setAlignment_(2)
        area.addSubview_(self._mic_status)

        mic_btn = NSButton.alloc().initWithFrame_(NSMakeRect(320, 70, 60, 24))
        mic_btn.setTitle_("Open")
        mic_btn.setBezelStyle_(NSBezelStyleRounded)
        mic_btn.setTarget_(self)
        mic_btn.setAction_("openMicrophonePrivacy:")
        area.addSubview_(mic_btn)

        self._update_permission_status()
        self._permission_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            2.0, self, "pollPermissions:", None, True
        )

    def _update_permission_status(self):
        ax_ok = ApplicationServices.AXIsProcessTrusted()
        mic_ok = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(
            AVFoundation.AVMediaTypeAudio
        ) == 3

        self._acc_status.setStringValue_("Granted" if ax_ok else "Not Granted")
        self._acc_status.setTextColor_(
            NSColor.systemGreenColor() if ax_ok else NSColor.systemRedColor()
        )
        self._mic_status.setStringValue_("Granted" if mic_ok else "Not Granted")
        self._mic_status.setTextColor_(
            NSColor.systemGreenColor() if mic_ok else NSColor.systemRedColor()
        )
        self._update_buttons()

    @objc.typedSelector(b"v@:@")
    def pollPermissions_(self, timer):
        if self._step == _PERMISSIONS:
            self._update_permission_status()

    @objc.typedSelector(b"v@:@")
    def openAccessibility_(self, sender):
        url = NSURL.URLWithString_(
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
        )
        NSWorkspace.sharedWorkspace().openURL_(url)

    @objc.typedSelector(b"v@:@")
    def openMicrophonePrivacy_(self, sender):
        status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(
            AVFoundation.AVMediaTypeAudio
        )
        if status == 0:  # NotDetermined — trigger system dialog
            AVFoundation.AVCaptureDevice.requestAccessForMediaType_completionHandler_(
                AVFoundation.AVMediaTypeAudio, lambda granted: None
            )
        else:  # Denied/Restricted — open System Settings
            url = NSURL.URLWithString_(
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"
            )
            NSWorkspace.sharedWorkspace().openURL_(url)

    # --- Step 3: Hotkey ---

    def _build_hotkey(self):
        area = self._content_area
        w = _WIDTH

        title = NSTextField.labelWithString_("Hotkey")
        title.setFrame_(NSMakeRect(0, 170, w, 24))
        title.setFont_(NSFont.boldSystemFontOfSize_(16.0))
        title.setAlignment_(1)
        area.addSubview_(title)

        subtitle = NSTextField.labelWithString_("Press to start/stop recording")
        subtitle.setFrame_(NSMakeRect(0, 150, w, 18))
        subtitle.setFont_(NSFont.systemFontOfSize_(12.0))
        subtitle.setTextColor_(NSColor.secondaryLabelColor())
        subtitle.setAlignment_(1)
        area.addSubview_(subtitle)

        self._shortcut_field = ShortcutField.alloc().initWithFrame_preferences_(
            NSMakeRect((w - 200) / 2, 100, 200, 32), self._prefs
        )
        self._shortcut_field.setFont_(NSFont.monospacedSystemFontOfSize_weight_(20.0, 0.5))
        self._shortcut_field.setAlignment_(1)
        area.addSubview_(self._shortcut_field)

        change_btn = NSButton.alloc().initWithFrame_(NSMakeRect((w - 80) / 2, 64, 80, 24))
        change_btn.setTitle_("Change")
        change_btn.setBezelStyle_(NSBezelStyleRounded)
        change_btn.setTarget_(self)
        change_btn.setAction_("changeShortcut:")
        area.addSubview_(change_btn)

    @objc.typedSelector(b"v@:@")
    def changeShortcut_(self, sender):
        self._shortcut_field.startCapture()

    # --- Step 4: Model Download ---

    def _build_model(self):
        area = self._content_area
        w = _WIDTH

        title = NSTextField.labelWithString_("Model")
        title.setFrame_(NSMakeRect(0, 170, w, 24))
        title.setFont_(NSFont.boldSystemFontOfSize_(16.0))
        title.setAlignment_(1)
        area.addSubview_(title)

        # Model name
        name_label = NSTextField.labelWithString_(self._prefs.model_id)
        name_label.setFrame_(NSMakeRect(20, 138, w - 40, 20))
        name_label.setFont_(NSFont.systemFontOfSize_(12.0))
        name_label.setAlignment_(1)
        area.addSubview_(name_label)

        # Size label
        self._size_label = NSTextField.labelWithString_("Checking size...")
        self._size_label.setFrame_(NSMakeRect(20, 120, w - 40, 18))
        self._size_label.setFont_(NSFont.systemFontOfSize_(11.0))
        self._size_label.setTextColor_(NSColor.secondaryLabelColor())
        self._size_label.setAlignment_(1)
        area.addSubview_(self._size_label)

        # Progress bar (hidden initially)
        self._progress_bar = NSProgressIndicator.alloc().initWithFrame_(
            NSMakeRect(20, 90, w - 40, 8)
        )
        self._progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self._progress_bar.setMinValue_(0.0)
        self._progress_bar.setMaxValue_(100.0)
        self._progress_bar.setHidden_(True)
        area.addSubview_(self._progress_bar)

        # Progress text
        self._progress_label = NSTextField.labelWithString_("")
        self._progress_label.setFrame_(NSMakeRect(20, 70, w - 40, 18))
        self._progress_label.setFont_(NSFont.systemFontOfSize_(11.0))
        self._progress_label.setTextColor_(NSColor.secondaryLabelColor())
        self._progress_label.setAlignment_(1)
        self._progress_label.setHidden_(True)
        area.addSubview_(self._progress_label)

        # Error label (hidden)
        self._error_label = NSTextField.labelWithString_("")
        self._error_label.setFrame_(NSMakeRect(20, 50, w - 40, 18))
        self._error_label.setFont_(NSFont.systemFontOfSize_(11.0))
        self._error_label.setTextColor_(NSColor.systemRedColor())
        self._error_label.setAlignment_(1)
        self._error_label.setHidden_(True)
        area.addSubview_(self._error_label)

        # Download button
        self._download_btn = NSButton.alloc().initWithFrame_(
            NSMakeRect((w - 100) / 2, 44, 100, 32)
        )
        self._download_btn.setTitle_("Download")
        self._download_btn.setBezelStyle_(NSBezelStyleRounded)
        self._download_btn.setTarget_(self)
        self._download_btn.setAction_("downloadClicked:")
        area.addSubview_(self._download_btn)

        # Retry button (hidden)
        self._retry_btn = NSButton.alloc().initWithFrame_(
            NSMakeRect((w - 80) / 2, 44, 80, 32)
        )
        self._retry_btn.setTitle_("Retry")
        self._retry_btn.setBezelStyle_(NSBezelStyleRounded)
        self._retry_btn.setTarget_(self)
        self._retry_btn.setAction_("downloadClicked:")
        self._retry_btn.setHidden_(True)
        area.addSubview_(self._retry_btn)

        # Check model size in background
        threading.Thread(target=self._fetch_model_size, daemon=True).start()

    def _fetch_model_size(self):
        size = transcriber.get_model_size(self._prefs.model_id)
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateSizeLabel:", str(size), False
        )

    @objc.typedSelector(b"v@:@")
    def updateSizeLabel_(self, size_str):
        size = int(size_str)
        if size > 0:
            gb = size / (1024 ** 3)
            self._size_label.setStringValue_(f"~{gb:.1f} GB download")
        else:
            self._size_label.setStringValue_("Size unknown")

    @objc.typedSelector(b"v@:@")
    def downloadClicked_(self, sender):
        self._download_btn.setHidden_(True)
        self._retry_btn.setHidden_(True)
        self._error_label.setHidden_(True)
        self._progress_bar.setHidden_(False)
        self._progress_bar.setIndeterminate_(True)
        self._progress_bar.startAnimation_(None)
        self._progress_label.setHidden_(False)
        self._progress_label.setStringValue_("Downloading...")
        threading.Thread(target=self._do_download, daemon=True).start()

    def _do_download(self):
        model_id = self._prefs.model_id
        try:
            local_path = transcriber.download_model(model_id)
        except Exception as e:
            self.performSelectorOnMainThread_withObject_waitUntilDone_(
                "downloadFailed:", str(e), False
            )
            return

        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "downloadComplete:", local_path, False
        )

    @objc.typedSelector(b"v@:@")
    def downloadFailed_(self, error_msg):
        self._progress_bar.setHidden_(True)
        self._progress_label.setHidden_(True)
        self._error_label.setStringValue_(str(error_msg))
        self._error_label.setHidden_(False)
        self._retry_btn.setAction_("downloadClicked:")
        self._retry_btn.setHidden_(False)
        self._status_bar.setDownloadProgress_(-1)

    @objc.typedSelector(b"v@:@")
    def downloadComplete_(self, local_path):
        self._local_model_path = str(local_path)
        self._progress_label.setStringValue_("Loading model...")
        threading.Thread(
            target=self._do_load_model,
            args=(self._local_model_path,),
            daemon=True,
        ).start()

    def _do_load_model(self, local_path):
        try:
            transcriber.load_from_local(local_path)
        except Exception as e:
            self.performSelectorOnMainThread_withObject_waitUntilDone_(
                "modelLoadFailed:", str(e), False
            )
            return
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "modelLoadComplete:", None, False
        )

    @objc.typedSelector(b"v@:@")
    def modelLoadFailed_(self, error_msg):
        self._load_retries += 1
        self._progress_bar.setIndeterminate_(False)
        self._progress_bar.stopAnimation_(None)
        if self._load_retries >= 3:
            self._progress_bar.setHidden_(True)
            self._progress_label.setHidden_(True)
            self._error_label.setStringValue_("Model loading failed after 3 attempts")
            self._error_label.setHidden_(False)
            return
        self._progress_bar.setHidden_(True)
        self._progress_label.setHidden_(True)
        self._error_label.setStringValue_(str(error_msg))
        self._error_label.setHidden_(False)
        self._retry_btn.setAction_("retryLoad:")
        self._retry_btn.setHidden_(False)

    @objc.typedSelector(b"v@:@")
    def retryLoad_(self, sender):
        if self._local_model_path is None:
            return
        self._retry_btn.setHidden_(True)
        self._error_label.setHidden_(True)
        self._progress_bar.setHidden_(False)
        self._progress_bar.setIndeterminate_(True)
        self._progress_bar.startAnimation_(None)
        self._progress_label.setStringValue_("Loading model...")
        self._progress_label.setHidden_(False)
        threading.Thread(
            target=self._do_load_model,
            args=(self._local_model_path,),
            daemon=True,
        ).start()

    @objc.typedSelector(b"v@:@")
    def modelLoadComplete_(self, _):
        self._progress_bar.setIndeterminate_(False)
        self._progress_bar.stopAnimation_(None)
        self._progress_bar.setDoubleValue_(100.0)
        self._progress_label.setStringValue_("Model ready!")
        self._update_buttons()
