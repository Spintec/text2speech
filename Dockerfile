FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends espeak-ng libportaudio2 libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download spaCy language model and Kokoro-82M weights from HuggingFace
RUN python -m spacy download en_core_web_sm && \
    python -c "from kokoro import KPipeline; KPipeline(lang_code='a')"

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
