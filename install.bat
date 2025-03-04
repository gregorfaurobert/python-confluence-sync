@echo off
echo === Confluence Sync Installation ===
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is required but not installed.
    echo Please install Python 3.8 or higher and try again.
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
for /f "tokens=1,2 delims=." %%A in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%A
    set PYTHON_MINOR=%%B
)

if %PYTHON_MAJOR% LSS 3 (
    echo Error: Python 3.8 or higher is required.
    echo Current version: %PYTHON_VERSION%
    exit /b 1
)

if %PYTHON_MAJOR% EQU 3 (
    if %PYTHON_MINOR% LSS 8 (
        echo Error: Python 3.8 or higher is required.
        echo Current version: %PYTHON_VERSION%
        exit /b 1
    )
)

echo Python version %PYTHON_VERSION% detected.
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to create virtual environment.
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment.
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install dependencies.
    exit /b 1
)

REM Install package in development mode
echo Installing Confluence Sync...
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install package.
    exit /b 1
)

echo.
echo === Installation Complete ===
echo.
echo To use Confluence Sync, activate the virtual environment:
echo   venv\Scripts\activate
echo.
echo Then run the CLI:
echo   confluence-sync --help
echo.
echo Or:
echo   python -m confluence_sync --help
echo.
echo To set up your Confluence credentials:
echo   confluence-sync config credentials
echo.
echo To configure a Confluence space:
echo   confluence-sync config spaces --add
echo.

pause 