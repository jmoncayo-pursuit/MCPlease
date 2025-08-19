@echo off
REM MCPlease Universal Installer for Windows
REM Auto-detects system and provides easiest installation path

setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    MCPlease Universal Installer              ║
echo ║              AI Coding Assistant for Windows                 ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [INFO] Starting MCPlease installation for Windows...
echo.

REM Check if Python is installed
echo [STEP] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
    echo [INFO] Please install Python 3.9+ from https://python.org
    echo [INFO] Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

python --version
echo [SUCCESS] Python found
echo.

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    echo [ERROR] Python 3.9+ required, found %PYTHON_VERSION%
    pause
    exit /b 1
)

if %MAJOR% EQU 3 (
    if %MINOR% LSS 9 (
        echo [ERROR] Python 3.9+ required, found %PYTHON_VERSION%
        pause
        exit /b 1
    )
)

echo [SUCCESS] Python version %PYTHON_VERSION% is compatible
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo [STEP] Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
) else (
    echo [SUCCESS] Virtual environment found
)

REM Activate virtual environment
echo [STEP] Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo [STEP] Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
if exist "requirements.txt" (
    echo [STEP] Installing Python dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [SUCCESS] Python dependencies installed
) else (
    echo [WARNING] requirements.txt not found
)

echo.

REM Check for OSS-20B model
if not exist "models\gpt-oss-20b" (
    echo [WARNING] OSS-20B model not found
    set /p DOWNLOAD_MODEL="Download OSS-20B model now? (13GB, y/N): "
    if /i "!DOWNLOAD_MODEL!"=="y" (
        echo [INFO] Downloading OSS-20B model (this may take 10-30 minutes)...
        python download_model.py
    ) else (
        echo [WARNING] Model download skipped. AI features will use fallback responses.
    )
) else (
    echo [SUCCESS] OSS-20B model found
)

echo.

REM Setup IDE configurations
if exist "scripts\setup_ide.py" (
    echo [STEP] Setting up IDE configurations...
    python scripts\setup_ide.py
    echo [SUCCESS] IDE configurations created
) else (
    echo [WARNING] IDE setup script not found
)

echo.

REM Test installation
echo [STEP] Testing installation...
python -c "import mcp" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] MCP library import failed
    pause
    exit /b 1
)
echo [SUCCESS] MCP library import successful

REM Test server startup
python mcplease_mcp_server.py --help >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] MCP server startup test failed
    pause
    exit /b 1
)
echo [SUCCESS] MCP server startup test successful

echo.
echo [SUCCESS] Installation complete!
echo.
echo 🎯 Next Steps:
echo.
echo 1. Start MCPlease:
echo    • Local: start.bat
echo    • Docker: start-docker.sh (if WSL available)
echo.
echo 2. Use in your IDE:
echo    • Cursor/VS Code: Look for MCPlease in Workspace Tools → MCP
echo    • Continue.dev: Use ./start-docker.sh --http (if WSL available)
echo.
echo 3. Test everything:
echo    • python scripts\test_transports.py
echo.
echo 4. Get help:
echo    • README.md for detailed instructions
echo    • GitHub Issues for support
echo.
pause
