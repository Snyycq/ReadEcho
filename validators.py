"""
ReadEcho Pro 输入验证模块
提供数据验证和清理函数
"""

import re
from pathlib import Path
from config import LOGGER


class InputValidator:
    """输入验证和清理类"""
    
    @staticmethod
    def validate_book_title(title: str, max_length: int = 255) -> str:
        """
        验证书籍标题
        
        Args:
            title: 书籍标题
            max_length: 最大长度
            
        Returns:
            清理后的标题
            
        Raises:
            ValueError: 如果标题无效
        """
        if not isinstance(title, str):
            raise ValueError("标题必须是字符串类型")
        
        title = title.strip()
        if not title:
            raise ValueError("标题不能为空")
        
        if len(title) > max_length:
            title = title[:max_length]
            LOGGER.warning(f"标题过长，已截断至{max_length}个字符")
        
        # 移除可能危险的字符
        sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
        return sanitized
    
    @staticmethod
    def validate_author_name(author: str, max_length: int = 100) -> str:
        """
        验证作者名称
        
        Args:
            author: 作者名称
            max_length: 最大长度
            
        Returns:
            清理后的作者名称
        """
        if not isinstance(author, str):
            return ""
        
        author = author.strip()
        if len(author) > max_length:
            author = author[:max_length]
        
        return author
    
    @staticmethod
    def validate_question(question: str, max_length: int = 500) -> str:
        """
        验证问题文本
        
        Args:
            question: 问题文本
            max_length: 最大长度
            
        Returns:
            清理后的问题
            
        Raises:
            ValueError: 如果问题无效
        """
        if not isinstance(question, str):
            raise ValueError("问题必须是字符串类型")
        
        question = question.strip()
        if not question:
            raise ValueError("问题不能为空")
        
        if len(question) > max_length:
            raise ValueError(f"问题过长（最大{max_length}个字符）")
        
        return question
    
    @staticmethod
    def validate_file_path(file_path: str, allowed_dir: str = None) -> str:
        """
        验证文件路径，防止目录遍历攻击
        
        Args:
            file_path: 文件路径
            allowed_dir: 允许的目录（可选）
            
        Returns:
            验证后的绝对路径
            
        Raises:
            ValueError: 如果路径无效
        """
        try:
            path = Path(file_path).resolve()
            
            if not path.exists():
                raise ValueError(f"文件不存在: {file_path}")
            
            if allowed_dir:
                allowed_path = Path(allowed_dir).resolve()
                try:
                    path.relative_to(allowed_path)
                except ValueError:
                    raise ValueError(f"文件不在允许的目录内: {allowed_dir}")
            
            return str(path)
        except Exception as e:
            LOGGER.error(f"文件路径验证失败: {e}")
            raise ValueError(f"无效的文件路径: {file_path}")
    
    @staticmethod
    def validate_audio_file(file_path: str) -> str:
        """
        验证音频文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            验证后的路径
            
        Raises:
            ValueError: 如果不是有效的音频文件
        """
        audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
        
        path = Path(file_path).resolve()
        if path.suffix.lower() not in audio_extensions:
            raise ValueError(f"不支持的音频格式: {path.suffix}")
        
        if not path.exists():
            raise ValueError(f"音频文件不存在: {file_path}")
        
        return str(path)
