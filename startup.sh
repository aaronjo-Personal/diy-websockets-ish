#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

command -v python3 >/dev/null
command -v vp >/dev/null

# Give each server its own process group so its child processes stop too.
set -m
server_pid=""
frontend_pid=""

cleanup() {
  trap '' INT TERM
  for pid in "$server_pid" "$frontend_pid"; do
    if [[ -n "$pid" ]]; then
      kill -TERM -- "-$pid" 2>/dev/null || true
    fi
  done
  wait 2>/dev/null || true
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

python3 -u websocket.py &
server_pid=$!

(cd frontend && exec vp dev --strictPort) &
frontend_pid=$!

# If either server exits, stop the other one as well.
while kill -0 "$server_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do
  sleep 1
done

if ! kill -0 "$server_pid" 2>/dev/null; then
  wait "$server_pid"
else
  wait "$frontend_pid"
fi
