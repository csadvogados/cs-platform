@echo off
cd backend
if not exist .env copy .env.example .env
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install -r requirements.txt
start http://localhost:8000/docs
uvicorn app.main:app --reload
pause
