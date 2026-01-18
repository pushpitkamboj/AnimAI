from e2b import Template

dockerfile_content = """
# FROM e2bdev/code-interpreter:latest

RUN apt-get update -y && apt-get install -y s3fs
RUN yes | curl -LsSf https://astral.sh/uv/install.sh | sh

#base image from e2b.dev with code interpreter
FROM e2bdev/code-interpreter:latest
USER root
# Install s3fs (kept from your original request)
RUN apt-get update -y && apt-get install -y s3fs

# Install uv (kept from your original request)
RUN yes | curl -LsSf https://astral.sh/uv/install.sh | sh

# Install FFmpeg and necessary system dependencies for Manim
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
      libcairo2-dev libpango1.0-dev libfreetype6-dev libjpeg-dev libpng-dev \
      curl ca-certificates \
   && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y texlive-full && rm -rf /var/lib/apt/lists/*

RUN pip install manim

# RUN apt-get install -y gettext

# RUN apt-get install -y sox libsox-fmt-all

RUN pip install --upgrade "manim-voiceover[azure,gtts]"
"""

template = (
    Template()
    .from_dockerfile(dockerfile_content)
)