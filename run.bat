@echo off
title Nexus DP1
cd /d %~dp0
if not exist .venv py -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --host 0.0.0.0 --port 8010
pause
