# ReadEcho Pro 测试运行脚本

# 激活虚拟环境并运行所有测试
@echo off
echo ========================================
echo   ReadEcho Pro - 测试运行器
echo ========================================
echo.

# 检查虚拟环境是否存在
if not exist "venv_ai\Scripts\python.exe" (
    echo 错误: 虚拟环境不存在！
    echo 请先运行: python -m venv venv_ai
    echo 然后激活并安装依赖:
    echo   venv_ai\Scripts\activate
    echo   pip install -e .
    echo   pip install pytest pytest-cov
    echo.
    pause
    exit /b 1
)

echo [1/2] 激活虚拟环境...
call venv_ai\Scripts\activate.bat

echo.
echo [2/2] 运行 pytest 测试...
echo.

# 运行测试
python -m pytest tests/ -v --tb=short

echo.
echo ========================================
echo   测试完成！
echo ========================================
echo.
pause
