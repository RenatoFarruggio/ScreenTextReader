# ScreenTextReader

ScreenTextReader reads visible game dialogue aloud on Windows. It detects configured game
processes, enables a global hotkey while a configured game is running, captures the whole
screen or a saved region, runs Windows OCR, and speaks the recognized text with local Piper TTS.

## Setup

This project uses `uv` for the Python environment and dependency management.

Required on the machine:

- Windows 10/11.
- Python 3.12, managed by `uv` for this project.
- `uv` installed.
- Windows OCR language `de-DE` installed.
- Audio output device available for `sounddevice`.

If `uv` is missing, install it first:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

From the project directory:

```powershell
uv sync
uv run python -c "from src.tts import ensure_voice; ensure_voice('de_DE-thorsten-medium')"
```

That downloads the German Piper voice to:

```text
C:\Users\<User>\AppData\Local\ScreenTextReader\voices\de_DE-thorsten-medium\
```

Alternatively, download the two files manually from a Piper voice list such as
`https://docs.gladecore.com/files/piper-voice-models`. The app needs both matching files:

```text
de_DE-thorsten-medium.onnx
de_DE-thorsten-medium.onnx.json
```

Place them in:

```text
C:\Users\<User>\AppData\Local\ScreenTextReader\voices\de_DE-thorsten-medium\
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

- OCR preprocessing currently converts screenshots to black/white with a fixed threshold
selected from the sample images. It also scales very small text regions before OCR.
- Piper TTS runs locally and uses the `de_DE-thorsten-medium` voice by default.

