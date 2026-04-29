@echo off
title ReadEcho Pro - GPU Accelerated
color 0b

:: 1. 切换到项目根目录（脚本在 scripts/ 子目录中）
cd /d "%~dp0.."

echo ==========================================
echo       ReadEcho Pro - GPU Accelerated
echo ==========================================

:: 2. 优先使用项目虚拟环境 .venv（已安装所有依赖）
if exist ".\.venv\Scripts\python.exe" (
    echo [INFO] 使用项目虚拟环境启动...
    .\.venv\Scripts\python.exe main.py
) else if exist ".\venv_ai\Scripts\python.exe" (
    echo [INFO] 使用 venv_ai 虚拟环境启动...
    .\venv_ai\Scripts\python.exe main.py
) else (
    echo [INFO] 使用系统 Python 启动...
    where python >nul 2>&1
    if %errorlevel%==0 (
        python main.py
    ) else (
        color 0c
        echo [ERROR] Cannot find Python!
        echo Please install Python 3.12+ or create virtual environment
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
