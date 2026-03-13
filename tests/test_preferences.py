"""Tests for preferences module."""
import unittest
from Foundation import NSUserDefaults


# Keys that tests may modify — cleaned up before each test
_TEST_KEYS = [
    "hotkey_keycode", "hotkey_modifiers", "mic_device",
    "model_id", "max_tokens", "launch_at_login", "sound_start", "sound_stop",
    "onboarding_completed", "custom_words", "auto_update_check", "last_update_check",
]


class TestPreferences(unittest.TestCase):
    def setUp(self):
        defaults = NSUserDefaults.standardUserDefaults()
        for key in _TEST_KEYS:
            defaults.removeObjectForKey_(key)

    def tearDown(self):
        defaults = NSUserDefaults.standardUserDefaults()
        for key in _TEST_KEYS:
            defaults.removeObjectForKey_(key)

    def test_default_hotkey_keycode(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertEqual(prefs.hotkey_keycode, 0x31)

    def test_default_hotkey_modifiers(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        from Quartz import kCGEventFlagMaskAlternate
        expected = int(kCGEventFlagMaskAlternate)
        self.assertEqual(prefs.hotkey_modifiers, expected)

    def test_default_mic_device_is_none(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertIsNone(prefs.mic_device)

    def test_default_max_tokens(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertEqual(prefs.max_tokens, 128000)

    def test_default_model_id(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertEqual(prefs.model_id, "mlx-community/Qwen3-ASR-1.7B-8bit")

    def test_default_sounds(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertEqual(prefs.sound_start, "Glass")
        self.assertEqual(prefs.sound_stop, "Purr")

    def test_default_launch_at_login(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertFalse(prefs.launch_at_login)

    def test_set_and_get_hotkey_keycode(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        prefs.hotkey_keycode = 0x00  # 'A'
        self.assertEqual(prefs.hotkey_keycode, 0x00)

    def test_set_and_get_mic_device(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        prefs.mic_device = "Blue Yeti"
        self.assertEqual(prefs.mic_device, "Blue Yeti")

    def test_set_mic_device_to_none(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        prefs.mic_device = "Blue Yeti"
        prefs.mic_device = None
        self.assertIsNone(prefs.mic_device)

    def test_default_onboarding_completed(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertFalse(prefs.onboarding_completed)

    def test_set_onboarding_completed(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        prefs.onboarding_completed = True
        self.assertTrue(prefs.onboarding_completed)

    def test_default_custom_words(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertEqual(prefs.custom_words, "")

    def test_set_custom_words(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        prefs.custom_words = "MLX, Qwen, vvrite"
        self.assertEqual(prefs.custom_words, "MLX, Qwen, vvrite")

    def test_default_auto_update_check(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertTrue(prefs.auto_update_check)

    def test_set_auto_update_check(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        prefs.auto_update_check = False
        self.assertFalse(prefs.auto_update_check)

    def test_default_last_update_check(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        self.assertEqual(prefs.last_update_check, 0.0)

    def test_set_last_update_check(self):
        from vvrite.preferences import Preferences
        prefs = Preferences()
        prefs.last_update_check = 1234567890.0
        self.assertAlmostEqual(prefs.last_update_check, 1234567890.0)


if __name__ == "__main__":
    unittest.main()
