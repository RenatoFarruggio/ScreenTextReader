from __future__ import annotations

import tkinter as tk

import mss

from src.config_store import Region


class RegionSelector:
    def __init__(self) -> None:
        self._start_x = 0
        self._start_y = 0
        self._rect_id: int | None = None
        self._region: Region | None = None

    def select(self) -> Region | None:
        with mss.mss() as screen:
            monitor = screen.monitors[0]

        root = tk.Toplevel()
        root.title("Select OCR region")
        root.geometry(
            f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}"
        )
        root.attributes("-alpha", 0.35)
        root.attributes("-topmost", True)
        root.configure(bg="black")
        root.overrideredirect(True)

        canvas = tk.Canvas(root, cursor="crosshair", bg="black", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        def on_press(event: tk.Event) -> None:
            self._start_x = event.x_root
            self._start_y = event.y_root
            if self._rect_id is not None:
                canvas.delete(self._rect_id)
            self._rect_id = canvas.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline="white",
                width=3,
            )

        def on_drag(event: tk.Event) -> None:
            if self._rect_id is None:
                return
            x1 = self._start_x - monitor["left"]
            y1 = self._start_y - monitor["top"]
            x2 = event.x_root - monitor["left"]
            y2 = event.y_root - monitor["top"]
            canvas.coords(self._rect_id, x1, y1, x2, y2)

        def on_release(event: tk.Event) -> None:
            left = min(self._start_x, event.x_root)
            top = min(self._start_y, event.y_root)
            right = max(self._start_x, event.x_root)
            bottom = max(self._start_y, event.y_root)
            width = right - left
            height = bottom - top
            if width > 0 and height > 0:
                self._region = Region(left=left, top=top, width=width, height=height)

        def accept(_: tk.Event | None = None) -> None:
            root.destroy()

        def cancel(_: tk.Event | None = None) -> None:
            self._region = None
            root.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        root.bind("<Return>", accept)
        root.bind("<Escape>", cancel)
        root.focus_force()
        root.grab_set()
        root.wait_window()
        return self._region


def select_region() -> Region | None:
    return RegionSelector().select()
