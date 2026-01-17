@echo off
REM Cross-platform launcher script for Windows
REM Usage: run_pipeline.bat [options]

echo ==========================================
echo Research Paper Processing Pipeline
echo Platform: Windows
echo ==========================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo.
    echo Warning: .env file not found
    echo Create a .env file with your API keys:
    echo   ANTHROPIC_API_KEY=your-key-here
    echo   OPENAI_API_KEY=your-key-here
    echo.
)

REM Load environment variables from .env
if exist ".env" (
    for /f "delims== tokens=1,2" %%a in (.env) do (
        if not "%%a"=="" (
            if not "%%a:~0,1%"=="#" (
                set %%a=%%b
            )
        )
    )
)

REM Check what to run
if "%1"=="gui" (
    echo.
    echo Starting GUI application...
    python project\scripts\windows_app.py
) else if "%1"=="dashboard" (
    echo.
    echo Starting monitoring dashboard...
    streamlit run monitoring_dashboard.py
) else (
    echo.
    echo Starting command-line pipeline...
    python project\scripts\process_papers.py %*
)

pause