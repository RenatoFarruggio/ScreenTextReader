from __future__ import annotations

import logging
import queue
import subprocess
import sys
import tempfile
import threading
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sounddevice as sd


VOICE_FILES = {
    "de_DE-thorsten-medium": {
        "model": "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx",
        "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json",
    }
}


@dataclass(frozen=True, slots=True)
class PiperVoice:
    name: str
    model_path: Path
    config_path: Path


def voice_dir() -> Path:
    return Path.home() / "AppData" / "Local" / "ScreenTextReader" / "voices"


def get_voice(name: str) -> PiperVoice:
    directory = voice_dir() / name
    return PiperVoice(
        name=name,
        model_path=directory / f"{name}.onnx",
        config_path=directory / f"{name}.onnx.json",
    )


def is_voice_installed(name: str) -> bool:
    voice = get_voice(name)
    return voice.model_path.exists() and voice.config_path.exists()


def download_voice(name: str) -> PiperVoice:
    if name not in VOICE_FILES:
        raise ValueError(f"Unsupported Piper voice: {name}")

    voice = get_voice(name)
    voice.model_path.parent.mkdir(parents=True, exist_ok=True)
    files = VOICE_FILES[name]

    if not voice.model_path.exists():
        urllib.request.urlretrieve(files["model"], voice.model_path)
        logging.info("Downloaded Piper model to %s", voice.model_path)

    if not voice.config_path.exists():
        urllib.request.urlretrieve(files["config"], voice.config_path)
        logging.info("Downloaded Piper config to %s", voice.config_path)

    return voice


def ensure_voice(name: str) -> PiperVoice:
    voice = get_voice(name)
    if not is_voice_installed(name):
        return download_voice(name)
    logging.info("Piper voice is installed: %s", name)
    return voice


def synthesize_to_wav(text: str, voice_name: str, output_path: Path) -> None:
    voice = ensure_voice(voice_name)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as input_file:
        input_file.write(text)
        input_path = Path(input_file.name)

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "piper",
                "--model",
                str(voice.model_path),
                "--config",
                str(voice.config_path),
                "--input-file",
                str(input_path),
                "--output-file",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        input_path.unlink(missing_ok=True)

    logging.info("Synthesized %d character(s) to %s", len(text), output_path)


def _wav_to_array(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        frames = wav_file.readframes(wav_file.getnframes())

    if sample_width == 2:
        dtype = np.int16
    elif sample_width == 4:
        dtype = np.int32
    else:
        raise RuntimeError(f"Unsupported WAV sample width: {sample_width}")

    audio = np.frombuffer(frames, dtype=dtype)
    if channels > 1:
        audio = audio.reshape(-1, channels)
    return audio, sample_rate


def play_wav(path: Path) -> None:
    audio, sample_rate = _wav_to_array(path)
    sd.stop()
    sd.play(audio, sample_rate)
    sd.wait()
    logging.info("Played WAV output from %s", path)


class TtsWorker:
    def __init__(self, voice_name: str) -> None:
        self.voice_name = voice_name
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._thread = threading.Thread(target=self._run, name="tts-worker", daemon=True)
        self._thread.start()

    def speak(self, text: str) -> None:
        sd.stop()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        self._queue.put(text)

    def stop(self) -> None:
        sd.stop()
        self._queue.put(None)

    def _run(self) -> None:
        while True:
            text = self._queue.get()
            if text is None:
                logging.info("Stopped TTS worker")
                return

            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
                    output_path = Path(wav_file.name)
                synthesize_to_wav(text, self.voice_name, output_path)
                play_wav(output_path)
            except Exception:
                logging.exception("TTS failed")
            finally:
                output_path.unlink(missing_ok=True)
