@echo off
title J.A.R.V.I.S [EARLY ACCESS] — Windows installer
cd /d "%~dp0\..\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-JARVIS.ps1"
if errorlevel 1 pause
