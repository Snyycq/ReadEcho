@echo off
:: 切换到脚本所在目录
cd /d "%~dp0"

:: 激活虚拟环境
call .\venv_ai\Scripts\activate

:: 使用 pythonw 启动，这样就不会弹出黑框
:: 'start' 命令会让 UI 独立运行，'/b' 隐藏背景，'exit' 立即关闭 CMD
start /b pythonw ReadEcho_Pro.py
exit