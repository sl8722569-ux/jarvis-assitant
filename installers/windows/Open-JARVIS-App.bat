@echo off
REM Opens J.A.R.V.I.S as an app window (Edge/Chrome app mode)
start "" msedge --app="https://sl8722569-ux.github.io/jarvis-assitant/webapp/"
if errorlevel 1 start "" chrome --app="https://sl8722569-ux.github.io/jarvis-assitant/webapp/"
