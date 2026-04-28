@echo off
title ReadEcho Pro - GPU Accelerated
color 0b

:: 1. 切换到项目根目录（脚本在 scripts/ 子目录中）
cd /d "%~dp0.."

echo ==========================================
echo       ReadEcho Pro - GPU Accelerated
echo ==========================================

:: 2. 检查是否需要使用虚拟环境（通过参数 --venv 或 -v）
set USE_VENV=0
if "%1"=="--venv" set USE_VENV=1
if "%1"=="-v" set USE_VENV=1

if %USE_VENV%==1 (
    echo [INFO] 使用虚拟环境启动...
    if not exist ".\venv_ai\Scripts\python.exe" (
        color 0c
        echo [ERROR] Cannot find 'venv_ai' folder!
        pause
        exit
    )
    echo [INFO] 启动应用（虚拟环境模式）...
    .\venv_ai\Scripts\python.exe main.py
) else (
    echo [INFO] 使用系统 Python 启动...
    :: 优先使用系统 Python 3.12
    where python >nul 2>&1
    if %errorlevel%==0 (
        python main.py
    ) else (
        color 0c
        echo [ERROR] Cannot find system Python!
        echo Please install Python 3.12+ or use: start.bat --venv
        pause
        exit
    )
)

:: 3. 错误处理
if %errorlevel% neq 0 (
    color 0c
    echo.
    echo [CRASH] Program exited with error code: %errorlevel%
    pause
)
