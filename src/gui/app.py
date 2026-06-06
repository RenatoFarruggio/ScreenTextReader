from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from src.config_store import AppConfig, GameProfile, Region, load_config, save_config
from src.game_monitor import GameMonitor
from src.hotkey_handler import HotkeyHandler
from src.reader_pipeline import ReaderPipeline
from src.region_selector import select_region
from src.tts import download_voice, is_voice_installed


class ScreenTextReaderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ScreenTextReader")
        self.root.geometry("820x520")
        self.config = load_config()
        self.selected_profile_id: str | None = None
        self.selected_region: Region | None = None
        self.active_profile: GameProfile | None = None

        self.pipeline = ReaderPipeline(self.config)
        self.hotkey_handler = HotkeyHandler(self._on_hotkey)
        self.monitor = GameMonitor(
            self.config.profiles,
            self.config.poll_interval_seconds,
            self._on_active_profile_changed,
        )

        self._build_ui()
        self._load_global_settings()
        self._refresh_profiles()
        self.monitor.start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        list_frame = ttk.Frame(self.root, padding=10)
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.profile_tree = ttk.Treeview(
            list_frame,
            columns=("name", "process", "region", "hotkey"),
            show="headings",
            selectmode="browse",
        )
        self.profile_tree.heading("name", text="Name")
        self.profile_tree.heading("process", text="Process")
        self.profile_tree.heading("region", text="Region")
        self.profile_tree.heading("hotkey", text="Hotkey")
        self.profile_tree.grid(row=0, column=0, sticky="nsew")
        self.profile_tree.bind("<<TreeviewSelect>>", self._on_profile_selected)

        list_buttons = ttk.Frame(list_frame)
        list_buttons.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(list_buttons, text="New", command=self._new_profile).pack(side=tk.LEFT)
        ttk.Button(list_buttons, text="Delete", command=self._delete_profile).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(list_buttons, text="Test OCR + TTS", command=self._test_selected_profile).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        form = ttk.Frame(self.root, padding=10)
        form.grid(row=0, column=1, sticky="nsew")

        self.display_name = tk.StringVar()
        self.process_name = tk.StringVar()
        self.profile_hotkey = tk.StringVar()
        self.use_full_screen = tk.BooleanVar(value=True)
        self.global_hotkey = tk.StringVar()
        self.poll_interval = tk.StringVar()
        self.ocr_language = tk.StringVar()
        self.tts_voice = tk.StringVar()
        self.region_text = tk.StringVar(value="Full screen")
        self.status_text = tk.StringVar(value="No configured game is active")

        row = 0
        row = self._field(form, row, "Display name", self.display_name)
        row = self._field(form, row, "Process name", self.process_name)
        row = self._field(form, row, "Profile hotkey (optional)", self.profile_hotkey)

        ttk.Checkbutton(
            form,
            text="Use full screen",
            variable=self.use_full_screen,
            command=self._update_region_controls,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 0))
        row += 1

        ttk.Label(form, textvariable=self.region_text).grid(row=row, column=0, sticky="w")
        ttk.Button(form, text="Select region", command=self._select_region).grid(
            row=row, column=1, sticky="ew", pady=4
        )
        row += 1

        ttk.Separator(form).grid(row=row, column=0, columnspan=2, sticky="ew", pady=12)
        row += 1

        row = self._field(form, row, "Global hotkey", self.global_hotkey)
        row = self._field(form, row, "Poll interval seconds", self.poll_interval)
        row = self._field(form, row, "OCR language", self.ocr_language)
        row = self._field(form, row, "Piper voice", self.tts_voice)

        ttk.Button(form, text="Save", command=self._save).grid(row=row, column=0, sticky="ew")
        ttk.Button(form, text="Download voice", command=self._download_voice).grid(
            row=row, column=1, sticky="ew", padx=(8, 0)
        )
        row += 1

        ttk.Label(form, textvariable=self.status_text).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(18, 0),
        )

    def _field(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> int:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)
        parent.columnconfigure(1, weight=1)
        return row + 1

    def _load_global_settings(self) -> None:
        self.global_hotkey.set(self.config.global_hotkey)
        self.poll_interval.set(str(self.config.poll_interval_seconds))
        self.ocr_language.set(self.config.ocr_language)
        self.tts_voice.set(self.config.tts_voice)

    def _refresh_profiles(self) -> None:
        for item in self.profile_tree.get_children():
            self.profile_tree.delete(item)

        for profile in self.config.profiles:
            region = "Full screen" if profile.use_full_screen else self._format_region(profile.region)
            hotkey = profile.hotkey or self.config.global_hotkey
            self.profile_tree.insert(
                "",
                tk.END,
                iid=profile.id,
                values=(profile.display_name, profile.process_name, region, hotkey),
            )
            self.profile_tree.set(profile.id, "name", profile.display_name)
            self.profile_tree.set(profile.id, "process", profile.process_name)
            self.profile_tree.set(profile.id, "region", region)
            self.profile_tree.set(profile.id, "hotkey", hotkey)
        logging.info("Refreshed GUI profile list")

    def _format_region(self, region: Region | None) -> str:
        if region is None:
            return "No region"
        return f"{region.left},{region.top} {region.width}x{region.height}"

    def _on_profile_selected(self, _: tk.Event | None = None) -> None:
        selection = self.profile_tree.selection()
        if not selection:
            return
        profile = self._profile_by_id(selection[0])
        if profile is None:
            return

        self.selected_profile_id = profile.id
        self.selected_region = profile.region
        self.display_name.set(profile.display_name)
        self.process_name.set(profile.process_name)
        self.profile_hotkey.set(profile.hotkey or "")
        self.use_full_screen.set(profile.use_full_screen)
        self.region_text.set("Full screen" if profile.use_full_screen else self._format_region(profile.region))

    def _profile_by_id(self, profile_id: str) -> GameProfile | None:
        return next((profile for profile in self.config.profiles if profile.id == profile_id), None)

    def _new_profile(self) -> None:
        new_id = f"profile-{len(self.config.profiles) + 1}"
        profile = GameProfile(id=new_id, display_name="New Profile", process_name="game.exe")
        self.config.profiles.append(profile)
        self.selected_profile_id = profile.id
        self._refresh_profiles()
        self.profile_tree.selection_set(profile.id)
        self._on_profile_selected()

    def _delete_profile(self) -> None:
        if self.selected_profile_id is None:
            return
        self.config.profiles = [
            profile for profile in self.config.profiles if profile.id != self.selected_profile_id
        ]
        self.selected_profile_id = None
        self._refresh_profiles()
        logging.info("Deleted selected profile")

    def _select_region(self) -> None:
        region = select_region()
        if region is None:
            return
        self.selected_region = region
        self.use_full_screen.set(False)
        self.region_text.set(self._format_region(region))

    def _update_region_controls(self) -> None:
        if self.use_full_screen.get():
            self.region_text.set("Full screen")
        else:
            self.region_text.set(self._format_region(self.selected_region))

    def _save(self) -> None:
        self.config.global_hotkey = self.global_hotkey.get().strip() or "f9"
        self.config.poll_interval_seconds = int(self.poll_interval.get())
        self.config.ocr_language = self.ocr_language.get().strip() or "de-DE"
        self.config.tts_voice = self.tts_voice.get().strip() or "de_DE-thorsten-medium"

        if self.selected_profile_id is not None:
            profile = self._profile_by_id(self.selected_profile_id)
            if profile:
                profile.display_name = self.display_name.get().strip() or profile.id
                profile.process_name = self.process_name.get().strip()
                profile.hotkey = self.profile_hotkey.get().strip() or None
                profile.use_full_screen = self.use_full_screen.get()
                profile.region = None if profile.use_full_screen else self.selected_region

        save_config(self.config)
        self.pipeline.update_config(self.config)
        self.monitor.update_profiles(self.config.profiles, self.config.poll_interval_seconds)
        self._refresh_profiles()
        messagebox.showinfo("ScreenTextReader", "Configuration saved.")

    def _download_voice(self) -> None:
        voice_name = self.tts_voice.get().strip()
        if not voice_name:
            return

        def worker() -> None:
            try:
                download_voice(voice_name)
                self.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        "ScreenTextReader",
                        f"Voice installed: {voice_name}",
                    ),
                )
            except Exception as error:
                logging.exception("Voice download failed")
                self.root.after(0, lambda: messagebox.showerror("ScreenTextReader", str(error)))

        threading.Thread(target=worker, name="voice-download", daemon=True).start()

    def _test_selected_profile(self) -> None:
        if self.selected_profile_id is None:
            return
        profile = self._profile_by_id(self.selected_profile_id)
        if profile is None:
            return
        threading.Thread(
            target=lambda: self.pipeline.read_profile(profile),
            name="profile-test",
            daemon=True,
        ).start()

    def _on_active_profile_changed(self, profile: GameProfile | None) -> None:
        self.root.after(0, lambda: self._apply_active_profile(profile))

    def _apply_active_profile(self, profile: GameProfile | None) -> None:
        self.active_profile = profile
        if profile is None:
            self.hotkey_handler.deactivate()
            self.status_text.set("No configured game is active")
            return

        hotkey = profile.hotkey or self.config.global_hotkey
        self.hotkey_handler.activate(hotkey)
        self.status_text.set(
            f"Active: {profile.display_name} ({profile.process_name}) - Hotkey {hotkey.upper()}"
        )

    def _on_hotkey(self) -> None:
        if self.active_profile is None:
            return
        threading.Thread(
            target=lambda: self.pipeline.read_profile(self.active_profile),
            name="hotkey-reader",
            daemon=True,
        ).start()

    def _on_close(self) -> None:
        self.monitor.stop()
        self.hotkey_handler.deactivate()
        self.pipeline.stop()
        self.root.destroy()


def run_app() -> None:
    root = tk.Tk()
    app = ScreenTextReaderApp(root)
    if not is_voice_installed(app.config.tts_voice):
        app.status_text.set(
            f"Voice not installed: {app.config.tts_voice}. Use 'Download voice' before TTS."
        )
    root.mainloop()
