from __future__ import annotations

import logging
import threading

from src.capture import capture_screen
from src.config_store import AppConfig, GameProfile
from src.ocr import recognize_text
from src.ocr_preprocess import to_black_and_white
from src.tts import TtsWorker


class ReaderPipeline:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._tts_worker = TtsWorker(config.tts_voice)
        self._lock = threading.Lock()

    def update_config(self, config: AppConfig) -> None:
        self._config = config
        logging.info("Updated reader pipeline config")

    def stop(self) -> None:
        self._tts_worker.stop()

    def read_profile(self, profile: GameProfile) -> str:
        with self._lock:
            image = capture_screen(profile.effective_region)
            processed = to_black_and_white(image)
            text = recognize_text(processed, self._config.ocr_language)

            if not text:
                logging.info("OCR returned no text for profile '%s'", profile.display_name)
                return ""

            self._tts_worker.speak(text)
            logging.info("Queued OCR text for TTS (%d character(s))", len(text))
            return text
