# Reachy Personal Assistant
#
# Usage:
#   docker compose up --build
#   docker compose down

FROM python:3.13-slim

WORKDIR /app

# Layer 1: System dependencies (rarely changes)
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
    libosmesa6 \
    xvfb \
    xauth \
    supervisor \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Layer 2: Install uv and pip packages (rarely changes)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN pip install aiohttp websockets

# Layer 3: Bot dependencies (changes when pyproject.toml/uv.lock change)
COPY bot/pyproject.toml bot/uv.lock /app/bot/
WORKDIR /app/bot
RUN uv sync --frozen

# Layer 4: NAT dependencies (changes when pyproject.toml/uv.lock change)
# Note: NAT requires src/ for editable install
COPY nat/pyproject.toml nat/uv.lock /app/nat/
COPY nat/src/ /app/nat/src/
WORKDIR /app/nat
RUN uv sync --frozen

WORKDIR /app

# Layer 5: Runtime setup (rarely changes)
RUN mkdir -p /tmp/runtime-root && chmod 700 /tmp/runtime-root
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
command=/bin/bash -c "sleep 3 && cd /app/bot && uv run python -m reachy_mini.daemon.app.main --sim --no-localhost-only --headless --no-wake-up-on-start"
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/reachy-daemon.log
stderr_logfile=/var/log/supervisor/reachy-daemon-error.log
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

[program:startup-message]
command=/bin/bash -c "sleep 20 && echo '' && echo '==================================================' && echo '  Reachy Personal Assistant Ready!' && echo '==================================================' && echo '  Bot UI:         http://localhost:7860/client/' && echo '  Robot Viewer:   http://localhost:8080' && echo '  Robot Dashboard: http://localhost:8000' && echo '  NAT Service:    http://localhost:8001' && echo '==================================================' && echo ''"
autostart=true
autorestart=false
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
priority=5
EOF

# Layer 5b: Additional GL packages for arm64 osmesa (new layer to avoid full rebuild)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libosmesa6-dev \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

# Layer 6: Source code (changes frequently - LAST)
COPY bot/*.py /app/bot/
COPY bot/services/ /app/bot/services/
COPY viewer_server.py /app/

# Expose ports
EXPOSE 7860 8000 8001 8080 8765

# Run supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
