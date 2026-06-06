from __future__ import annotations

import logging

import mss
from PIL import Image

from src.config_store import Region


def capture_screen(region: Region | None = None) -> Image.Image:
    with mss.mss() as screen:
        monitor = region.as_mss_monitor() if region else screen.monitors[0]
        screenshot = screen.grab(monitor)

    image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
    if region:
        logging.info(
            "Captured screenshot region left=%d top=%d width=%d height=%d",
            region.left,
            region.top,
            region.width,
            region.height,
        )
    else:
        logging.info("Captured full virtual screen screenshot")
    return image
