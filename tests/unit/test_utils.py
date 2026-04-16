"""
utils.py 单元测试
测试工具函数
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils import format_summary_content, truncate_text


class TestFormatSummaryContent:
    """测试摘要内容格式化"""

    def test_basic_formatting(self):
        """测试基本格式化"""
        content = "第一行\n第二行\n第三行"
        result = format_summary_content(content)
        assert "<p>" in result
        assert "</p>" in result
        assert "第一行" in result
        assert "第二行" in result

    def test_empty_content(self):
        """测试空内容"""
        result = format_summary_content("")
        assert result == "<p></p>"

    def test_single_line(self):
        """测试单行内容"""
        result = format_summary_content("单行文本")
        assert "<p>单行文本</p>" in result

    def test_whitespace_handling(self):
        """测试空白字符处理"""
        content = "  前后有空格  "
        result = format_summary_content(content)
        assert "<p>" in result
        assert "</p>" in result


class TestTruncateText:
    """测试文本截断"""

    def test_short_text_no_truncate(self):
        """测试短文本不截断"""
        text = "短文本"
        result = truncate_text(text, max_length=100)
        assert result == text

    def test_long_text_truncate(self):
        """测试长文本截断"""
        text = "A" * 100
        result = truncate_text(text, max_length=50)
        assert len(result) <= 53  # 50 + "..."
        assert result.endswith("...")

    def test_exact_length_text(self):
        """测试精确长度文本"""
        text = "A" * 50
        result = truncate_text(text, max_length=50)
        assert result == text

    def test_empty_text(self):
        """测试空文本"""
        result = truncate_text("", max_length=50)
        assert result == ""

    def test_custom_suffix(self):
        """测试自定义后缀"""
        text = "A" * 100
        result = truncate_text(text, max_length=50, suffix=" [更多]")
        assert result.endswith(" [更多]")
