#!/usr/bin/env python3
"""Kokoro TTS Web App - Browser-based text-to-speech using local Kokoro-82M model."""

import io
import json
import os

import numpy as np
import requests as http_requests
import soundfile as sf
from flask import Flask, render_template, request, jsonify, send_file

from tts import VOICES, get_lang_code

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'api_keys.json')


def load_api_keys():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


CATEGORY_QUERIES = {
    'geopolitics': 'geopolitics OR diplomacy OR foreign policy OR international relations',
    'tech': 'technology OR software OR AI OR startup',
    'hacking': 'hacking OR cybersecurity OR infosec OR data breach',
}

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


def search_newsapi(query, user_query):
    config = load_api_keys()
    newsapi = config.get('newsapi', {})
    api_key = newsapi.get('api_key', '')
    if not api_key:
        return []
    base_url = newsapi.get('base_url', 'https://newsapi.org/v2')
    full_query = f'{user_query} {query}' if user_query else query
    try:
        resp = http_requests.get(f'{base_url}/everything', params={
            'q': full_query,
            'sortBy': 'publishedAt',
            'pageSize': 10,
            'apiKey': api_key,
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [
            {'title': a['title'], 'url': a['url'], 'source': f"NewsAPI - {a['source']['name']}"}
            for a in data.get('articles', []) if a.get('title') and a.get('url')
        ]
    except Exception:
        return []


def search_hackernews(query, user_query):
    full_query = f'{user_query} {query}' if user_query else query
    try:
        resp = http_requests.get('https://hn.algolia.com/api/v1/search', params={
            'query': full_query,
            'tags': 'story',
            'hitsPerPage': 10,
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [
            {'title': h['title'], 'url': h.get('url', f"https://news.ycombinator.com/item?id={h['objectID']}"), 'source': 'HackerNews'}
            for h in data.get('hits', []) if h.get('title')
        ]
    except Exception:
        return []


@app.route('/search-articles/<category>', methods=['GET'])
def search_articles(category):
    if category not in CATEGORY_QUERIES:
        return jsonify({"error": f"Unknown category: {category}"}), 400

    user_query = request.args.get('q', '').strip()
    base_query = CATEGORY_QUERIES[category]
    results = []

    results.extend(search_newsapi(base_query, user_query))
    results.extend(search_hackernews(base_query, user_query))

    return jsonify({"results": results})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
