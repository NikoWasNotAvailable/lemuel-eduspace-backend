@echo off
echo ================================
echo  Lemuel EduSpace Backend Server
echo ================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment!
        echo Make sure Python is installed and in your PATH.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
    echo.
)

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found!
    echo Please copy .env.example to .env and configure your settings.
    echo.
    if exist ".env.example" (
        echo Copying .env.example to .env...
        copy .env.example .env
        echo Please edit .env file with your database credentials and settings.
        echo.
    )
)

REM Start the server
echo Starting FastAPI server...
echo Server will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000

echo.
echo Server stopped.
pause