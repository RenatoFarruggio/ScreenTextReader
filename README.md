# ScreenTextReader

ScreenTextReader reads visible game dialogue aloud on Windows. It detects configured game
processes, enables a global hotkey while a configured game is running, captures the whole
screen or a saved region, runs Windows OCR, and speaks the recognized text with local Piper TTS.

Many games still show dialogue as on-screen text without full voice acting. This helps when
you would rather hear the lines spoken than read them yourself.

## Disclaimer

This project is in beta and early development, not ready for general use. It works
technically, but it is slow. You must start it via Python each time (`uv run main.py`), and
you need to understand the setup steps below to get it working.

The project is currently set up for German dialogue: Windows OCR `de-DE` and the Piper voice
`de_DE-thorsten-medium`. English or other languages are not covered by the default setup, but switching to other languages is possible without much effort.

The default Piper voice sounds very "AI-like" — do not expect world-class voice acting with
this setup. On the positive side, Windows OCR and Piper TTS both run locally on CPU, so the
stack should work on lower-end machines without a dedicated GPU.

## Setup

This project uses `uv` for the Python environment and dependency management.

Required on the machine:

- Windows 10/11.
- **Hardware:** 4 GB RAM minimum (8 GB recommended when a game runs at the same time). A
  modern dual-core x64 CPU is enough for OCR and TTS on CPU; no GPU is required. Allow ~500 MB
  disk space for Python dependencies and the Piper voice model.
- Python 3.12, managed by `uv` for this project.
- `uv` installed.
- Windows OCR language `de-DE` installed.
- Audio output device available for `sounddevice`.

If `uv` is missing, install it first:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

From the project directory (`cd ScreenTextReader`):

```powershell
uv sync
uv run python -c "from src.tts import ensure_voice; ensure_voice('de_DE-thorsten-medium')"
```

The voice download step needs internet access once. It downloads the German Piper voice to:

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

## Start

```powershell
uv run main.py
```

Keep the ScreenTextReader window open while you play. It is a normal Python GUI process, not a
background service or tray app.

The shipped `config.json` contains placeholder game profiles such as `example.exe` and
`game.exe`. Replace them in the GUI before expecting anything to work for a real game:

1. Create or select a profile and set **Process name** to the game's executable from Task
   Manager, for example `eldenring.exe`.
2. Choose **Use full screen**, or to capture a dialogue box area: click **Select region**,
   drag to select the area, then press Enter to confirm.
3. Click **Save** to save the config.
4. Start the game and wait until the status shows that profile as active.
5. Press the configured hotkey (default `F9`) to capture the screen region, run OCR, and
   speak the recognized text.

It worked for me when started without Administrator level access, but if the global hotkey
does not trigger while a game is focused, try starting the terminal or app as Administrator.
Some games block non-admin global keyboard hooks.

## Notes

- OCR preprocessing currently converts screenshots to black/white with a fixed threshold
  selected from the sample images. It also scales very small text regions before OCR.
- Piper TTS runs locally and uses the `de_DE-thorsten-medium` voice by default.
- Licensed under the GNU General Public License v3.0; see `LICENSE`.

