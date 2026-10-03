@echo off
cd /d "%~dp0"
if exist "C:\Python311\pythonw.exe" (
    start "" "C:\Python311\pythonw.exe" -B "%~dp0tabuleiro.py"
    exit /b
)
where pyw >nul 2>nul
if not errorlevel 1 (
    start "" pyw -3 "%~dp0tabuleiro.py"
    exit /b
)
python tabuleiro.py
if errorlevel 1 pause
