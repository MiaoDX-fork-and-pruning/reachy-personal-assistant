#!/bin/bash
# Stop all host services
cd "$(dirname "$0")"

echo "Stopping all services..."
supervisorctl -c supervisord.conf shutdown 2>/dev/null || pkill -f "supervisord.*supervisord.conf" 2>/dev/null || true
sleep 1
echo "Done."
