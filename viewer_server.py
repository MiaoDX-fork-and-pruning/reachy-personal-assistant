#!/usr/bin/env python3
"""
WebSocket Video Receiver and HTTP Server for Reachy Robot Visualization.

Receives JPEG frames from reachy daemon via WebSocket and serves them via HTTP.

Usage:
    python viewer_server.py

Then open http://localhost:8765 in your browser.
"""

import asyncio
import io
import logging
from datetime import datetime

from aiohttp import web
import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global frame storage
latest_frame: bytes = b""
frame_count = 0
last_frame_time = None


async def websocket_handler(websocket):
    """Handle incoming WebSocket connections from reachy daemon."""
    global latest_frame, frame_count, last_frame_time

    logger.info(f"Reachy daemon connected from {websocket.remote_address}")

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                latest_frame = message
                frame_count += 1
                last_frame_time = datetime.now()

                if frame_count % 100 == 0:
                    logger.info(f"Received {frame_count} frames")
    except websockets.exceptions.ConnectionClosed:
        logger.info("Reachy daemon disconnected")


async def index_handler(request):
    """Serve the HTML viewer page."""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Reachy Robot Viewer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a2e;
            color: white;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 { color: #e94560; }
        #video {
            max-width: 100%;
            border: 2px solid #e94560;
            border-radius: 8px;
        }
        #status {
            margin-top: 10px;
            padding: 10px;
            background: #16213e;
            border-radius: 4px;
        }
        .connected { color: #4ecca3; }
        .disconnected { color: #e94560; }
    </style>
</head>
<body>
    <h1>Reachy Robot Viewer</h1>
    <img id="video" src="/frame" alt="Waiting for video stream...">
    <div id="status" class="disconnected">Waiting for connection...</div>

    <script>
        const img = document.getElementById('video');
        const status = document.getElementById('status');
        let frameCount = 0;
        let lastUpdate = Date.now();

        function updateFrame() {
            // Add timestamp to prevent caching
            img.src = '/frame?' + Date.now();
        }

        img.onload = function() {
            frameCount++;
            const now = Date.now();
            const fps = Math.round(1000 / (now - lastUpdate));
            lastUpdate = now;
            status.textContent = `Connected - Frame ${frameCount} (${fps} fps)`;
            status.className = 'connected';
            setTimeout(updateFrame, 40); // ~25 fps
        };

        img.onerror = function() {
            status.textContent = 'Waiting for video stream...';
            status.className = 'disconnected';
            setTimeout(updateFrame, 1000);
        };

        updateFrame();
    </script>
</body>
</html>
"""
    return web.Response(text=html, content_type='text/html')


async def frame_handler(request):
    """Serve the latest frame as JPEG."""
    global latest_frame

    if latest_frame:
        return web.Response(body=latest_frame, content_type='image/jpeg')
    else:
        # Return a placeholder image
        return web.Response(status=204)


async def status_handler(request):
    """Return status information."""
    global frame_count, last_frame_time

    return web.json_response({
        'frames_received': frame_count,
        'last_frame_time': last_frame_time.isoformat() if last_frame_time else None,
        'connected': latest_frame != b""
    })


async def start_websocket_server():
    """Start the WebSocket server to receive frames from reachy daemon."""
    server = await websockets.serve(websocket_handler, "0.0.0.0", 8765)
    logger.info("WebSocket server listening on ws://0.0.0.0:8765")
    return server


async def start_http_server():
    """Start the HTTP server for the viewer."""
    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_get('/frame', frame_handler)
    app.router.add_get('/status', status_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("HTTP viewer available at http://localhost:8080")
    return runner


async def main():
    """Main entry point."""
    logger.info("Starting Reachy Video Viewer Server...")

    # Start both servers
    ws_server = await start_websocket_server()
    http_runner = await start_http_server()

    logger.info("")
    logger.info("=" * 50)
    logger.info("Reachy Video Viewer Ready!")
    logger.info("  WebSocket: ws://localhost:8765 (reachy daemon connects here)")
    logger.info("  Viewer:    http://localhost:8080 (open in browser)")
    logger.info("=" * 50)
    logger.info("")

    # Keep running
    try:
        await asyncio.Future()  # Run forever
    except asyncio.CancelledError:
        pass
    finally:
        ws_server.close()
        await ws_server.wait_closed()
        await http_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
