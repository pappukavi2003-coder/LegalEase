"""Shared configuration for both the FastAPI backend and the Streamlit frontend."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-3.8-flash"
GEMINI_FALLBACK_MODELS = [
    m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.5-flash-lite,gemini-3.5-flash,gemini-2.5-flash").split(",")
    if m.strip()
]

# The Streamlit app is a separate process from FastAPI, so it reaches the
# backend over HTTP rather than importing it directly.
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

LOGO_PATH = str(BASE_DIR / "Image" / "Logo.png")
