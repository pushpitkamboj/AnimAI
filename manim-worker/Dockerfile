FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    fonts-dejavu \
    libffi-dev \
    libgdk-pixbuf-2.0-0 \
    libcairo2-dev \
    libpango1.0-dev \
    pkg-config \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install --no-cache-dir "manim>=0.19,<0.20" "manim-voiceover[gtts]>=0.3.7"

COPY manim-worker /app/manim-worker
COPY src/observability /app/observability

EXPOSE 8080

CMD ["uvicorn", "app:app", "--app-dir", "/app/manim-worker", "--host", "0.0.0.0", "--port", "8080"]
