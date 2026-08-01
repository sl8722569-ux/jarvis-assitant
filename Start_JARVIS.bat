@echo off
title JARVIS Assistant
cd /d "%~dp0"
set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if not exist "%PY%" set PY=python
echo Starting JARVIS...
"%PY%" "%~dp0jarvis.py"
if errorlevel 1 pause
