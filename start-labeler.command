#!/bin/bash
# Double-click to run Weekday Labeler on this Mac.
# Needs nothing installed — macOS ships the Python this uses.
cd "$(dirname "$0")"
PORT=8080
while lsof -i :$PORT >/dev/null 2>&1; do PORT=$((PORT+1)); done
echo "Weekday Labeler → http://localhost:$PORT"
echo "Leave this window open while you work. Close it to stop."
( sleep 1; open "http://localhost:$PORT" ) &
exec python3 serve.py "$PORT"
