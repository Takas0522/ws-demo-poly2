#!/bin/bash
cd "$(dirname "$0")/src"
exec /workspaces/ws-demo-poly-integration/.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
