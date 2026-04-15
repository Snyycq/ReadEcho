"""
ReadEcho Pro 模型缓存管理模块
实现AI模型的单例缓存机制，避免重复加载
"""

import os
import torch
import whisper
from pathlib import Path
from functools import lru_cache
from typing import Optional
from config import LOGGER, WHISPER_MODEL


class ModelCache:
    """
    AI模型缓存管理器 - 单例模式
    用于管理Whisper和其他AI模型的加载和缓存
    """
    
    _instance = None
    _models = {}
    _cache_dir = None
    
    def __new__(cls):
        """单例模式：确保只有一个ModelCache实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化模型缓存"""
        if self._initialized:
            return
        
        self._cache_dir = Path.home() / '.readecho' / 'models'
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        LOGGER.info(f"模型缓存目录: {self._cache_dir}")
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_whisper_model(self, model_size: str = WHISPER_MODEL) -> object:
        """
        获取或加载Whisper模型
        
        Args:
            model_size: 模型大小 ("tiny", "base", "small", "medium", "large")
            
        Returns:
            Whisper模型实例
            
        Raises:
            RuntimeError: 如果模型加载失败
        """
        try:
            # 检查缓存中是否已存在该模型
            if model_size in self._models:
                LOGGER.debug(f"从缓存获取Whisper模型: {model_size}")
                return self._models[model_size]
            
            # 加载新模型
            device = "cuda" if torch.cuda.is_available() else "cpu"
            LOGGER.info(f"加载Whisper模型: {model_size} (设备: {device})")
            
            model = whisper.load_model(
                model_size,
                device=device,
                download_root=str(self._cache_dir / "whisper")
            )
            
            # 缓存模型
            self._models[model_size] = model
            LOGGER.info(f"Whisper模型加载完成: {model_size}")
            
            return model
        except Exception as e:
            error_msg = f"加载Whisper模型失败 ({model_size}): {str(e)}"
            LOGGER.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)
    
    def unload_model(self, model_size: str = WHISPER_MODEL) -> None:
        """
        卸载缓存中的模型以释放内存
        
        Args:
            model_size: 要卸载的模型大小
        """
        try:
            if model_size in self._models:
                del self._models[model_size]
                LOGGER.info(f"已卸载模型: {model_size}")
                # 清理GPU内存
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        except Exception as e:
            LOGGER.error(f"卸载模型失败: {e}")
    
    def clear_cache(self) -> None:
        """清空所有缓存的模型"""
        try:
            self._models.clear()
            LOGGER.info("已清空所有缓存模型")
            
            # 清理GPU内存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                LOGGER.debug("已清理GPU内存")
        except Exception as e:
            LOGGER.error(f"清空缓存失败: {e}")
    
    def get_cached_models(self) -> dict:
        """获取当前缓存的所有模型信息"""
        info = {}
        for model_name, model in self._models.items():
            info[model_name] = {
                'loaded': True,
                'type': type(model).__name__
            }
        return info
    
    def get_model_size(self) -> dict:
        """
        获取缓存模型占用的内存大小
        
        Returns:
            模型名称和其大小的字典（以字节为单位）
        """
        sizes = {}
        cache_root = self._cache_dir
        
        try:
            for model_dir in cache_root.rglob('*'):
                if model_dir.is_file():
                    model_name = model_dir.parent.name
                    if model_name not in sizes:
                        sizes[model_name] = 0
                    sizes[model_name] += model_dir.stat().st_size
        except Exception as e:
            LOGGER.error(f"获取模型大小失败: {e}")
        
        return sizes
    
    def clear_disk_cache(self, model_size: Optional[str] = None) -> None:
        """
        清空磁盘上的缓存模型文件
        
        Args:
            model_size: 要清除的特定模型，None表示清空所有
        """
        try:
            if model_size:
                model_dir = self._cache_dir / "whisper" / model_size
                if model_dir.exists():
                    import shutil
                    shutil.rmtree(model_dir)
                    LOGGER.info(f"已清空磁盘缓存: {model_size}")
            else:
                # 清空所有缓存
                import shutil
                if self._cache_dir.exists():
                    shutil.rmtree(self._cache_dir)
                    self._cache_dir.mkdir(parents=True, exist_ok=True)
                    LOGGER.info("已清空所有磁盘缓存")
        except Exception as e:
            LOGGER.error(f"清空磁盘缓存失败: {e}")


# 全局单例实例
model_cache = ModelCache.get_instance()
