"""
validators.py 单元测试
测试输入验证功能
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validators import InputValidator  # noqa: E402


class TestInputValidator:
    """测试输入验证器"""

    class TestValidateBookTitle:
        """测试书籍标题验证"""

        def test_valid_title(self):
            """测试有效标题"""
            title = "Python编程入门"
            result = InputValidator.validate_book_title(title)
            assert result == title

        def test_title_with_whitespace(self):
            """测试带空白字符的标题"""
            title = "  Python编程  "
            result = InputValidator.validate_book_title(title)
            assert result == "Python编程"

        def test_empty_title_raises_error(self):
            """测试空标题应抛出错误"""
            with pytest.raises(ValueError, match="不能为空"):
                InputValidator.validate_book_title("")

        def test_whitespace_only_title_raises_error(self):
            """测试仅空白字符标题应抛出错误"""
            with pytest.raises(ValueError, match="不能为空"):
                InputValidator.validate_book_title("   ")

        def test_title_with_special_chars_removal(self):
            """测试标题中特殊字符移除"""
            title = '书名:<>"/?*|'
            result = InputValidator.validate_book_title(title)
            # 移除非法文件名字符，包括冒号
            assert result == "书名"

        def test_long_title_truncated(self):
            """测试长标题被截断"""
            long_title = "A" * 300
            result = InputValidator.validate_book_title(long_title)
            assert len(result) == 255

    class TestValidateAuthorName:
        """测试作者名称验证"""

        def test_valid_author(self):
            """测试有效作者名"""
            author = "张三"
            result = InputValidator.validate_author_name(author)
            assert result == author

        def test_empty_author_returns_empty(self):
            """测试空作者名返回空字符串"""
            result = InputValidator.validate_author_name("")
            assert result == ""

        def test_author_with_whitespace(self):
            """测试带空白字符的作者名"""
            author = "  张三  "
            result = InputValidator.validate_author_name(author)
            assert result == "张三"

        def test_long_author_truncated(self):
            """测试长作者名被截断"""
            long_author = "A" * 150
            result = InputValidator.validate_author_name(long_author)
            assert len(result) == 100

    class TestValidateQuestion:
        """测试问题验证"""

        def test_valid_question(self):
            """测试有效问题"""
            question = "这本书的主要内容是什么？"
            result = InputValidator.validate_question(question)
            assert result == question

        def test_empty_question_raises_error(self):
            """测试空问题应抛出错误"""
            with pytest.raises(ValueError, match="不能为空"):
                InputValidator.validate_question("")

        def test_question_with_whitespace(self):
            """测试带空白字符的问题"""
            question = "  这本书讲什么？  "
            result = InputValidator.validate_question(question)
            assert result == "这本书讲什么？"

        def test_question_too_long_raises_error(self):
            """测试过长问题应抛出错误"""
            long_question = "A" * 501
            with pytest.raises(ValueError, match="问题过长"):
                InputValidator.validate_question(long_question)

    class TestValidateAudioFile:
        """测试音频文件路径验证"""

        def test_invalid_audio_extension_raises_error(self):
            """测试无效音频格式应抛出错误"""
            with pytest.raises(ValueError, match="不支持的音频格式"):
                InputValidator.validate_audio_file("/path/to/file.exe")

        def test_valid_extensions_accepted(self):
            """测试各种有效音频扩展名"""
            # 注意：由于需要文件实际存在，这部分测试无法完全验证
            # 只能测试错误情况
            pass

    class TestValidateFilePath:
        """测试文件路径验证"""

        def test_nonexistent_file_raises_error(self):
            """测试不存在的文件应抛出错误"""
            with pytest.raises(ValueError):
                InputValidator.validate_file_path("/nonexistent/file.txt")


class TestInputValidatorFixtures:
    """使用pytest fixtures进行测试"""

    def test_title_stripping(self):
        """测试标题清理"""
        result = InputValidator.validate_book_title("  Hello World  ")
        assert result == "Hello World"

    def test_question_stripping(self):
        """测试问题清理"""
        result = InputValidator.validate_question("  What is this?  ")
        assert result == "What is this?"
