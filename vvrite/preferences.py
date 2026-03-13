"""User preferences backed by NSUserDefaults."""

from Foundation import NSUserDefaults
from Quartz import kCGEventFlagMaskAlternate

_DEFAULTS = {
    "hotkey_keycode": 0x31,  # Space
    "hotkey_modifiers": int(kCGEventFlagMaskAlternate),
    # mic_device intentionally omitted — None/absent means system default
    "model_id": "mlx-community/Qwen3-ASR-1.7B-8bit",
    "max_tokens": 128000,
    "launch_at_login": False,
    "sound_start": "Glass",
    "sound_stop": "Purr",
    "onboarding_completed": False,
    "custom_words": "",
    "auto_update_check": True,
    "last_update_check": 0.0,
}

# Hard-coded constants (not user-configurable)
SAMPLE_RATE = 16000
CHANNELS = 1
CLIPBOARD_RESTORE_DELAY = 0.2
FFMPEG_ARGS = ["-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le"]


class Preferences:
    """Read/write app preferences via NSUserDefaults."""

    def __init__(self):
        self._defaults = NSUserDefaults.standardUserDefaults()
        self._defaults.registerDefaults_(_DEFAULTS)

    def _get(self, key):
        val = self._defaults.objectForKey_(key)
        if val is None:
            return _DEFAULTS.get(key)
        return val

    def _set(self, key, value):
        if value is None:
            self._defaults.removeObjectForKey_(key)
        else:
            self._defaults.setObject_forKey_(value, key)

    @property
    def hotkey_keycode(self) -> int:
        return int(self._get("hotkey_keycode"))

    @hotkey_keycode.setter
    def hotkey_keycode(self, value: int):
        self._set("hotkey_keycode", value)

    @property
    def hotkey_modifiers(self) -> int:
        return int(self._get("hotkey_modifiers"))

    @hotkey_modifiers.setter
    def hotkey_modifiers(self, value: int):
        self._set("hotkey_modifiers", value)

    @property
    def mic_device(self) -> str | None:
        val = self._defaults.objectForKey_("mic_device")
        if val is None:
            return None
        return str(val)

    @mic_device.setter
    def mic_device(self, value: str | None):
        self._set("mic_device", value)

    @property
    def model_id(self) -> str:
        return str(self._get("model_id"))

    @model_id.setter
    def model_id(self, value: str):
        self._set("model_id", value)

    @property
    def max_tokens(self) -> int:
        return int(self._get("max_tokens"))

    @max_tokens.setter
    def max_tokens(self, value: int):
        self._set("max_tokens", value)

    @property
    def launch_at_login(self) -> bool:
        return bool(self._get("launch_at_login"))

    @launch_at_login.setter
    def launch_at_login(self, value: bool):
        self._set("launch_at_login", value)

    @property
    def sound_start(self) -> str:
        return str(self._get("sound_start"))

    @sound_start.setter
    def sound_start(self, value: str):
        self._set("sound_start", value)

    @property
    def sound_stop(self) -> str:
        return str(self._get("sound_stop"))

    @sound_stop.setter
    def sound_stop(self, value: str):
        self._set("sound_stop", value)

    @property
    def custom_words(self) -> str:
        return str(self._get("custom_words"))

    @custom_words.setter
    def custom_words(self, value: str):
        self._set("custom_words", value)

    @property
    def onboarding_completed(self) -> bool:
        return bool(self._get("onboarding_completed"))

    @onboarding_completed.setter
    def onboarding_completed(self, value: bool):
        self._set("onboarding_completed", value)

    @property
    def auto_update_check(self) -> bool:
        return bool(self._get("auto_update_check"))

    @auto_update_check.setter
    def auto_update_check(self, value: bool):
        self._set("auto_update_check", value)

    @property
    def last_update_check(self) -> float:
        return float(self._get("last_update_check"))

    @last_update_check.setter
    def last_update_check(self, value: float):
        self._set("last_update_check", value)
