"""Tests for launch-at-login management."""

import unittest
from unittest.mock import MagicMock, patch

from vvrite import launch_at_login


class TestSupportDetection(unittest.TestCase):
    @patch("vvrite.launch_at_login.SMAppService", None)
    def test_reports_missing_bridge(self):
        self.assertEqual(
            launch_at_login.support_error(),
            "Launch at login is unavailable in this build.",
        )

    @patch("vvrite.launch_at_login.SMAppService", object())
    @patch("vvrite.launch_at_login._main_bundle_identifier", return_value="")
    @patch("vvrite.launch_at_login._main_bundle_path", return_value="/usr/local/bin/python")
    def test_requires_bundled_app(self, *_):
        self.assertEqual(
            launch_at_login.support_error(),
            "Launch at login is only available in the packaged app.",
        )

    @patch("vvrite.launch_at_login.SMAppService", object())
    @patch("vvrite.launch_at_login._main_bundle_identifier", return_value="com.vvrite.app")
    @patch("vvrite.launch_at_login._main_bundle_path", return_value="/Applications/vvrite.app")
    def test_detects_supported_environment(self, *_):
        self.assertTrue(launch_at_login.is_supported())


class TestStatusAndToggle(unittest.TestCase):
    def _patch_supported_service(self, service):
        return patch.multiple(
            "vvrite.launch_at_login",
            SMAppService=MagicMock(mainAppService=MagicMock(return_value=service)),
            _main_bundle_identifier=MagicMock(return_value="com.vvrite.app"),
            _main_bundle_path=MagicMock(return_value="/Applications/vvrite.app"),
        )

    def test_enabled_status_counts_as_registered(self):
        service = MagicMock()
        service.status.return_value = launch_at_login.STATUS_ENABLED

        with self._patch_supported_service(service):
            self.assertTrue(launch_at_login.is_registered())
            self.assertEqual(launch_at_login.status_message(), "Enabled")

    def test_requires_approval_counts_as_registered(self):
        service = MagicMock()
        service.status.return_value = launch_at_login.STATUS_REQUIRES_APPROVAL

        with self._patch_supported_service(service):
            self.assertTrue(launch_at_login.is_registered())
            self.assertIn("Needs approval", launch_at_login.status_message())

    def test_set_enabled_uses_service_registration(self):
        service = MagicMock()
        service.registerAndReturnError_.return_value = (True, None)
        service.status.return_value = launch_at_login.STATUS_ENABLED

        with self._patch_supported_service(service):
            self.assertTrue(launch_at_login.set_enabled(True))

        service.registerAndReturnError_.assert_called_once_with(None)

    def test_set_enabled_raises_on_error(self):
        service = MagicMock()
        service.registerAndReturnError_.return_value = (False, "bad signature")

        with self._patch_supported_service(service):
            with self.assertRaisesRegex(launch_at_login.LaunchAtLoginError, "bad signature"):
                launch_at_login.set_enabled(True)

    def test_set_disabled_unregisters(self):
        service = MagicMock()
        service.unregisterAndReturnError_.return_value = (True, None)
        service.status.return_value = launch_at_login.STATUS_NOT_REGISTERED

        with self._patch_supported_service(service):
            self.assertFalse(launch_at_login.set_enabled(False))

        service.unregisterAndReturnError_.assert_called_once_with(None)


if __name__ == "__main__":
    unittest.main()
