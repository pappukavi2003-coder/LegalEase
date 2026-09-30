@echo off
cd /d "%~dp0"
if not exist venv python -m venv venv
call venv\Scripts\activate
pip install -q -r requirements.txt
if not exist .env (
  copy .env.example .env >nul
  echo Created .env - open it, add your GEMINI_API_KEY, then run this script again.
  pause
  exit /b 1
)
start "LegalEase backend" cmd /k uvicorn legalEaseAPI.main:app --reload
timeout /t 3 >nul
streamlit run frontend/app.py
