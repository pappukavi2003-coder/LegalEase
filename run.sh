#!/usr/bin/env bash
# Starts the FastAPI backend and the Streamlit frontend together.
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
[ -f .env ] || { cp .env.example .env; echo "Created .env - add your GEMINI_API_KEY, then run this script again."; exit 1; }

uvicorn legalEaseAPI.main:app --reload &
BACKEND_PID=$!
trap "kill $BACKEND_PID" EXIT
sleep 2
streamlit run frontend/app.py
