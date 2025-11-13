@echo off
REM Management CLI for Lemuel Eduspace Backend
REM This script activates the virtual environment and runs management commands

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please make sure you have created the virtual environment with: python -m venv venv
    echo Then install dependencies with: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the management command
python manage.py %*

REM Keep window open if there was an error
if %errorlevel% neq 0 (
    echo.
    echo ❌ Command failed with exit code %errorlevel%
    pause
)