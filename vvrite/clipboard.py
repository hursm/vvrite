"""Clipboard swap pattern: backup, write, paste, restore."""

import time
from AppKit import NSPasteboard, NSPasteboardItem, NSData, NSPasteboardTypeString
from Quartz import (
    CGEventSourceCreate,
    CGEventCreateKeyboardEvent,
    CGEventSetFlags,
    CGEventPost,
    kCGEventSourceStateHIDSystemState,
    kCGEventFlagMaskCommand,
    kCGHIDEventTap,
)

from vvrite.preferences import CLIPBOARD_RESTORE_DELAY

kVK_ANSI_V = 0x09


def backup() -> list:
    """Back up all clipboard items (preserves images, rich text, etc.)."""
    pb = NSPasteboard.generalPasteboard()
    items = pb.pasteboardItems()
    if not items:
        return []

    saved = []
    for item in items:
        item_data = {}
        for ptype in item.types():
            data = item.dataForType_(ptype)
            if data is not None:
                item_data[ptype] = NSData.dataWithData_(data)
        saved.append(item_data)
    return saved


def restore(saved: list):
    """Restore clipboard contents from a backup."""
    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    if not saved:
        return

    new_items = []
    for item_data in saved:
        pb_item = NSPasteboardItem.alloc().init()
        for ptype, data in item_data.items():
            pb_item.setData_forType_(data, ptype)
        new_items.append(pb_item)
    pb.writeObjects_(new_items)


def _set_text(text: str):
    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.setString_forType_(text, NSPasteboardTypeString)


def _simulate_cmd_v():
    source = CGEventSourceCreate(kCGEventSourceStateHIDSystemState)
    down = CGEventCreateKeyboardEvent(source, kVK_ANSI_V, True)
    up = CGEventCreateKeyboardEvent(source, kVK_ANSI_V, False)
    CGEventSetFlags(down, kCGEventFlagMaskCommand)
    CGEventSetFlags(up, kCGEventFlagMaskCommand)
    CGEventPost(kCGHIDEventTap, down)
    CGEventPost(kCGHIDEventTap, up)


def paste_and_restore(text: str):
    """Write text to clipboard, paste via Cmd-V, then restore original clipboard."""
    saved = backup()
    _set_text(text)
    time.sleep(0.05)
    _simulate_cmd_v()
    time.sleep(CLIPBOARD_RESTORE_DELAY)
    restore(saved)
