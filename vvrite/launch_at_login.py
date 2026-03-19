"""Launch-at-login helpers backed by SMAppService."""

from __future__ import annotations

from Foundation import NSBundle

STATUS_NOT_REGISTERED = 0
STATUS_ENABLED = 1
STATUS_REQUIRES_APPROVAL = 2
STATUS_NOT_FOUND = 3

_STATUS_MESSAGES = {
    STATUS_NOT_REGISTERED: "Off",
    STATUS_ENABLED: "Enabled",
    STATUS_REQUIRES_APPROVAL: "Needs approval in System Settings > General > Login Items",
    STATUS_NOT_FOUND: "Login item not found",
}

try:
    from ServiceManagement import SMAppService
except ImportError:  # pragma: no cover - exercised via patched symbol in tests
    SMAppService = None


class LaunchAtLoginError(RuntimeError):
    """Raised when launch-at-login cannot be queried or changed."""


def _main_bundle():
    return NSBundle.mainBundle()


def _main_bundle_path() -> str:
    bundle = _main_bundle()
    path = bundle.bundlePath() if bundle else None
    return str(path or "")


def _main_bundle_identifier() -> str:
    bundle = _main_bundle()
    bundle_id = bundle.bundleIdentifier() if bundle else None
    return str(bundle_id or "")


def support_error() -> str | None:
    if SMAppService is None:
        return "Launch at login is unavailable in this build."

    bundle_path = _main_bundle_path()
    bundle_id = _main_bundle_identifier()
    if not bundle_id or not bundle_path.endswith(".app"):
        return "Launch at login is only available in the packaged app."

    return None


def is_supported() -> bool:
    return support_error() is None


def _service():
    error = support_error()
    if error:
        raise LaunchAtLoginError(error)
    service_factory = getattr(SMAppService, "mainAppService", None)
    if service_factory is None:
        service_factory = getattr(SMAppService, "mainApp", None)
    if service_factory is None:
        raise LaunchAtLoginError("Launch at login is unavailable in this build.")
    return service_factory()


def _unwrap_result(result):
    if isinstance(result, tuple):
        if len(result) == 2:
            return bool(result[0]), result[1]
        if len(result) == 1:
            return bool(result[0]), None
    return bool(result), None


def status() -> int:
    return int(_service().status())


def is_registered() -> bool:
    return status() in (STATUS_ENABLED, STATUS_REQUIRES_APPROVAL)


def status_message() -> str:
    return _STATUS_MESSAGES.get(status(), "Unknown status")


def set_enabled(enabled: bool) -> bool:
    service = _service()
    if enabled:
        ok, error = _unwrap_result(service.registerAndReturnError_(None))
    else:
        ok, error = _unwrap_result(service.unregisterAndReturnError_(None))

    if not ok:
        if error:
            raise LaunchAtLoginError(str(error))
        raise LaunchAtLoginError("ServiceManagement rejected the request.")

    return is_registered()
