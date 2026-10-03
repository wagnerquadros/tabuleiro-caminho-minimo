@echo off
setlocal
cd /d "%~dp0"
where pythonw >nul 2>nul
if not errorlevel 1 (
    start "" pythonw -B "%~dp0tabuleiro.py"
    exit /b
)
where pyw >nul 2>nul
if not errorlevel 1 (
    start "" pyw -3 "%~dp0tabuleiro.py"
    exit /b
)
python -B tabuleiro.py
if errorlevel 1 pause
