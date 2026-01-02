FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV MANIM_DISABLE_CACHING=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpango1.0-dev \
    libfreetype6 \
    libfreetype6-dev \
    libjpeg62-turbo \
    libjpeg-dev \
    libpng16-16 \
    libpng-dev \
    pkg-config \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    manim \
    fastapi \
    uvicorn \
    boto3

WORKDIR /app
COPY app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
