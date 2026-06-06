from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

import psutil
import win32gui
import win32process

from src.config_store import GameProfile


ProfileCallback = Callable[[GameProfile | None], None]


def is_process_running(process_name: str) -> bool:
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == process_name:
            return True
    return False


def _foreground_process_name() -> str | None:
    window = win32gui.GetForegroundWindow()
    if not window:
        return None

    _, process_id = win32process.GetWindowThreadProcessId(window)
    if not process_id:
        return None

    try:
        return psutil.Process(process_id).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


class GameMonitor:
    def __init__(
        self,
        profiles: list[GameProfile],
        poll_interval_seconds: int,
        on_active_profile_changed: ProfileCallback,
    ) -> None:
        self._profiles = profiles
        self._poll_interval_seconds = poll_interval_seconds
        self._on_active_profile_changed = on_active_profile_changed
        self._active_profile: GameProfile | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def active_profile(self) -> GameProfile | None:
        return self._active_profile

    def update_profiles(self, profiles: list[GameProfile], poll_interval_seconds: int) -> None:
        self._profiles = profiles
        self._poll_interval_seconds = poll_interval_seconds
        logging.info("Updated monitor with %d profile(s)", len(profiles))

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="game-monitor", daemon=True)
        self._thread.start()
        logging.info("Started game monitor")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        logging.info("Stopped game monitor")

    def _matching_profiles(self) -> list[GameProfile]:
        return [
            profile
            for profile in self._profiles
            if profile.process_name and is_process_running(profile.process_name)
        ]

    def _select_active_profile(self, matches: list[GameProfile]) -> GameProfile | None:
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]

        foreground_name = _foreground_process_name()
        for profile in matches:
            if profile.process_name == foreground_name:
                return profile
        return matches[0]

    def _set_active_profile(self, profile: GameProfile | None) -> None:
        if self._active_profile and profile and self._active_profile.id == profile.id:
            return
        if self._active_profile is None and profile is None:
            return

        self._active_profile = profile
        if profile:
            logging.info("%s detected. Hotkey activated.", profile.process_name)
        else:
            logging.info("No configured game is active. Hotkey deactivated.")
        self._on_active_profile_changed(profile)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            matches = self._matching_profiles()
            self._set_active_profile(self._select_active_profile(matches))
            time.sleep(self._poll_interval_seconds)
