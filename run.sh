#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; .venv/bin/pip install -r backend/requirements.txt; fi
if [ ! -d frontend/node_modules ]; then (cd frontend && npm install); fi
(cd frontend && npm run build)
cd backend && ../.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
