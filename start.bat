@echo off
title ReadEcho Pro - System Loading...
color 0b

:: 1. 强制切换到当前脚本所在的文件夹，防止路径偏移
cd /d "%~dp0"

echo ==========================================
echo       ReadEcho Pro - GPU Accelerated
echo ==========================================
echo [1/3] Activating Virtual Environment (venv_ai)...

:: 2. 检查环境文件夹是否存在
if not exist ".\venv_ai\Scripts\activate" (
    color 0c
    echo [ERROR] Cannot find 'venv_ai' folder! 
    echo Please ensure the .bat is in the same folder as venv_ai.
    pause
    exit
)

echo [2/3] Checking CUDA and Dependencies...
echo [3/3] Launching ReadEcho_Pro.py...
echo ------------------------------------------

:: 3. 启动程序，使用虚拟环境的 Python
.\venv_ai\Scripts\python.exe ReadEcho_Pro.py

:: 4. 只有当程序“非正常崩溃”时才保留窗口，正常关闭则随之消失
if %errorlevel% neq 0 (
    color 0c
    echo.
    echo [CRASH] Program exited with error code: %errorlevel%
    pause
)

:: 去掉这里的 pause，程序正常退出后窗口就会自动关闭
