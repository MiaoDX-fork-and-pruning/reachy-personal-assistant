# Reachy Personal Assistant
#
# Usage:
#   docker compose up --build
#   docker compose down

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for mujoco and general use
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgl1 \
    libglx0 \
    libegl1 \
    libgbm1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libglfw3 \
    libglfw3-dev \
    libportaudio2 \
    portaudio19-dev \
    xvfb \
    xauth \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy bot project and install dependencies
COPY bot/pyproject.toml bot/uv.lock /app/bot/
WORKDIR /app/bot
RUN uv sync --frozen

# Copy bot source files
COPY bot/*.py /app/bot/
COPY bot/services/ /app/bot/services/

# Copy viewer server
COPY viewer_server.py /app/

# Install viewer server dependencies
RUN pip install aiohttp websockets

# Copy nat project and source files, then install dependencies
COPY nat/pyproject.toml nat/uv.lock /app/nat/
COPY nat/src/ /app/nat/src/
WORKDIR /app/nat
RUN uv sync --frozen

WORKDIR /app

# Create supervisord config
RUN mkdir -p /var/log/supervisor
COPY <<EOF /etc/supervisor/conf.d/services.conf
[supervisord]
nodaemon=true
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid

[program:viewer]
command=python /app/viewer_server.py
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/viewer.log
stderr_logfile=/var/log/supervisor/viewer-error.log
priority=1

[program:reachy-daemon]
command=/bin/bash -c "sleep 3 && cd /app/bot && xvfb-run -a uv run python -m reachy_mini.daemon.app.main --sim --no-localhost-only --websocket-uri ws://localhost:8765"
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/reachy-daemon.log
stderr_logfile=/var/log/supervisor/reachy-daemon-error.log
environment=MUJOCO_GL="egl"
priority=2

[program:nat]
command=/bin/bash -c "cd /app/nat && uv run nat serve --config_file src/ces_tutorial/config.yml --port 8001 --host 0.0.0.0"
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/nat.log
stderr_logfile=/var/log/supervisor/nat-error.log
priority=3
startsecs=5

[program:bot]
command=/bin/bash -c "sleep 10 && cd /app/bot && uv run python main.py --host 0.0.0.0"
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/bot.log
stderr_logfile=/var/log/supervisor/bot-error.log
priority=4
startsecs=15
EOF

# Expose ports
EXPOSE 7860 8000 8001 8080 8765

# Run supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
