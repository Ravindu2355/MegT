FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    git \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Try to install megatools (provides megadl) and megacmd (optional)
# Install megatools (older but often available)
RUN apt-get update && apt-get install -y --no-install-recommends megatools || true

# Install megacmd (if apt package not available, try alternative)
# Note: megacmd packages may not be available on slim; user can customize as needed.

# Copy project files
WORKDIR /app
COPY . /app

# Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Expose health port
EXPOSE 8000

# create work dir default
ENV WORK_DIR=/tmp/mega_bot
RUN mkdir -p /tmp/mega_bot/downloads /tmp/mega_bot/thumbs

# Run bot
CMD ["python", "bot.py"]
