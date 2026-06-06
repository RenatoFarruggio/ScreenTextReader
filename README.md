# ScreenTextReader

ScreenTextReader reads visible game dialogue aloud on Windows. It detects configured game
processes, enables a global hotkey while a configured game is running, captures the whole
screen or a saved region, runs Windows OCR, and speaks the recognized text with local Piper TTS.

## Setup

This project uses `uv` for the Python environment and dependency management.

Required on the machine:

- Windows 10/11.
- Python 3.12, managed by `uv` for this project.
- `uv` installed and available as `uv.exe`.
- Windows OCR language `de-DE` installed.
- Audio output device available for `sounddevice`.

If `uv` is missing, install it first:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

What has been installed/downloaded in this working copy:

- `uv` is available at `C:\Users\Bob\.local\bin\uv.exe`.
- Project dependencies were installed with:

```powershell
uv add psutil keyboard mss Pillow numpy piper-tts sounddevice winsdk pywin32
```

- The local virtual environment was created at `.venv`.
- The German Piper voice was downloaded to:

```text
C:\Users\Bob\AppData\Local\ScreenTextReader\voices\de_DE-thorsten-medium\
```

It is also okay to download the two files manually from a Piper voice list such as
`https://docs.gladecore.com/files/piper-voice-models`. The app needs both matching files:

```text
de_DE-thorsten-medium.onnx
de_DE-thorsten-medium.onnx.json
```

Place them in:

```text
C:\Users\Bob\AppData\Local\ScreenTextReader\voices\de_DE-thorsten-medium\
```

The manually downloaded files from this project root were moved there.

To set up from scratch on another machine:

```powershell
cd C:\Users\Bob\Documents\ScreenTextReader
uv sync
uv run python -c "from src.tts import ensure_voice; ensure_voice('de_DE-thorsten-medium')"
```

Check installed Windows OCR languages:

```powershell
uv run python -c "from winsdk.windows.media.ocr import OcrEngine; print([lang.language_tag for lang in OcrEngine.available_recognizer_languages])"
```

The expected OCR language for normal use is `de-DE`. If it is missing, install German in
Windows Settings under language options, then run the check again.

## Start

```powershell
uv run main.py
```

If the global hotkey does not trigger while a game is focused, start the terminal or app as
Administrator. Some games block non-admin global keyboard hooks.

## Configuration

Configuration is stored in `config.json`.

Each game profile contains:

- `display_name`: name shown in the GUI.
- `process_name`: executable name from Task Manager, for example `eldenring.exe`.
- `use_full_screen`: `true` captures the full virtual screen.
- `region`: saved screen rectangle for OCR when `use_full_screen` is `false`.
- `hotkey`: optional profile-specific hotkey. `null` uses `global_hotkey`.

The GUI can create/edit profiles, save the selected OCR region, download the Piper voice,
and run a test capture/OCR/TTS pass for the selected profile.

## OCR Test

The included sample images verify OCR preprocessing and text recognition:

```powershell
uv run scripts/test_ocr.py
```

Current result on this machine with `de-DE` Windows OCR:

- `sample_text_pipistrello.png`: 100% similarity.
- `sample_text_easy.png`: 100% similarity.

OCR output joins recognized lines with spaces before sending text to TTS, so dialogue split
over multiple lines is spoken as one sentence instead of containing newline characters.

## TTS Test

Run a German Piper TTS sample and play it through the default audio device:

```powershell
uv run scripts/test_tts.py
```

The sample sentence is:

```text
Hallo, dies ist ein deutscher Test der Sprachausgabe.
```

## Notes

- `autoclicker.py` is kept unchanged and only served as the process-monitoring reference.
- OCR preprocessing currently converts screenshots to black/white with a fixed threshold
  selected from the sample images. It also scales very small text regions before OCR.
- Piper TTS runs locally and uses the `de_DE-thorsten-medium` voice by default.
