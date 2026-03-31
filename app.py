#!/usr/bin/env python3
"""Kokoro TTS Web App - Browser-based text-to-speech using local Kokoro-82M model."""

import io

import numpy as np
import soundfile as sf
from flask import Flask, render_template, request, jsonify, send_file

from tts import VOICES, get_lang_code

app = Flask(__name__)

_pipelines = {}


def get_pipeline(lang_code):
    if lang_code not in _pipelines:
        from kokoro import KPipeline
        _pipelines[lang_code] = KPipeline(lang_code=lang_code)
    return _pipelines[lang_code]


def generate_audio(text, voice, speed):
    lang_code = get_lang_code(voice)
    pipeline = get_pipeline(lang_code)

    audio_chunks = []
    for _, _, audio in pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+'):
        audio_chunks.append(audio)

    if not audio_chunks:
        return None

    combined = np.concatenate(audio_chunks)
    buf = io.BytesIO()
    sf.write(buf, combined, 24000, format='WAV')
    buf.seek(0)
    return buf


@app.route('/')
def index():
    return render_template('index.html', voices=VOICES)


@app.route('/synthesize', methods=['POST'])
def synthesize():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    text = data.get('text', '').strip()
    voice = data.get('voice', 'af_heart')
    speed = float(data.get('speed', 1.0))

    if not text:
        return jsonify({"error": "No text provided"}), 400

    if voice not in VOICES:
        return jsonify({"error": f"Unknown voice: {voice}"}), 400

    buf = generate_audio(text, voice, speed)
    if buf is None:
        return jsonify({"error": "No audio generated"}), 500

    return send_file(buf, mimetype='audio/wav', download_name='speech.wav')


@app.route('/fetch-url', methods=['POST'])
def fetch_url():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    url = data.get('url', '').strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return jsonify({"error": "Could not fetch URL"}), 400

        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not text:
            return jsonify({"error": "No article content found at that URL"}), 400

        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if metadata and metadata.title else url
    except ImportError:
        return jsonify({"error": "trafilatura is not installed"}), 500

    return jsonify({"text": text, "title": title})


RSS_FEEDS = {
    "hackernews": {
        "name": "Hacker News",
        "search_url": "https://hnrss.org/newest?q={query}&count={count}",
    },
}


@app.route('/search-rss', methods=['POST'])
def search_rss():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    query = data.get('query', '').strip()
    if not query:
        return jsonify({"error": "No search query provided"}), 400

    feed_id = data.get('feed', 'hackernews')
    count = min(int(data.get('count', 10)), 30)

    feed_config = RSS_FEEDS.get(feed_id)
    if not feed_config:
        return jsonify({"error": f"Unknown feed: {feed_id}"}), 400

    try:
        import feedparser
        url = feed_config["search_url"].format(query=query, count=count)
        feed = feedparser.parse(url)

        results = []
        for entry in feed.entries[:count]:
            results.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
            })

        return jsonify({"results": results, "feed_name": feed_config["name"]})
    except ImportError:
        return jsonify({"error": "feedparser is not installed"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to fetch RSS feed: {str(e)}"}), 500


@app.route('/rss-feeds', methods=['GET'])
def list_rss_feeds():
    return jsonify({fid: cfg["name"] for fid, cfg in RSS_FEEDS.items()})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
