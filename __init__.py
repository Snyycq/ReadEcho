"""
ReadEcho Pro - GPU加速阅读助手
一个智能读书笔记和摘要生成工具
"""

__version__ = "1.0.0"
__author__ = "ReadEcho Team"
__description__ = "GPU Accelerated Reading Assistant with AI"

from config import LOGGER, WHISPER_MODEL, OLLAMA_MODEL
from database_manager import DBManager
from ai_processor import AIService, ModelLoaderThread, AIProcessThread
from validators import InputValidator

__all__ = [
    "LOGGER",
    "DBManager",
    "AIService",
    "ModelLoaderThread",
    "AIProcessThread",
    "InputValidator",
    "WHISPER_MODEL",
    "OLLAMA_MODEL",
]
