# Kokoro TTS

Local text-to-speech using the [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) model. Available as both a CLI tool and a web app.

## Installation

Requires Python 3.10-3.12, espeak-ng, and portaudio.

Run the install script to set everything up automatically:

```bash
./install.sh
```

This will:
1. Install system dependencies (espeak-ng, portaudio) via apt or brew
2. Install [uv](https://github.com/astral-sh/uv) if not present
3. Create a Python 3.12 virtual environment
4. Install all Python dependencies

## Running

### Web App

```bash
.venv/bin/python app.py
```

Open http://localhost:5000 in your browser.

### CLI

```bash
.venv/bin/python tts.py "Hello, world!"
```

Pipe text from stdin:

```bash
echo "Hello, world!" | .venv/bin/python tts.py
```

Read a news article aloud:

```bash
.venv/bin/python tts.py --url https://example.com/article
```

Save to a file instead of playing:

```bash
.venv/bin/python tts.py -o output.wav "Hello, world!"
```

Change voice and speed:

```bash
.venv/bin/python tts.py -v bm_george -s 1.3 "Hello, world!"
```

List available voices:

```bash
.venv/bin/python tts.py --list-voices
```

## Features

### Voices

11 built-in voices across two accents:

- **American English** -- af_heart, af_bella, af_nicole, af_sarah, af_sky, am_adam, am_michael
- **British English** -- bf_emma, bf_isabella, bm_george, bm_lewis

### Speed Control

Adjustable speech speed from 0.5x to 2.0x (default 1.0x).

### Article Extraction

Paste a URL and the app extracts the article text automatically using [trafilatura](https://github.com/adbar/trafilatura), stripping ads, navigation, and other clutter.

### Listening Queue (Web App)

The web app includes a queue panel for building a playlist of articles:

- **Add URLs** -- paste article links to queue them; each entry is fetched in the background and displayed by its article title
- **Sequential playback** -- plays through the queue in order, automatically advancing when each article finishes
- **Shuffle** -- randomizes the play order
- **Repeat** -- loops the queue when it reaches the end
- **Drag and drop** -- reorder items by dragging
- **Click to jump** -- click any item to start playing from that point

### Audio Output

- **Web app** -- in-browser playback with download option
- **CLI** -- direct playback via sounddevice, or save to WAV/MP3 with `-o`
