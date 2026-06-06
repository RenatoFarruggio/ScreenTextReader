from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.tts import play_wav, synthesize_to_wav  # noqa: E402


SAMPLE_TEXT = "Hallo, dies ist ein deutscher Test der Sprachausgabe."
VOICE_NAME = "de_DE-thorsten-medium"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
        output_path = Path(wav_file.name)

    try:
        synthesize_to_wav(SAMPLE_TEXT, VOICE_NAME, output_path)
        play_wav(output_path)
    finally:
        output_path.unlink(missing_ok=True)

    print(f"Played German TTS sample: {SAMPLE_TEXT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
