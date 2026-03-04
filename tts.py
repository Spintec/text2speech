#!/usr/bin/env python3
# Run with: .venv/bin/python tts.py  (after running install.sh)
"""
Kokoro TTS CLI - Text to speech using the local Kokoro-82M model.

Usage:
  tts "Hello, world!"
  echo "Hello" | tts
  tts -v af_heart -s 1.2 "Hello"
  tts -o output.wav "Hello"
  tts --url https://example.com/article
  tts --list-voices
"""

import sys
import argparse
import numpy as np


VOICES = {
    # American English
    "af_heart":   "American Female (Heart)",
    "af_bella":   "American Female (Bella)",
    "af_nicole":  "American Female (Nicole)",
    "af_sarah":   "American Female (Sarah)",
    "af_sky":     "American Female (Sky)",
    "am_adam":    "American Male (Adam)",
    "am_michael": "American Male (Michael)",
    # British English
    "bf_emma":    "British Female (Emma)",
    "bf_isabella":"British Female (Isabella)",
    "bm_george":  "British Male (George)",
    "bm_lewis":   "British Male (Lewis)",
}

LANG_FOR_VOICE = {
    "a": [v for v in VOICES if v.startswith("a")],
    "b": [v for v in VOICES if v.startswith("b")],
}


def get_lang_code(voice: str) -> str:
    if voice.startswith("b"):
        return "b"
    return "a"


def list_voices():
    print("Available voices:\n")
    print(f"  {'Voice ID':<16} Language")
    print(f"  {'-'*16} {'-'*30}")
    for voice_id, description in VOICES.items():
        lang = "British English" if voice_id.startswith("b") else "American English"
        print(f"  {voice_id:<16} {description}")
    print()


def fetch_article(url: str, quiet: bool) -> str:
    try:
        import trafilatura
    except ImportError:
        print("Error: trafilatura is not installed. Run: pip install trafilatura", file=sys.stderr)
        sys.exit(1)

    if not quiet:
        print(f"Fetching: {url}", file=sys.stderr)

    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        print(f"Error: could not fetch URL: {url}", file=sys.stderr)
        sys.exit(1)

    text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
    if not text:
        print("Error: no article content found at that URL.", file=sys.stderr)
        sys.exit(1)

    if not quiet:
        words = len(text.split())
        print(f"Extracted {words} words.", file=sys.stderr)

    return text


def speak(text: str, voice: str, speed: float, output: str | None, quiet: bool):
    try:
        from kokoro import KPipeline
    except ImportError:
        print("Error: kokoro is not installed. Run: pip install kokoro soundfile sounddevice", file=sys.stderr)
        sys.exit(1)

    lang_code = get_lang_code(voice)

    if not quiet:
        print(f"Voice: {voice}  Speed: {speed}  Lang: {'American' if lang_code == 'a' else 'British'} English", file=sys.stderr)

    pipeline = KPipeline(lang_code=lang_code)

    audio_chunks = []
    for _, _, audio in pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+'):
        audio_chunks.append(audio)

    if not audio_chunks:
        print("Error: no audio generated.", file=sys.stderr)
        sys.exit(1)

    combined = np.concatenate(audio_chunks)
    sample_rate = 24000

    if output:
        import soundfile as sf
        sf.write(output, combined, sample_rate)
        if not quiet:
            print(f"Saved to: {output}", file=sys.stderr)
    else:
        try:
            import sounddevice as sd
            sd.play(combined, sample_rate)
            sd.wait()
        except ImportError:
            print("Error: sounddevice not installed. Install it or use -o to save to a file.", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Text-to-speech using local Kokoro-82M model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("text", nargs="?", help="Text to speak (reads from stdin if omitted)")
    parser.add_argument("-v", "--voice", default="af_heart", metavar="VOICE",
                        help="Voice ID (default: af_heart)")
    parser.add_argument("-s", "--speed", type=float, default=1.0, metavar="SPEED",
                        help="Speech speed multiplier (default: 1.0)")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="Save audio to file instead of playing (e.g. out.wav, out.mp3)")
    parser.add_argument("--url", metavar="URL",
                        help="Fetch and read a news article from a URL")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress status messages")
    parser.add_argument("--list-voices", action="store_true",
                        help="List available voices and exit")

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        return

    if args.url:
        text = fetch_article(args.url, args.quiet)
    elif args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        parser.print_help()
        sys.exit(1)

    if not text:
        print("Error: no text provided.", file=sys.stderr)
        sys.exit(1)

    if args.voice not in VOICES:
        print(f"Warning: unknown voice '{args.voice}'. Use --list-voices to see options.", file=sys.stderr)

    speak(text, args.voice, args.speed, args.output, args.quiet)


if __name__ == "__main__":
    main()
