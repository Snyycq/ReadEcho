@echo off
echo ========================================
echo ReadEcho Pro EXE Auto Update Tool
echo ========================================
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查虚拟环境是否存在
if not exist "venv_ai\Scripts\activate.bat" (
    echo ERROR: venv_ai virtual environment not found!
    echo Please make sure venv_ai exists in the current directory.
    pause
    exit /b 1
)

:: 检查主程序文件是否存在
if not exist "main.py" (
    echo ERROR: main.py not found!
    echo Please make sure main.py exists in the current directory.
    pause
    exit /b 1
)

echo [1/4] Cleaning old build files...
if exist "build" (
    rmdir /s /q "build"
    echo   - Removed build directory
)
if exist "dist" (
    rmdir /s /q "dist"
    echo   - Removed dist directory
)
if exist "ReadEcho_Pro.spec" (
    del "ReadEcho_Pro.spec"
    echo   - Removed old spec file
)

echo.
echo [2/4] Activating virtual environment...
call venv_ai\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)

echo.
echo [3/4] Building new EXE with PyInstaller...
venv_ai\Scripts\pyinstaller --onedir --windowed main.py --name ReadEcho_Pro --hidden-import database_manager --hidden-import ai_processor --hidden-import recording_manager --hidden-import app_services --hidden-import ui_builder --hidden-import event_handler --hidden-import config --hidden-import utils
if errorlevel 1 (
    echo ERROR: PyInstaller failed!
    pause
    exit /b 1
)

echo.
echo [4/4] Creating launcher batch file...
if exist "ReadEcho_Pro_Exe.bat" del "ReadEcho_Pro_Exe.bat"
echo @echo off > ReadEcho_Pro_Exe.bat
echo :: ReadEcho Pro Launcher >> ReadEcho_Pro_Exe.bat
echo cd /d "%%~dp0" >> ReadEcho_Pro_Exe.bat
echo start dist\ReadEcho_Pro\ReadEcho_Pro.exe >> ReadEcho_Pro_Exe.bat
echo exit >> ReadEcho_Pro_Exe.bat

echo.
echo ========================================
echo SUCCESS: EXE updated successfully!
echo ========================================
echo.
echo The new EXE is located in: dist\ReadEcho_Pro\
echo You can run it using: ReadEcho_Pro_Exe.bat
echo.
echo Press any key to exit...
pause >nul