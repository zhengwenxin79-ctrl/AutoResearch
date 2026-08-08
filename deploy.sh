#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/AutoResearch}
BRANCH=${BRANCH:-main}
HOST=${HOST:-127.0.0.1}
AUTORESEARCH_PORT=${AUTORESEARCH_PORT:-8766}
AUTORESEARCH_OUTPUT_DIR=${AUTORESEARCH_OUTPUT_DIR:-outputs}
AUTORESEARCH_DEFAULT_RUN=${AUTORESEARCH_DEFAULT_RUN:-gui-agent-benchmark-real-world-workflow}

cd "$APP_DIR"

git fetch origin "$BRANCH" -q
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" != "$REMOTE" ]; then
  git pull origin "$BRANCH" -q
fi

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install -e . >/tmp/autoresearch_pip_install.log

pkill -f "python.*autoresearch_server.py" || true
sleep 1

nohup env \
  HOST="$HOST" \
  AUTORESEARCH_PORT="$AUTORESEARCH_PORT" \
  AUTORESEARCH_OUTPUT_DIR="$AUTORESEARCH_OUTPUT_DIR" \
  AUTORESEARCH_DEFAULT_RUN="$AUTORESEARCH_DEFAULT_RUN" \
  .venv/bin/python autoresearch_server.py > autoresearch_server.log 2>&1 &

echo "AutoResearch deployed at $(date)"
echo "Local service: http://$HOST:$AUTORESEARCH_PORT"
echo "Default run: $AUTORESEARCH_DEFAULT_RUN"
