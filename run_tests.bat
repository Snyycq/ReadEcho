# ReadEcho Pro 测试运行脚本

# 智能检测虚拟环境并运行测试
@echo off
echo ========================================
echo   ReadEcho Pro - 智能测试运行器
echo ========================================
echo.

# 函数：检测当前是否在虚拟环境中
set PYTHON_DETECT_CMD=python -c "import sys; exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)"
%PYTHON_DETECT_CMD% >nul 2>&1
if %errorlevel% equ 0 (
    echo [状态检测] 当前已在虚拟环境中
    set IN_VENV=1
) else (
    echo [状态检测] 当前不在虚拟环境中
    set IN_VENV=0
)

# 检查虚拟环境是否存在
if not exist "venv_ai\Scripts\python.exe" (
    echo 错误: 虚拟环境不存在！
    echo 请先运行: python -m venv venv_ai
    echo 然后激活并安装依赖:
    echo   venv_ai\Scripts\activate
    echo   pip install -e .
    echo   pip install pytest pytest-cov python-dotenv
    echo.
    pause
    exit /b 1
)

# 如果不在虚拟环境中，激活它
if %IN_VENV% equ 0 (
    echo [1/3] 激活虚拟环境...
    call venv_ai\Scripts\activate.bat
) else (
    echo [1/3] 已在虚拟环境中，跳过激活
)

echo.
echo [2/3] 运行 pytest 测试...
echo.

# 创建临时文件用于捕获测试输出
set OUTPUT_FILE=%TEMP%\readecho_test_output_%RANDOM%.txt

# 运行测试并捕获输出和退出码
echo 运行测试命令: python -m pytest tests/ -v --tb=short
echo.
python -m pytest tests/ -v --tb=short > "%OUTPUT_FILE%" 2>&1
set TEST_EXIT_CODE=%errorlevel%

# 显示测试输出
type "%OUTPUT_FILE%"

echo.
echo ========================================

# 检查测试结果
if %TEST_EXIT_CODE% equ 0 (
    echo   所有测试通过！ ✓
) else (
    echo   测试失败！ ✗
    echo.
    echo [3/3] 分析失败原因...
    echo.

    # 尝试显示失败测试的详细信息
    echo === 失败测试详情 ===
    python -c "
import sys
import re
try:
    with open(r'%OUTPUT_FILE%', 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找失败测试
    failures = []
    errors = []
    lines = content.split('\n')
    in_failure = False
    current_failure = None

    for i, line in enumerate(lines):
        # 检测FAILED测试
        if 'FAILED' in line and 'tests/' in line:
            test_match = re.search(r'tests/.*\.py::.*::.*', line)
            if test_match:
                current_failure = {
                    'name': test_match.group(0),
                    'type': 'FAILED',
                    'error': '',
                    'location': ''
                }
                failures.append(current_failure)
                in_failure = True
        # 检测ERROR测试
        elif 'ERROR' in line and 'tests/' in line:
            test_match = re.search(r'tests/.*\.py::.*::.*', line)
            if test_match:
                current_failure = {
                    'name': test_match.group(0),
                    'type': 'ERROR',
                    'error': '',
                    'location': ''
                }
                errors.append(current_failure)
                in_failure = True
        # 收集错误信息
        elif in_failure and current_failure:
            if 'E   ' in line or 'AssertionError' in line or 'Error:' in line:
                current_failure['error'] += line.strip() + ' '
            if line.startswith('    File ') and current_failure['location'] == '':
                current_failure['location'] = line.strip()
            if line.startswith('_' * 20) or line.startswith('=' * 20):
                in_failure = False
                current_failure = None

    # 输出结果
    all_issues = failures + errors
    if all_issues:
        print(f'找到 {len(all_issues)} 个问题测试:\n')
        for i, issue in enumerate(all_issues, 1):
            print(f'{i}. [{issue[\"type\"]}] {issue[\"name\"]}')
            if issue['location']:
                print(f'   位置: {issue[\"location\"]}')
            if issue['error']:
                error_msg = issue['error'][:300].strip()
                print(f'   原因: {error_msg}')
            print()

        # 提供修复建议
        print('\n=== 修复建议 ===')
        for issue in all_issues[:3]:  # 最多显示3个建议
            if 'AssertionError' in issue['error']:
                print(f'- {issue[\"name\"]}: 断言失败，检查预期值与实际值')
            elif 'TypeError' in issue['error']:
                print(f'- {issue[\"name\"]}: 类型错误，检查参数类型')
            elif 'ImportError' in issue['error'] or 'ModuleNotFoundError' in issue['error']:
                print(f'- {issue[\"name\"]}: 导入错误，检查模块是否存在')
            elif 'AttributeError' in issue['error']:
                print(f'- {issue[\"name\"]}: 属性错误，检查对象是否有该属性')
            elif 'IndentationError' in issue['error'] or 'SyntaxError' in issue['error']:
                print(f'- {issue[\"name\"]}: 语法错误，检查代码格式')
            else:
                print(f'- {issue[\"name\"]}: 检查测试代码和被测代码')
    else:
        # 如果没有找到标准格式的失败信息，显示最后50行输出
        print('无法解析失败信息，显示最后输出:')
        print('-' * 50)
        last_lines = [l for l in lines if l.strip()][-50:]
        for line in last_lines:
            print(line)
except Exception as e:
    print(f'分析失败: {e}')
    print('请查看上面的输出了解详细错误信息。')
"

    echo.
    echo === 运行失败测试以获取更多信息 ===
    python -m pytest tests/ --lf -v --tb=long

    echo.
    echo === 测试覆盖率报告 ===
    python -m pytest tests/ --cov=. --cov-report=term-missing

    # 删除临时文件
    del "%OUTPUT_FILE%" >nul 2>&1

    echo.
    echo ========================================
    echo   修复建议
    echo ========================================
    echo 1. 检查上面显示的失败测试和错误原因
    echo 2. 查看相关代码文件中的问题行
    echo 3. 运行单个失败测试进行调试:
    echo    python -m pytest [测试路径] -v --tb=long
    echo 4. 如果是导入错误，检查模块依赖
    echo 5. 如果是断言错误，检查预期值与实际值
    echo.
    pause
    exit /b %TEST_EXIT_CODE%
)

# 删除临时文件
del "%OUTPUT_FILE%" >nul 2>&1

echo.
echo [3/3] 生成测试覆盖率报告...
echo.
python -m pytest tests/ --cov=. --cov-report=term-missing

echo.
echo ========================================
echo   所有测试已完成！
echo ========================================
echo.
echo 测试统计:
python -m pytest tests/ --collect-only 2>nul | find /c "test_" | findstr /v "0" >nul && (
    python -c "
import subprocess
import re
result = subprocess.run(['python', '-m', 'pytest', 'tests/', '--collect-only'],
                       capture_output=True, text=True, encoding='utf-8')
if result.returncode == 0:
    test_count = len(re.findall(r'test_.*\(', result.stdout))
    print(f'✓ 总测试数量: {test_count}')
    print('✓ 所有测试通过')
else:
    print('✗ 无法获取测试统计信息')
"
)

echo.
pause
