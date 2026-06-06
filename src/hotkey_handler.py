from __future__ import annotations

import logging
from collections.abc import Callable

import keyboard


class HotkeyHandler:
    def __init__(self, callback: Callable[[], None]) -> None:
        self._callback = callback
        self._current_hotkey: str | None = None

    @property
    def current_hotkey(self) -> str | None:
        return self._current_hotkey

    def activate(self, hotkey: str) -> None:
        if self._current_hotkey == hotkey:
            return

        self.deactivate()
        keyboard.add_hotkey(hotkey, self._callback)
        self._current_hotkey = hotkey
        logging.info("Activated hotkey '%s'", hotkey.upper())

    def deactivate(self) -> None:
        if self._current_hotkey is None:
            return

        keyboard.remove_hotkey(self._current_hotkey)
        logging.info("Deactivated hotkey '%s'", self._current_hotkey.upper())
        self._current_hotkey = None
