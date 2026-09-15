@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m fps_ascii %*
) else (
    python -m fps_ascii %*
)
if errorlevel 1 pause

