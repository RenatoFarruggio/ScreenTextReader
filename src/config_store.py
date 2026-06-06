from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


CONFIG_PATH = Path("config.json")


@dataclass(slots=True)
class Region:
    left: int
    top: int
    width: int
    height: int

    def as_mss_monitor(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


@dataclass(slots=True)
class GameProfile:
    id: str
    display_name: str
    process_name: str
    use_full_screen: bool = True
    region: Region | None = None
    hotkey: str | None = None

    @property
    def effective_region(self) -> Region | None:
        if self.use_full_screen:
            return None
        return self.region


@dataclass(slots=True)
class AppConfig:
    global_hotkey: str = "f9"
    poll_interval_seconds: int = 5
    tts_voice: str = "de_DE-thorsten-medium"
    ocr_language: str = "de-DE"
    profiles: list[GameProfile] = field(default_factory=list)


def default_config() -> AppConfig:
    return AppConfig(
        profiles=[
            GameProfile(
                id="example-game",
                display_name="Example Game",
                process_name="example.exe",
            )
        ]
    )


def _profile_from_dict(data: dict[str, Any]) -> GameProfile:
    region_data = data.get("region")
    region = Region(**region_data) if isinstance(region_data, dict) else None
    return GameProfile(
        id=str(data["id"]),
        display_name=str(data["display_name"]),
        process_name=str(data["process_name"]),
        use_full_screen=bool(data.get("use_full_screen", True)),
        region=region,
        hotkey=data.get("hotkey"),
    )


def _config_from_dict(data: dict[str, Any]) -> AppConfig:
    profiles = [_profile_from_dict(profile) for profile in data.get("profiles", [])]
    return AppConfig(
        global_hotkey=str(data.get("global_hotkey", "f9")),
        poll_interval_seconds=int(data.get("poll_interval_seconds", 5)),
        tts_voice=str(data.get("tts_voice", "de_DE-thorsten-medium")),
        ocr_language=str(data.get("ocr_language", "de-DE")),
        profiles=profiles,
    )


def _to_jsonable(config: AppConfig) -> dict[str, Any]:
    data = asdict(config)
    return data


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    if not path.exists():
        config = default_config()
        save_config(config, path)
        logging.info("Created default config at %s", path)
        return config

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    config = _config_from_dict(data)
    logging.info("Loaded %d profile(s) from %s", len(config.profiles), path)
    return config


def save_config(config: AppConfig, path: Path = CONFIG_PATH) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(_to_jsonable(config), file, indent=2)
        file.write("\n")
    logging.info("Saved config with %d profile(s) to %s", len(config.profiles), path)
