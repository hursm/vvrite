"""Tests for clipboard helper functions."""

import unittest
from unittest.mock import patch

from Quartz import kCGEventFlagMaskCommand

from vvrite import clipboard


class TestClipboardHelpers(unittest.TestCase):
    @patch("vvrite.clipboard._post_keypress")
    def test_simulate_cmd_v_uses_command_modifier(self, mock_post_keypress):
        clipboard._simulate_cmd_v()

        mock_post_keypress.assert_called_once_with(
            clipboard.kVK_ANSI_V, kCGEventFlagMaskCommand
        )

    @patch("vvrite.clipboard._simulate_delete_backward")
    def test_retract_text_sends_delete_for_each_character(self, mock_delete):
        text = "한글 abc\n"

        result = clipboard.retract_text(text)

        self.assertTrue(result)
        mock_delete.assert_called_once_with(len(text))

    @patch("vvrite.clipboard._simulate_delete_backward")
    def test_retract_text_ignores_empty_text(self, mock_delete):
        self.assertFalse(clipboard.retract_text(""))
        mock_delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
