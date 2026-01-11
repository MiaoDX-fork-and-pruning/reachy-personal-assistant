# Reachy Mini Robot with NeMo Agent Toolkit Tutorial

This tutorial showcases a real-time AI agent built with the **NVIDIA NeMo Agent Toolkit**, powered by **Qwen models via HuggingFace Inference API**, controlling a **Reachy Mini Robot**. The agent uses an intelligent LLM router to dynamically route between:
- **Qwen2.5-7B-Instruct** for text-based interactions
- **Qwen2.5-VL-7B-Instruct** (Vision Language Model) for visual understanding
- **Qwen2.5-72B-Instruct** REACT agent for tool-based actions

![Reachy Mini Robot Demo](ces_tutorial.png)

## Architecture

The system consists of three main components running in parallel:

1. **Reachy Mini Daemon** - Controls the robot hardware (or simulation)
2. **Bot Service** - Processes vision and speech, coordinates robot actions
3. **NeMo Agent Service** - Handles AI agent logic with intelligent routing between models

![System Architecture](ces_tutorial_arch.png)

## Quick Start with Docker (Recommended)

The easiest way to run the system is with Docker:

```bash
# 1. Create .env file with your API keys
cp .env.template .env
# Edit .env with your HF_API_KEY and ELEVENLABS_API_KEY

# 2. Start all services
docker compose up --build

# 3. Open in browser:
#    - Bot UI: http://localhost:7860/client/
#    - Robot Viewer: http://localhost:8080
#    - Robot Dashboard: http://localhost:8000
```

To stop: `docker compose down`

## Prerequisites

- Docker (for Docker setup) OR Python 3.12+ with [uv](https://github.com/astral-sh/uv) (for local setup)
- HuggingFace API Key (for Qwen models via Inference Providers)
- ElevenLabs API Key (for text-to-speech)

## Setup Instructions

### Option A: Docker Setup (Recommended)

1. **Create Environment File**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

2. **Run with Docker Compose**
   ```bash
   docker compose up --build
   ```

3. **Access the Services**
   - **Bot/Pipecat UI**: http://localhost:7860/client/
   - **Robot Video Viewer**: http://localhost:8080
   - **Robot Dashboard**: http://localhost:8000
   - **NAT Service**: http://localhost:8001

### Option B: Local Setup (Manual)

#### 1. Create Environment File

Create a `.env` file in the main directory with your API keys:

```bash
# Get your HuggingFace token from: https://huggingface.co/settings/tokens
HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxx
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

#### 2. Setup Bot Service

```bash
cd bot
uv venv
uv sync
```

#### 3. Setup NeMo Agent Service

```bash
cd nat
uv venv
uv sync
```

#### 4. Running Locally (3 terminals)

**Terminal 1: Start Reachy Mini Daemon**
```bash
cd bot
# macOS:
uv run mjpython -m reachy_mini.daemon.app.main --sim --no-localhost-only
# Linux:
uv run -m reachy_mini.daemon.app.main --sim --no-localhost-only
```

**Terminal 2: Start NeMo Agent Service**
```bash
cd nat
uv run --env-file ../.env nat serve --config_file src/ces_tutorial/config.yml --port 8001
```

**Terminal 3: Start Bot Service**
```bash
cd bot
uv run --env-file ../.env python main.py
```

## How It Works

1. **Vision & Audio Input**: The bot captures visual information and listens for speech
2. **Agent Processing**: The NeMo Agent router intelligently selects the appropriate Qwen model:
   - Text queries → Qwen2.5-7B-Instruct
   - Visual queries → Qwen2.5-VL-7B-Instruct
   - Action requests → Qwen2.5-72B-Instruct REACT agent with tool calling
3. **Robot Actions**: Based on the agent's response, the bot executes movements, expressions, or speaks

## Demo

Check out `ces_tutorial.mp4` to see the system in action!

## Project Structure

```
reachy-personal-assistant/
├── bot/                    # Robot control and vision/speech processing
│   ├── main.py            # Main bot orchestration
│   ├── nat_vision_llm.py  # Vision and LLM integration
│   └── services/          # Robot services (moves, speech, etc.)
├── nat/                    # NeMo Agent Toolkit configuration
│   └── src/ces_tutorial/
│       ├── config.yml     # Agent configuration
│       └── functions/     # Router and agent implementations
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── viewer_server.py       # Robot video streaming server
└── .env                   # API keys (create from .env.template)
```

## Troubleshooting

- **Port conflicts**: Ensure ports 7860, 8000, 8001, 8080 are available
- **API key errors**: Verify your `.env` file is properly formatted and contains valid keys
- **Robot connection issues**: Check that the Reachy daemon started successfully
- **Docker build issues**: Try `docker compose down && docker compose up --build`

## Resources

- [NVIDIA NeMo Agent Toolkit](https://github.com/NVIDIA/NeMo-Agent-Toolkit)
- [Reachy Mini Robot](https://www.pollen-robotics.com/)
- [Qwen2.5 Models](https://huggingface.co/collections/Qwen/qwen25)
- [HuggingFace Inference Providers](https://huggingface.co/docs/inference-providers/en/index)
