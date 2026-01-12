#!/bin/bash
# Run all services on host system using supervisord (same as Docker)
# Usage: ./run_host.sh
#
# Install supervisor first: brew install supervisor

set -e
cd "$(dirname "$0")"

# Stop any existing processes
echo "Stopping existing processes..."
supervisorctl -c supervisord.conf shutdown 2>/dev/null || true
pkill -f "supervisord.*supervisord.conf" 2>/dev/null || true
# Kill by ports: zenoh(7447), bot(7860), dashboard(8000), nat(8001), viewer(8080), ws(8765)
lsof -ti:7447,7860,8000,8001,8080,8765 | xargs kill -9 2>/dev/null || true
sleep 2

# Create log directory
mkdir -p logs

echo "=================================================="
echo "  Starting Reachy Personal Assistant (Host Mode)"
echo "=================================================="
echo ""
echo "Services will be available at:"
echo "  Bot UI:          http://localhost:7860/client/"
echo "  Robot Viewer:    http://localhost:8080"
echo "  Robot Dashboard: http://localhost:8000"
echo "  NAT Service:     http://localhost:8001"
echo ""
echo "Logs are in ./logs/ directory"
echo "Press Ctrl+C to stop all services"
echo "=================================================="
echo ""

# Run supervisord with our config
exec supervisord -c supervisord.conf
