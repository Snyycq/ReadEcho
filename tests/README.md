# ReadEcho Pro 测试文档

## 📊 测试状态概览

**最后更新**: 2026-04-22  
**测试框架**: pytest 9.0.3  
**测试通过率**: 100% (99/99 测试通过)  
**主要问题**: 无（所有测试通过）  
**总体覆盖率**: 33%（基于2026-04-21测试覆盖率报告）

### test文件夹用途
本目录是ReadEcho项目的专用测试框架，包含：
- **单元测试**：测试单个模块的功能正确性
- **集成测试**：测试模块间交互和完整工作流
- **测试文档**：测试框架使用说明和状态跟踪
- **测试配置**：pytest配置、fixtures和运行脚本

### 相关文档
- **[TODO.md](TODO.md)** - 测试待办事项和计划
- **[CHANGELOG.md](CHANGELOG.md)** - 测试框架变更日志
- **[运行测试脚本](../../run_tests.bat)** - Windows一键测试脚本

### 测试报告
- **[docs/reports/test_coverage_report.md](../../docs/reports/test_coverage_report.md)** - 详细测试覆盖率分析报告
- **[docs/reports/code_quality_report.md](../../docs/reports/code_quality_report.md)** - 代码质量问题分析报告

### 快速开始
```bash
# 运行所有测试
pytest

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

---

## 目录

1. [测试框架](#测试框架)
2. [运行测试](#运行测试)
3. [测试类型](#测试类型)
4. [测试结构](#测试结构)
5. [编写新测试](#编写新测试)

## 测试框架

本项目使用 [pytest](https://pytest.org/) 作为测试框架，提供以下工具：

- **pytest**: 核心测试运行器
- **pytest-cov**: 代码覆盖率报告

### 安装测试依赖

```bash
# 激活虚拟环境
source venv_ai/Scripts/activate

# 安装测试依赖
pip install pytest pytest-cov
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行单元测试

```bash
pytest tests/unit/
```

### 运行集成测试

```bash
pytest tests/integration/
```

### 运行特定测试文件

```bash
pytest tests/unit/test_validators.py
```

### 运行特定测试类/函数

```bash
# 运行测试类
pytest tests/unit/test_validators.py::TestInputValidator

# 运行特定测试函数
pytest tests/unit/test_validators.py::TestInputValidator::TestValidateBookTitle::test_valid_title
```

### 生成代码覆盖率报告

```bash
# 生成覆盖率报告
pytest --cov=. --cov-report=html

# 查看覆盖率报告
# 打开 htmlcov/index.html
```

### 查看详细输出

```bash
# 详细输出（包括打印信息）
pytest -v -s

# 只显示失败的测试
pytest -v --tb=short

# 失败时立即停止
pytest -v -x
```

## 测试类型

### 单元测试 (Unit Tests)

位于 `tests/unit/` 目录，测试单个模块的功能。

**测试内容：**
- validators.py - 输入验证
- database_manager.py - 数据库操作
- app_services.py - 应用服务层
- model_cache.py - 模型缓存
- utils.py - 工具函数

### 集成测试 (Integration Tests)

位于 `tests/integration/` 目录，测试多个模块之间的交互。

**测试内容：**
- 书籍和录音的完整工作流
- 服务生命周期管理
- 数据持久化
- 错误恢复

## 测试结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # pytest 配置和 fixtures
├── unit/                    # 单元测试
│   ├── __init__.py
│   ├── test_validators.py
│   ├── test_database_manager.py
│   ├── test_app_services.py
│   ├── test_model_cache.py
│   └── test_utils.py
└── integration/             # 集成测试
    ├── __init__.py
    └── test_integration.py
```

### conftest.py

包含测试的通用配置：

- **fixtures**: 提供临时数据库、模拟数据等
- **pytest 配置**: 测试路径、标记等

### 测试文件命名约定

- 文件名：`test_<模块名>.py`
- 测试类：`Test<类名>`
- 测试方法：`test_<功能>`

### 测试最佳实践

1. **每个测试应该是独立的**
   - 测试之间不应该有依赖
   - 每个测试应该能单独运行

2. **使用 fixtures 进行设置和清理**
   - 避免在测试函数中重复设置代码
   - 使用 `@pytest.fixture` 创建可重用的测试资源

3. **测试边界情况**
   - 空值、空字符串
   - 最大/最小值
   - 无效输入
   - 错误处理

4. **测试预期的行为，而不是实现**
   - 关注"应该发生什么"，而不是"如何发生"

## 编写新测试

### 示例：编写验证器测试

```python
# tests/unit/test_validators.py

import pytest
from validators import InputValidator


class TestInputValidator:
    """测试输入验证器"""
    
    class TestValidateBookTitle:
        """测试书籍标题验证"""
        
        def test_valid_title(self):
            """测试有效标题"""
            title = "Python编程入门"
            result = InputValidator.validate_book_title(title)
            assert result == title
        
        def test_empty_title_raises_error(self):
            """测试空标题应抛出错误"""
            with pytest.raises(ValueError, match="不能为空"):
                InputValidator.validate_book_title("")
```

### 示例：编写数据库测试

```python
# tests/unit/test_database_manager.py

import pytest
import tempfile
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database_manager import DBManager


class TestDBManager:
    """测试数据库管理器"""
    
    @pytest.fixture
    def db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        import config
        original_db = config.DATABASE_FILE
        config.DATABASE_FILE = db_path
        
        db = DBManager()
        yield db
        
        db.close()
        config.DATABASE_FILE = original_db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_add_book_success(self, db):
        """测试成功添加书籍"""
        book_id = db.add_book("测试书籍", "测试作者")
        assert book_id is not None
        assert isinstance(book_id, int)
```

## 常见问题

### 1. 测试数据库被锁定

**问题**: `sqlite3.OperationalError: database is locked`

**解决方案**:
- 确保每个测试使用独立的数据库文件
- 在 fixtures 中正确清理数据库连接
- 检查是否有未关闭的数据库连接

### 2. 模块导入错误

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
- 确保在测试文件中添加了项目路径
- 使用相对导入或修改 `sys.path`
- 参考现有测试文件的导入方式

### 3. 测试失败但不知道原因

**问题**: 需要更多调试信息

**解决方案**:
```bash
# 运行测试时显示详细输出
pytest -v -s

# 查看更详细的回溯信息
pytest -v --tb=long
```

## 下一步

- ✅ 已完成：搭建 pytest 测试框架
- ✅ 已完成：编写基础单元测试
- ✅ 已完成：编写基础集成测试
- ⏳ 计划中：添加测试覆盖率监控
- ⏳ 计划中：持续集成配置
